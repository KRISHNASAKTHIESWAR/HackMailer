import os.path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Updated scopes - added pubsub scope for push notifications
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify', 
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/pubsub'
]

def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # If refresh fails, delete token and re-authenticate
                if os.path.exists('token.json'):
                    os.remove('token.json')
                    print("🔄 Deleted expired token, re-authenticating...")
                creds = None
        
        if not creds:
            # Delete old token to force re-authentication with new scopes
            if os.path.exists('token.json'):
                os.remove('token.json')
                print("🔄 Deleted old token.json to refresh permissions")
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            # Request offline access and force consent for new permissions
            creds = flow.run_local_server(port=8080, access_type='offline', prompt='consent')
        
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
    return creds