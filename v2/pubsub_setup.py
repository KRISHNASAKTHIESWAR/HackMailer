#SETUP SCRIPT FOR GMAIL PUSH NOTIFICATIONS WITH PUB/SUB

#!/usr/bin/env python3


"""
Complete setup script for Gmail Push Notifications with Pub/Sub
Run this script to set up all required permissions and topics
"""

import subprocess
import sys
import json
import os
from dotenv import load_dotenv as dotenv
from google.cloud import pubsub_v1
from google.cloud import iam
from google.oauth2 import service_account
dotenv()

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def setup_gcloud_project(project_id):
    """Set up gcloud project and enable required APIs"""
    print("=" * 60)
    print("STEP 1: Setting up Google Cloud Project")
    print("=" * 60)
    
    # Set the project
    if not run_command(f"gcloud config set project {project_id}", "Setting gcloud project"):
        print("⚠️ Make sure you have gcloud CLI installed and authenticated")
        return False
    
    # Enable required APIs
    apis = [
        "gmail.googleapis.com",
        "pubsub.googleapis.com",
        "iam.googleapis.com"
    ]
    
    for api in apis:
        if not run_command(f"gcloud services enable {api}", f"Enabling {api}"):
            print(f"⚠️ Failed to enable {api}")
            return False
    
    return True

def create_pubsub_topic(project_id, topic_id):
    """Create Pub/Sub topic"""
    print("\n" + "=" * 60)
    print("STEP 2: Creating Pub/Sub Topic")
    print("=" * 60)
    
    try:
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, topic_id)
        
        try:
            # Try to create the topic
            topic = publisher.create_topic(request={"name": topic_path})
            print(f"Created topic: {topic.name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"Topic {topic_id} already exists")
            else:
                print(f"Error creating topic: {e}")
                return False
        
        return topic_path
        
    except Exception as e:
        print(f"Error setting up Pub/Sub topic: {e}")
        return None

def setup_gmail_permissions(project_id, topic_path):
    """Set up Gmail API permissions for Pub/Sub"""
    print("\n" + "=" * 60)
    print("STEP 3: Setting up Gmail API Permissions")
    print("=" * 60)
    
    # Gmail API service account email
    gmail_service_account = "gmail-api-push@system.gserviceaccount.com"
    
    # Grant Gmail API permission to publish to the topic
    command = f"""gcloud pubsub topics add-iam-policy-binding {topic_path.split('/')[-1]} \\
        --member="serviceAccount:{gmail_service_account}" \\
        --role="roles/pubsub.publisher" \\
        --project={project_id}"""
    
    if run_command(command, "Adding Gmail API permissions to Pub/Sub topic"):
        print("Gmail API now has permission to publish to your topic")
        return True
    else:
        print("Failed to set Gmail API permissions")
        return False

def create_subscription(project_id, topic_id, subscription_id):
    """Create Pub/Sub subscription"""
    print("\n" + "=" * 60)
    print("STEP 4: Creating Pub/Sub Subscription")
    print("=" * 60)
    
    try:
        subscriber = pubsub_v1.SubscriberClient()
        publisher = pubsub_v1.PublisherClient()
        
        topic_path = publisher.topic_path(project_id, topic_id)
        subscription_path = subscriber.subscription_path(project_id, subscription_id)
        
        try:
            subscription = subscriber.create_subscription(
                request={
                    "name": subscription_path,
                    "topic": topic_path,
                }
            )
            print(f"Created subscription: {subscription.name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f" Subscription {subscription_id} already exists")
            else:
                print(f" Error creating subscription: {e}")
                return False
        
        return subscription_path
        
    except Exception as e:
        print(f" Error creating subscription: {e}")
        return None

def test_setup(project_id, topic_id):
    """Test the setup by publishing a test message"""
    print("\n" + "=" * 60)
    print("STEP 5: Testing Setup")
    print("=" * 60)
    
    try:
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, topic_id)
        
        # Publish a test message
        test_message = "Test message from setup script"
        future = publisher.publish(topic_path, test_message.encode("utf-8"))
        message_id = future.result()
        
        print(f" Test message published successfully. Message ID: {message_id}")
        print(" Pub/Sub setup is working correctly!")
        return True
        
    except Exception as e:
        print(f" Test failed: {e}")
        return False

def generate_updated_auth_code():
    """Generate updated auth.py with correct scopes"""
    auth_code = '''import os.path

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
            creds.refresh(Request())
        else:
            # Delete old token to force re-authentication with new scopes
            if os.path.exists('token.json'):
                os.remove('token.json')
                print("Deleted old token.json to refresh permissions")
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            # Request offline access and force consent for new permissions
            creds = flow.run_local_server(port=8080, access_type='offline', prompt='consent')
        
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
    return creds
'''
    
    try:
        with open('auth_updated.py', 'w') as f:
            f.write(auth_code)
        print(" Generated auth_updated.py with correct scopes")
        print(" Replace your auth.py with auth_updated.py after setup")
        return True
    except Exception as e:
        print(f"Failed to generate updated auth code: {e}")
        return False

def main():
    """Main setup function"""
    print("Gmail Push Notification Setup Script")
    print("=" * 60)
    
    # Configuration
    project_id = os.getenv("project_id")
    topic_id = os.getenv("topic_id")
    subscription_id = os.getenv("subscription_id")

    print(f"Project ID: {project_id}")
    print(f"Topic ID: {topic_id}")
    print(f"Subscription ID: {subscription_id}")
    
    # Step 1: Setup gcloud project
    if not setup_gcloud_project(project_id):
        print("Failed to setup gcloud project. Exiting.")
        return False
    
    # Step 2: Create Pub/Sub topic
    topic_path = create_pubsub_topic(project_id, topic_id)
    if not topic_path:
        print("Failed to create Pub/Sub topic. Exiting.")
        return False
    
    # Step 3: Setup Gmail permissions
    if not setup_gmail_permissions(project_id, topic_path):
        print("Failed to setup Gmail permissions. Exiting.")
        return False
    
    # Step 4: Create subscription
    subscription_path = create_subscription(project_id, topic_id, subscription_id)
    if not subscription_path:
        print("Failed to create subscription. Exiting.")
        return False
    
    # Step 5: Test setup
    if not test_setup(project_id, topic_id):
        print("Setup test failed. Check your configuration.")
        return False
    
    # Generate updated auth code
    generate_updated_auth_code()
    
    print("\n" + "" * 20)
    print("SUCCESS! Gmail Push Notifications Setup Complete!")
    print("" * 20)
    print("\nNext steps:")
    print("1. Replace your auth.py with auth_updated.py")
    print("2. Delete your token.json file (if it exists)")
    print("3. Run your automated_hackathon_monitor.py script")
    print("4. Re-authenticate when prompted to grant new permissions")
    print("\n Your system is now ready for real-time email notifications!")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n Setup cancelled by user")
    except Exception as e:
        print(f"\n Setup failed with error: {e}")
        print("Please check your Google Cloud permissions and try again")