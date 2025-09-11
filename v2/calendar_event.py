from datetime import datetime, timedelta

def create_calendar_event(service, hackathon_name, deadline_date, url):
    # If deadline_date is datetime.date or datetime.datetime, convert to ISO
    if hasattr(deadline_date, 'isoformat'):
        start_date = deadline_date.isoformat()
        end_date = (deadline_date + timedelta(days=1)).isoformat()
    else:
        # If string passed, use as is or parse inside function
        start_date = deadline_date
        end_date = deadline_date

    event = {
        'summary': f"Hackathon Deadline: {hackathon_name}",
        'description': f"Register here: {url}",
        'start': {'date': start_date},
        'end': {'date': end_date},
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 60*24*7},  # 1 week before
                {'method': 'popup', 'minutes': 60*24},     # 1 day before
            ],
        },
    }
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    print(f"  Created calendar event: {created_event.get('htmlLink')}")
