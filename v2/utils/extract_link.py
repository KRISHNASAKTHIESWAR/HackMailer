from bs4 import BeautifulSoup

# Known email tracking/redirect domains to skip
TRACKING_DOMAINS = [
    'sendgrid.net', 't-info.mail.adobe.com', 'mailchimp.com',
    'click.em', 'trk.', 'tracking.', 'click.', 'links.', 'go.', 'email.',
    'mandrillapp.com', 'list-manage.com', 'hubspotemail.net',
]

def is_tracking_url(href):
    href_lower = href.lower()
    return any(domain in href_lower for domain in TRACKING_DOMAINS)

def extract_registration_links(html_body):
    soup = BeautifulSoup(html_body, "html.parser")
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if is_tracking_url(href):
            continue
        text = (a.get_text() or "").strip().lower()
        if any(keyword in text for keyword in ['register', 'sign up', 'apply', 'join']):
            links.append(href)
    if not links:
        for a in soup.find_all('a', href=True):
            href = a['href']
            if is_tracking_url(href):
                continue
            if any(domain in href.lower() for domain in ['devpost', 'hackerearth', 'challenge', 'hackathon', 'competitions', 'competition']):
                links.append(href)
    return links
