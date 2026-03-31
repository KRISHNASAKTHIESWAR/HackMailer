import base64
import json
import os
from datetime import datetime, timedelta

PROCESSED_FILE = os.path.join(os.path.dirname(__file__), '..', 'processed_emails.json')

def load_processed_ids():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_processed_id(msg_id):
    ids = load_processed_ids()
    ids.add(msg_id)
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(list(ids), f)

def fetch_hackathon_emails(service, maxResults=30, days_back=90):
    # Only fetch emails from the last N days
    after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
    query = f'subject:(hackathon OR "register now" OR deadline) after:{after_date}'
    results = service.users().messages().list(userId='me', q=query, maxResults=maxResults).execute()
    all_messages = results.get('messages', [])

    # Filter out already-processed emails
    processed = load_processed_ids()
    new_messages = [m for m in all_messages if m['id'] not in processed]
    print(f"📬 {len(all_messages)} matching emails found, {len(new_messages)} new (unprocessed).\n")
    return new_messages

def get_email_html_body(message):
    payload = message.get('payload', {})
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/html':
                data = part['body'].get('data')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
            # Handle nested multipart
            if 'parts' in part:
                for subpart in part['parts']:
                    if subpart.get('mimeType') == 'text/html':
                        data = subpart['body'].get('data')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8')
    elif payload.get('mimeType') == 'text/html':
        data = payload['body'].get('data')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8')
    return None
