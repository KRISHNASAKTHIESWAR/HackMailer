from bs4 import BeautifulSoup

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
