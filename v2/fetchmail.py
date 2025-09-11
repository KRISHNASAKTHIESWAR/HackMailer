import base64

def fetch_hackathon_emails(service, maxResults=30):
    query = 'subject:(hackathon OR "register now" OR deadline)'
    results = service.users().messages().list(userId='me', q=query, maxResults=maxResults).execute()
    messages = results.get('messages', [])
    return messages

def get_email_html_body(message):
    payload = message.get('payload', {})
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/html':
                data = part['body']['data']
                html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                return html_body
    elif payload.get('mimeType') == 'text/html':
        data = payload['body']['data']
        html_body = base64.urlsafe_b64decode(data).decode('utf-8')
        return html_body
    return None
