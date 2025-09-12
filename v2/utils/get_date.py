import re
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from PIL import Image
import pytesseract
from io import BytesIO

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

