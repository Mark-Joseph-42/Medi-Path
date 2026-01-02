import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import json

def book_appointment(patient_name, reasoning):
    """
    Finds the earliest 15-min slot and books a Google Calendar event.
    """
    scopes = ['https://www.googleapis.com/auth/calendar']
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if not creds_path or not os.path.exists(creds_path):
        print("Service Account credentials not found.")
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(creds_path, scopes=scopes)
        # Delegate if necessary: creds = creds.with_subject('nurse@clinic.com')
        service = build('calendar', 'v3', credentials=creds)

        calendar_id = os.getenv("CALENDAR_ID", "primary")
        
        # 1. Find a slot (Simplified: find first free 15m slot in next 4 hours)
        now = datetime.utcnow()
        start_search = now.isoformat() + 'Z'
        end_search = (now + timedelta(hours=4)).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId=calendar_id, timeMin=start_search,
            timeMax=end_search, singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        # Slot search logic (very simplified)
        booking_time = now + timedelta(minutes=30) # Default to 30 mins from now
        
        # 2. Create Event
        event = {
            'summary': f'URGENT: Red Flag Consult - {patient_name}',
            'description': f'AI Detected Red Flag. Reasoning: {reasoning}',
            'start': {
                'dateTime': booking_time.isoformat() + 'Z',
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': (booking_time + timedelta(minutes=15)).isoformat() + 'Z',
                'timeZone': 'UTC',
            },
            'conferenceData': {
                'createRequest': {
                    'requestId': f"req-{int(datetime.now().timestamp())}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            },
        }

        event = service.events().insert(
            calendarId=calendar_id, 
            body=event, 
            conferenceDataVersion=1
        ).execute()

        return {
            "time": booking_time.strftime("%I:%M %p"),
            "link": event.get('hangoutLink')
        }
    except Exception as e:
        print(f"Error booking appointment: {e}")
        return None
