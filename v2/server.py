# pubsub server.py for manual email run check
import os
from google.cloud import pubsub_v1
from dotenv import load_dotenv as dotenv
dotenv()

project_id = os.getenv("project_id")
subscription_id = os.getenv("subscription_id")


def pull_messages(project_id, subscription_id):
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    response = subscriber.pull(
        request={"subscription": subscription_path, "max_messages": 10}
    )

    for received_message in response.received_messages:
        data = received_message.message.data.decode("utf-8")
        print(f"Received message: {data}")
        # Process the notification (e.g., parse historyId, fetch emails)

        # Acknowledge message to remove from queue
        subscriber.acknowledge(
            request={"subscription": subscription_path, "ack_ids": [received_message.ack_id]}
        )

    
