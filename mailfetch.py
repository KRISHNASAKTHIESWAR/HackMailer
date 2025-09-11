# # Gmail Hackathon Email Link Extractor - Complete Script

# import os
# import base64
# from googleapiclient.discovery import build
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.oauth2.credentials import Credentials
# from bs4 import BeautifulSoup

# # If modifying these scopes, delete 'token.json'.
# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# def authenticate_gmail():
#     creds = None
#     # The token.json file stores user's access and refresh tokens
#     if os.path.exists('token.json'):
#         creds = Credentials.from_authorized_user_file('token.json', SCOPES)
#     # If there are no valid credentials, let the user log in.
#     if not creds or not creds.valid:
#         flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
#         creds = flow.run_local_server(port=0)
#         # Save credentials for next time
#         with open('token.json', 'w') as token:
#             token.write(creds.to_json())
#     return creds

# def fetch_hackathon_emails(service, maxResults=30):
#     # Search for emails about hackathons
#     query = 'subject:(hackathon OR "register now" OR deadline)'
#     results = service.users().messages().list(userId='me', q=query, maxResults=maxResults).execute()
#     messages = results.get('messages', [])
#     return messages

# def get_email_html_body(message):
#     payload = message.get('payload', {})
#     # Look for 'text/html' part
#     if 'parts' in payload:
#         for part in payload['parts']:
#             if part.get('mimeType') == 'text/html':
#                 data = part['body']['data']
#                 html_body = base64.urlsafe_b64decode(data).decode('utf-8')
#                 return html_body
#     elif payload.get('mimeType') == 'text/html':
#         data = payload['body']['data']
#         html_body = base64.urlsafe_b64decode(data).decode('utf-8')
#         return html_body
#     return None

# def extract_registration_links(html_body):
#     soup = BeautifulSoup(html_body, "html.parser")
#     links = []

#     # Find anchors with relevant button words
#     for a in soup.find_all('a', href=True):
#         text = (a.get_text() or "").strip().lower()
#         href = a['href']
#         if any(keyword in text for keyword in ['register', 'sign up', 'apply', 'join']):
#             links.append(href)

#     # Fallback: extract platform links
#     if not links:
#         for a in soup.find_all('a', href=True):
#             href = a['href']
#             if any(domain in href.lower() for domain in ['devpost', 'hackerearth', 'challenge', 'hackathon']):
#                 links.append(href)

#     return links

# def main():
#     creds = authenticate_gmail()
#     service = build('gmail', 'v1', credentials=creds)
#     messages = fetch_hackathon_emails(service, maxResults=30)
#     print(f"\nFound {len(messages)} hackathon-related emails.\n")

#     for msg in messages:
#         msg_id = msg['id']
#         try:
#             message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
#             html_body = get_email_html_body(message)
#             if html_body:
#                 links = extract_registration_links(html_body)
#                 if links:
#                     print(f"Message ID: {msg_id}")
#                     print("Extracted registration links:")
#                     for link in links:
#                         print(f"  {link}")
#                     print("")
#                 else:
#                     print(f"Message ID: {msg_id} -- No registration links found.\n")
#             else:
#                 print(f"Message ID: {msg_id} -- No HTML body found.\n")
#         except Exception as e:
#             print(f"Error processing email {msg_id}: {e}\n")

# if __name__ == "__main__":
#     main()

# #V2
# import os
# import base64
# import re
# import requests
# from bs4 import BeautifulSoup
# from googleapiclient.discovery import build
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.oauth2.credentials import Credentials
# from playwright.sync_api import sync_playwright

# # Gmail API scope
# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# # Authenticate Gmail API
# def authenticate_gmail():
#     creds = None
#     if os.path.exists('token.json'):
#         creds = Credentials.from_authorized_user_file('token.json', SCOPES)
#     if not creds or not creds.valid:
#         flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
#         creds = flow.run_local_server(port=8080)
#         with open('token.json', 'w') as token:
#             token.write(creds.to_json())
#     return creds

# # Fetch emails related to hackathons
# def fetch_hackathon_emails(service, maxResults=30):
#     query = 'subject:(hackathon OR "register now" OR deadline)'
#     results = service.users().messages().list(userId='me', q=query, maxResults=maxResults).execute()
#     messages = results.get('messages', [])
#     return messages

