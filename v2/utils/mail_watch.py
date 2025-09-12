def get_label_id(service, label_name="INBOX"):
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    for label in labels:
        if label['name'].lower() == label_name.lower():
            return label['id']
    return None


def start_gmail_watch(service, topic_name, label_id=None):
    body = {'topicName': topic_name}
    if label_id:
        body['labelIds'] = [label_id]
    response = service.users().watch(userId='me', body=body).execute()
    print(f"Watch started: {response}")
    return response

