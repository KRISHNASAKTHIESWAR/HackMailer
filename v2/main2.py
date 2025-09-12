#AUTOMATED HACKATHON EMAIL MONITOR that check frequently for new hackathon emails and creates calendar events
#Uses Gmail Push Notifications with Pub/Sub and a Flask webhook server

import json
import base64
import os
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, request
from utils.auth import authenticate_gmail
from utils.fetchmail import fetch_hackathon_emails, get_email_html_body
from utils.extract_link import extract_registration_links
from utils.get_date import scrape_deadline_and_name_static, scrape_deadline_and_name_dynamic
from utils.calendar_event import create_calendar_event
from utils.deadline_parse import parse_deadline
from utils.mail_watch import start_gmail_watch
from googleapiclient.discovery import build
from dotenv import load_dotenv as dotenv
dotenv()    

app = Flask(__name__)

class HackathonEmailMonitor:
    def __init__(self, project_id=os.getenv("project_id")):
        self.project_id = project_id
        self.processed_emails_file = "processed_emails.json"
        self.processed_emails = self.load_processed_emails()
        self.gmail_service = None
        self.calendar_service = None
        self.watch_expiration = None
        
    def initialize_services(self):
        """Initialize Gmail and Calendar services"""
        print("Authenticating with Google services...")
        creds = authenticate_gmail()
        self.gmail_service = build('gmail', 'v1', credentials=creds)
        self.calendar_service = build('calendar', 'v3', credentials=creds)
        print("Services initialized successfully")
    
    def load_processed_emails(self):
        """Load list of already processed email IDs"""
        if os.path.exists(self.processed_emails_file):
            try:
                with open(self.processed_emails_file, 'r') as f:
                    data = json.load(f)
                    return set(data) if isinstance(data, list) else set()
            except Exception as e:
                print(f" Error loading processed emails: {e}")
                return set()
        return set()
    
    def save_processed_emails(self):
        """Save list of processed email IDs"""
        try:
            with open(self.processed_emails_file, 'w') as f:
                json.dump(list(self.processed_emails), f)
        except Exception as e:
            print(f"Error saving processed emails: {e}")
    
    def is_hackathon_email(self, message):
        """Check if email is hackathon-related based on subject and content"""
        try:
            headers = message['payload'].get('headers', [])
            subject = ""
            sender = ""
            
            for header in headers:
                if header['name'].lower() == 'subject':
                    subject = header['value'].lower()
                elif header['name'].lower() == 'from':
                    sender = header['value'].lower()
            
            # Enhanced hackathon detection
            hackathon_keywords = [
                'competitions','hackathon', 'coding competition', 'tech challenge', 'programming contest',
                'code challenge', 'developer challenge', 'devpost', 'hackerearth',
                'coding contest', 'programming competition', 'hack', 'innovation challenge'
            ]
            
            # Check subject
            if any(keyword in subject for keyword in hackathon_keywords):
                return True
            
            # Check sender domains
            hackathon_domains = [
                'devpost', 'hackerearth', 'mlh.io', 'hackathon', 'codeforces',
                'topcoder', 'kaggle', 'codechef', 'hackerrank','unstop','competitions'
            ]
            
            if any(domain in sender for domain in hackathon_domains):
                return True
                
            return False
            
        except Exception as e:
            print(f"Error checking if email is hackathon-related: {e}")
            return False
    
    def is_recent_email(self, message, hours=24):
        """Check if email is from the last specified hours"""
        try:
            internal_date = int(message['internalDate']) / 1000
            email_time = datetime.fromtimestamp(internal_date)
            cutoff_time = datetime.now() - timedelta(hours=hours)
            return email_time > cutoff_time
        except:
            return False
    
    def process_hackathon_email(self, message_id):
        """Process a single hackathon email and create calendar events"""
        if message_id in self.processed_emails:
            return
            
        try:
            print(f" Processing email: {message_id}")
            
            # Get the full message
            message = self.gmail_service.users().messages().get(
                userId='me', 
                id=message_id, 
                format='full'
            ).execute()
            
            # Check if it's hackathon-related
            if not self.is_hackathon_email(message):
                print(f"Email {message_id} is not hackathon-related")
                self.processed_emails.add(message_id)
                return
            
            # Get subject for logging
            subject = ""
            for header in message['payload'].get('headers', []):
                if header['name'].lower() == 'subject':
                    subject = header['value']
                    break
            
            print(f" Processing hackathon email: {subject}")
            
            # Extract HTML body and links
            html_body = get_email_html_body(message)
            if not html_body:
                print(f" No HTML body found in email {message_id}")
                self.processed_emails.add(message_id)
                return
            
            links = extract_registration_links(html_body)
            if not links:
                print(f" No registration links found in: {subject}")
                self.processed_emails.add(message_id)
                return
            
            # Process each link
            events_created = 0
            for url in links:
                try:
                    print(f"🔍 Visiting: {url}")
                    
                    # Try static scraping first
                    name, deadline = scrape_deadline_and_name_static(url)
                    if not deadline:
                        # Try dynamic scraping + OCR fallback
                        name, deadline = scrape_deadline_and_name_dynamic(url)
                    
                    print(f"Hackathon: {name}")
                    print(f"Deadline: {deadline}")
                    
                    # Parse deadline and create calendar event
                    deadline_date = parse_deadline(deadline)
                    if deadline_date:
                        create_calendar_event(self.calendar_service, name, deadline_date, url)
                        print(f" Calendar event created for {name}")
                        events_created += 1
                    else:
                        print(" Could not determine deadline, skipping calendar event.")
                        
                except Exception as e:
                    print(f" Error processing link {url}: {e}")
            
            if events_created > 0:
                print(f" Successfully created {events_created} calendar events from email: {subject}")
            
            # Mark as processed
            self.processed_emails.add(message_id)
            
        except Exception as e:
            print(f" Error processing email {message_id}: {e}")
    
    def setup_gmail_watch(self):
        """Set up Gmail push notifications"""
        try:
            topic_name = f"projects/{self.project_id}/topics/gmail-notifications"
            
            # Start Gmail watch
            result = start_gmail_watch(self.gmail_service, topic_name)
            
            # Store expiration time (Gmail watch expires after 7 days)
            if 'expiration' in result:
                self.watch_expiration = int(result['expiration']) / 1000  # Convert to seconds
                expiry_date = datetime.fromtimestamp(self.watch_expiration)
                print(f" Gmail watch set up successfully. Expires: {expiry_date}")
            else:
                print(" Gmail watch set up successfully (no expiration provided)")
                
            return True
            
        except Exception as e:
            print(f" Error setting up Gmail watch: {e}")
            return False
    
    def check_and_renew_watch(self):
        """Check if Gmail watch needs renewal and renew if necessary"""
        if self.watch_expiration:
            current_time = time.time()
            # Renew 1 day before expiration
            if current_time > (self.watch_expiration - 86400):
                print(" Renewing Gmail watch...")
                self.setup_gmail_watch()
    
    def check_for_new_emails(self, max_results=20):
        """Check for new hackathon emails (backup method)"""
        try:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]  Checking for new hackathon emails...")
            
            # Fetch recent hackathon emails using your existing function
            messages = fetch_hackathon_emails(self.gmail_service, maxResults=max_results)
            new_emails_count = 0
            
            for msg in messages:
                msg_id = msg['id']
                
                # Skip if already processed
                if msg_id in self.processed_emails:
                    continue
                
                # Get full message to check if it's recent
                try:
                    full_message = self.gmail_service.users().messages().get(
                        userId='me', 
                        id=msg_id
                    ).execute()
                    
                    # Only process recent emails (last 24 hours for backup check)
                    if self.is_recent_email(full_message, hours=24):
                        self.process_hackathon_email(msg_id)
                        new_emails_count += 1
                    else:
                        # Mark old emails as processed
                        self.processed_emails.add(msg_id)
                        
                except Exception as e:
                    print(f" Error checking email {msg_id}: {e}")
            
            if new_emails_count > 0:
                print(f" Processed {new_emails_count} new hackathon emails")
            else:
                print(" No new hackathon emails found")
            
            # Save processed emails list
            self.save_processed_emails()
            
            # Check if Gmail watch needs renewal
            self.check_and_renew_watch()
            
        except Exception as e:
            print(f" Error checking for emails: {e}")
    
    def process_push_notification(self, notification_data):
        """Process Gmail push notification"""
        try:
            print(f" Received Gmail notification: {notification_data}")
            
            history_id = notification_data.get('historyId')
            if not history_id:
                print(" No historyId in notification")
                return
            
            # Get history of changes
            history = self.gmail_service.users().history().list(
                userId='me',
                startHistoryId=history_id
            ).execute()
            
            if 'history' not in history:
                print(" No new messages in history")
                return
            
            # Process new messages
            for history_record in history['history']:
                if 'messagesAdded' in history_record:
                    for message_added in history_record['messagesAdded']:
                        message_id = message_added['message']['id']
                        print(f" New message detected: {message_id}")
                        
                        # Process in separate thread to avoid blocking
                        threading.Thread(
                            target=self.process_hackathon_email,
                            args=(message_id,),
                            daemon=True
                        ).start()
            
            # Save processed emails after handling notifications
            self.save_processed_emails()
                        
        except Exception as e:
            print(f" Error processing push notification: {e}")
    
    def run_periodic_backup(self, check_interval=60):  # 10 minutes
        """Run periodic backup check"""
        print(f"Starting periodic backup check every {check_interval//60} minutes...")
        
        while True:
            try:
                time.sleep(check_interval)
                self.check_for_new_emails()
                
            except Exception as e:
                print(f" Error in periodic backup: {e}")
                time.sleep(check_interval)