# # Extract HTML body from email message
# def get_email_html_body(message):
#     payload = message.get('payload', {})
#     if 'parts' in payload:
#         for part in payload['parts']:
#             if part.get('mimeType') == 'text/html':
#                 data = part['body']['data']
#                 html_body = base64.urlsafe_b64decode(data).decode('utf-8')
#                 return html_body
#     elif payload.get('mimeType') == 'text/html':
#         data = payload['body']['data']
#         html_body = base64.urlsafe_b64decode(data).decode('utf-8')
#         return html_body
#     return None

# # Extract registration links from email HTML body
# def extract_registration_links(html_body):
#     soup = BeautifulSoup(html_body, "html.parser")
#     links = []

#     # First look for links with button-like text
#     for a in soup.find_all('a', href=True):
#         text = (a.get_text() or "").strip().lower()
#         href = a['href']
#         if any(keyword in text for keyword in ['register', 'sign up', 'apply', 'join']):
#             links.append(href)

#     # Fallback: search for known hackathon platform domains
#     if not links:
#         for a in soup.find_all('a', href=True):
#             href = a['href']
#             if any(domain in href.lower() for domain in ['devpost', 'hackerearth', 'challenge', 'hackathon']):
#                 links.append(href)

#     return links

# # Scrape hackathon deadline and name using static requests
# def scrape_deadline_and_name_static(url):
#     try:
#         response = requests.get(url, timeout=10)
#         response.raise_for_status()
#         html = response.text
#         soup = BeautifulSoup(html, "html.parser")
#         full_text = soup.get_text(separator=' ', strip=True)

#         # Extract deadline using regex pattern
#         deadline_pattern = r'(Deadline|Last Date|Submission Deadline|Ends on)\s*[:\-]?\s*(\d{1,2} \w+ \d{4}|\w+ \d{1,2},? \d{4})'
#         deadline_match = re.search(deadline_pattern, full_text, re.IGNORECASE)
#         deadline = deadline_match.group(2) if deadline_match else "Deadline not found"

#         # Try to extract hackathon name - usually inside <title> tag or <h1>
#         title = soup.title.string.strip() if soup.title else None
#         if not title:
#             h1 = soup.find('h1')
#             title = h1.get_text(strip=True) if h1 else "Name not found"

#         return title, deadline
#     except Exception as e:
#         return f"Error fetching page: {e}", None

# # Scrape hackathon deadline and name using Playwright (dynamic)
# def scrape_deadline_and_name_dynamic(url):
#     try:
#         with sync_playwright() as p:
#             browser = p.chromium.launch(headless=True)
#             page = browser.new_page()
#             page.goto(url, timeout=15000)
#             content = page.content()
#             browser.close()

#             soup = BeautifulSoup(content, "html.parser")
#             full_text = soup.get_text(separator=' ', strip=True)

#             deadline_pattern = r'(Deadline|Last Date|Submission Deadline|Ends on)\s*[:\-]?\s*(\d{1,2} \w+ \d{4}|\w+ \d{1,2},? \d{4})'
#             deadline_match = re.search(deadline_pattern, full_text, re.IGNORECASE)
#             deadline = deadline_match.group(2) if deadline_match else "Deadline not found"

#             # Extract hackathon name from <title> or <h1>
#             title = soup.title.string.strip() if soup.title else None
#             if not title:
#                 h1 = soup.find('h1')
#                 title = h1.get_text(strip=True) if h1 else "Name not found"

#             return title, deadline
#     except Exception as e:
#         return f"Error fetching page: {e}", None

# def main():
#     creds = authenticate_gmail()
#     service = build('gmail', 'v1', credentials=creds)

#     messages = fetch_hackathon_emails(service, maxResults=20)
#     print(f"Found {len(messages)} hackathon-related emails.\n")

