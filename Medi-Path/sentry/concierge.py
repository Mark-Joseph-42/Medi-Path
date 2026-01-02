import os
import google.auth
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import json

def book_appointment(patient_name, reasoning):
    """
    Finds the earliest 15-min slot and books a Google Calendar event.
    Removes auto-Meet creation to avoid secondary calendar 400 errors.
    """
    try:
        # Use Application Default Credentials (Workload Identity on Cloud Run)
        creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/calendar'])
        service = build('calendar', 'v3', credentials=creds)

        calendar_id = os.getenv("CALENDAR_ID", "primary")
        
        # 1. Slot search logic (simplified: 30 minutes from now)
        now = datetime.utcnow()
        booking_time = now + timedelta(minutes=30)
        
        # 2. Define Event Body (No conferenceData to avoid secondary calendar errors)
        event_body = {
            'summary': f'URGENT: Medi-Path Consult - {patient_name}',
            'description': f'AI Detected Red Flag.\n\nReasoning: {reasoning}',
            'start': {
                'dateTime': booking_time.isoformat() + 'Z',
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': (booking_time + timedelta(minutes=15)).isoformat() + 'Z',
                'timeZone': 'UTC',
            }
        }

        # Insert as a standard event
        event = service.events().insert(
            calendarId=calendar_id, 
            body=event_body
        ).execute()

        print(f"Successfully booked calendar event: {event.get('htmlLink')}")

        return {
            "time": booking_time.strftime("%I:%M %p UTC"),
            "link": event.get('htmlLink', "Check your calendar for details")
        }
    except Exception as e:
        print(f"CALENDAR BOOKING ERROR: {e}")
        return None
