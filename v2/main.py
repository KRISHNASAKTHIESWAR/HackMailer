from auth import authenticate_gmail
from fetchmail import fetch_hackathon_emails, get_email_html_body
from extract_link import extract_registration_links
from get_date import scrape_deadline_and_name_static, scrape_deadline_and_name_dynamic
from calendar_event import create_calendar_event
from deadline_parse import parse_deadline

from googleapiclient.discovery import build

def main():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
    calendar_service = build('calendar', 'v3', credentials=creds)
    messages = fetch_hackathon_emails(service, maxResults=20)
    print(f"Found {len(messages)} hackathon-related emails.\n")

    for msg in messages:
        msg_id = msg['id']
        try:
            message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            html_body = get_email_html_body(message)
            if html_body:
                links = extract_registration_links(html_body)
                if links:
                    print(f"Message ID: {msg_id}")
                    for url in links:
                        print(f" Visiting: {url}")
                        # Try static scraping
                        name, deadline = scrape_deadline_and_name_static(url)
                        if not deadline:
                            # Dynamic scraping + OCR fallback
                            name, deadline = scrape_deadline_and_name_dynamic(url)
                        print(f"  Hackathon: {name}")
                        print(f"  Deadline: {deadline}\n")
                        
                        
                        deadline_date = parse_deadline(deadline)
                        if deadline_date:
                            create_calendar_event(calendar_service, name, deadline_date, url)
                        else:
                            print("  Could not determine deadline, skipping calendar event creation.\n")
                else:
                    print(f"Message ID: {msg_id} -- No registration links found.\n")
            else:
                print(f"Message ID: {msg_id} -- No HTML body found.\n")
        except Exception as e:
            print(f"Error processing email {msg_id}: {e}\n")

if __name__ == "__main__":
    main()

