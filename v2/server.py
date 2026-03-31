# pubsub server.py for manual email run check
import os
from google.cloud import pubsub_v1
from dotenv import load_dotenv as dotenv
dotenv()

project_id = os.getenv("project_id")
subscription_id = os.getenv("subscription_id")


def pull_messages(project_id, subscription_id, credentials=None):
    if not project_id or not subscription_id:
        print("⚠️  Pub/Sub project_id or subscription_id not set in .env, skipping.")
        return

    try:
        subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
        subscription_path = subscriber.subscription_path(project_id, subscription_id)

        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": 10}
        )

        for received_message in response.received_messages:
            data = received_message.message.data.decode("utf-8")
            print(f"Received message: {data}")

            subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": [received_message.ack_id]}
            )

        print(f"✅ Pulled {len(response.received_messages)} Pub/Sub message(s).")
    except Exception as e:
        print(f"⚠️  Pub/Sub pull failed: {e}")