#     for msg in messages:
#         msg_id = msg['id']
#         try:
#             message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
#             html_body = get_email_html_body(message)
#             if html_body:
#                 links = extract_registration_links(html_body)
#                 if links:
#                     print(f"Message ID: {msg_id}")
#                     for url in links:
#                         print(f" Visiting: {url}")
#                         # Try static scraping first
#                         name, deadline = scrape_deadline_and_name_static(url)
#                         if deadline == "Deadline not found":
#                             # fallback to dynamic scraping
#                             name, deadline = scrape_deadline_and_name_dynamic(url)
#                         print(f"  Hackathon: {name}")
#                         print(f"  Deadline: {deadline}\n")
#                 else:
#                     print(f"Message ID: {msg_id} -- No registration links found.\n")
#             else:
#                 print(f"Message ID: {msg_id} -- No HTML body found.\n")
#         except Exception as e:
#             print(f"Error processing email {msg_id}: {e}\n")

# if __name__ == "__main__":
#     main()

# v3

import os
import base64
import re
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from playwright.sync_api import sync_playwright
from PIL import Image
import pytesseract
from io import BytesIO

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

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

def extract_registration_links(html_body):
    soup = BeautifulSoup(html_body, "html.parser")
    links = []
    for a in soup.find_all('a', href=True):
        text = (a.get_text() or "").strip().lower()
        href = a['href']
        if any(keyword in text for keyword in ['register', 'sign up', 'apply', 'join']):
            links.append(href)
    if not links:
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(domain in href.lower() for domain in ['devpost', 'hackerearth', 'challenge', 'hackathon']):
                links.append(href)
    return links

def extract_dates_from_text(text):
    # Regex to find various date formats (simple and common ones)
    date_patterns = [
        r'\b\d{1,2} \w+ \d{4}\b',        # 25 August 2025
        r'\b\w+ \d{1,2},? \d{4}\b',      # August 25, 2025
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # 25/08/2025 or 8/25/2025
        r'\b\d{4}-\d{1,2}-\d{1,2}\b'     # 2025-08-25
    ]
    dates_found = []
    for pattern in date_patterns:
        found = re.findall(pattern, text)
        dates_found.extend(found)
    return list(set(dates_found))  # unique dates

def scrape_deadline_and_name_static(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        full_text = soup.get_text(separator=' ', strip=True)
        deadline_pattern = r'(Deadline|Last Date|Submission Deadline|Ends on)\s*[:\-]?\s*(\d{1,2} \w+ \d{4}|\w+ \d{1,2},? \d{4})'
        deadline_match = re.search(deadline_pattern, full_text, re.IGNORECASE)
        deadline = deadline_match.group(2) if deadline_match else None
        title = soup.title.string.strip() if soup.title else None
        if not title:
            h1 = soup.find('h1')
            title = h1.get_text(strip=True) if h1 else "Name not found"
        return title, deadline
    except Exception as e:
        return f"Error fetching page: {e}", None

def scrape_deadline_and_name_dynamic(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            content = page.content()
            soup = BeautifulSoup(content, "html.parser")
            full_text = soup.get_text(separator=' ', strip=True)
            deadline_pattern = r'(Deadline|Last Date|Submission Deadline|Ends on)\s*[:\-]?\s*(\d{1,2} \w+ \d{4}|\w+ \d{1,2},? \d{4})'
            deadline_match = re.search(deadline_pattern, full_text, re.IGNORECASE)
            deadline = deadline_match.group(2) if deadline_match else None

            title = soup.title.string.strip() if soup.title else None
            if not title:
                h1 = soup.find('h1')
                title = h1.get_text(strip=True) if h1 else "Name not found"
            
            # If deadline found, return immediately
            if deadline:
                browser.close()
                return title, deadline

            # OCR fallback: take screenshot and run OCR if no deadline found
            screenshot_bytes = page.screenshot(full_page=True)
            browser.close()
            
            # OCR using pytesseract
            image = Image.open(BytesIO(screenshot_bytes))
            ocr_text = pytesseract.image_to_string(image)
            dates = extract_dates_from_text(ocr_text)
            return title, f"OCR Dates found: {dates if dates else 'No dates found'}"
    except Exception as e:
        return f"Error fetching page dynamically: {e}", None


def main():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
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
                else:
                    print(f"Message ID: {msg_id} -- No registration links found.\n")
            else:
                print(f"Message ID: {msg_id} -- No HTML body found.\n")
        except Exception as e:
            print(f"Error processing email {msg_id}: {e}\n")

if __name__ == "__main__":
    main()