# Global monitor instance
monitor = HackathonEmailMonitor()

@app.route('/webhook', methods=['POST'])
def gmail_webhook():
    """Handle Gmail push notifications"""
    try:
        # Parse the push notification
        envelope = json.loads(request.data.decode('utf-8'))
        
        if 'message' in envelope:
            message_data = envelope['message']['data']
            decoded_data = base64.b64decode(message_data).decode('utf-8')
            notification = json.loads(decoded_data)
            
            # Process notification in separate thread
            threading.Thread(
                target=monitor.process_push_notification,
                args=(notification,),
                daemon=True
            ).start()
        
        return 'OK', 200
        
    except Exception as e:
        print(f" Error handling webhook: {e}")
        return 'Error', 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}, 200

def main():
    print(" Starting Automated Hackathon Email Monitor...")
    
    # Initialize services
    monitor.initialize_services()
    
    # Set up Gmail push notifications
    if monitor.setup_gmail_watch():
        print(" Push notifications enabled")
    else:
        print(" Push notifications failed, will rely on periodic checks only")
    
    # Start periodic backup check in background
    backup_thread = threading.Thread(
        target=monitor.run_periodic_backup,
        daemon=True
    )
    backup_thread.start()
    
    # Run one initial check
    print(" Running initial email check...")
    monitor.check_for_new_emails()
    
    print(" System is now monitoring for hackathon emails automatically!")
    print(" Webhook server starting on port 8080...")
    print(" Periodic backup checks running every 10 minutes")
    
    # Start Flask webhook server
    app.run(host='0.0.0.0', port=8080, debug=False)

if __name__ == "__main__":
    main()