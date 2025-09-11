# static page

import requests
from bs4 import BeautifulSoup
import re

def scrape_deadline_static(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        full_text = soup.get_text(separator=' ', strip=True)

        # Regex pattern to find phrases like "Deadline: 25 August 2025" or similar
        pattern = r'(Deadline|Last Date|Submission Deadline|Ends on)\s*[:\-]?\s*(\d{1,2} \w+ \d{4}|\w+ \d{1,2},? \d{4})'
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            return match.group(2)
        else:
            return "Deadline not found with static scraping."
    except Exception as e:
        return f"Error fetching page: {e}"

#dynamic page

from playwright.sync_api import sync_playwright
import re
from bs4 import BeautifulSoup

def scrape_deadline_dynamic(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=15000)
        content = page.content()
        browser.close()

        soup = BeautifulSoup(content, "html.parser")
        full_text = soup.get_text(separator=' ', strip=True)

        # Same regex pattern for deadline date
        pattern = r'(Deadline|Last Date|Submission Deadline|Ends on)\s*[:\-]?\s*(\d{1,2} \w+ \d{4}|\w+ \d{1,2},? \d{4})'
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            return match.group(2)
        else:
            return "Deadline not found with dynamic scraping."

#test
url = "https://www.hackerearth.com/challenges/hackathon/mcp-hackathon/?utm_source=he_email&utm_medium=cta&utm_campaign=mcp-hackathon"

# For static page
deadline = scrape_deadline_static(url)
print(f"Extracted deadline (static): {deadline}")

# For dynamic page
deadline = scrape_deadline_dynamic(url)
print(f"Extracted deadline (dynamic): {deadline}")
