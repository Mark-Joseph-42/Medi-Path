import os
from twilio.rest import Client
from google.cloud import firestore
from datetime import datetime, timezone

# Initialize Twilio client
def get_twilio_client():
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    return Client(account_sid, auth_token)

def send_whatsapp_message(to_phone: str, message: str):
    """
    Send a WhatsApp message via Twilio.
    """
    try:
        client = get_twilio_client()
        twilio_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        
        msg = client.messages.create(
            from_=twilio_number,
            body=message,
            to=f"whatsapp:{to_phone}"
        )
        print(f"Sent reminder to {to_phone}: {msg.sid}")
        return True
    except Exception as e:
        print(f"Failed to send WhatsApp message to {to_phone}: {e}")
        return False

def get_reminder_times():
    """
    Returns a mapping of frequency keywords to reminder hours (UTC).
    """
    return {
        "once daily": [8],  # 8 AM
        "twice daily": [8, 20],  # 8 AM, 8 PM
        "three times daily": [8, 14, 20],  # 8 AM, 2 PM, 8 PM
        "four times daily": [8, 12, 16, 20],  # 8 AM, 12 PM, 4 PM, 8 PM
        "morning": [8],
        "evening": [20],
        "night": [21],
        "bedtime": [22],
    }

def should_send_reminder(freq: str, current_hour: int) -> bool:
    """
    Check if a reminder should be sent based on medication frequency and current hour.
    """
    reminder_map = get_reminder_times()
    freq_lower = freq.lower() if freq else ""
    
    for keyword, hours in reminder_map.items():
        if keyword in freq_lower:
            return current_hour in hours
    
    # Default: Check if any time indicator is present
    if "daily" in freq_lower or "day" in freq_lower:
        return current_hour == 8  # Default to morning
    
    return False

def format_medication_reminder(patient_name: str, medications: list, current_hour: int) -> str:
    """
    Format a friendly medication reminder message.
    """
    time_greeting = "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 17 else "Good evening"
    
    med_list = []
    for med in medications:
        if should_send_reminder(med.get("freq", ""), current_hour):
            drug = med.get("drug", "medication")
            dose = med.get("dose", "")
            med_list.append(f"• {drug} {dose}".strip())
    
    if not med_list:
        return None
    
    message = f"💊 {time_greeting}, {patient_name}!\n\n"
    message += "It's time to take your medication:\n"
    message += "\n".join(med_list)
    message += "\n\nReply 'done' when you've taken them, or let me know if you have any questions!"
    
    return message

def process_all_reminders(db: firestore.Client):
    """
    Process all patients and send medication reminders as needed.
    """
    current_hour = datetime.now(timezone.utc).hour
    print(f"Processing reminders for hour {current_hour} UTC")
    
    patients = db.collection("patients").where("status", "in", ["active", "onboarding_pending"]).stream()
    
    sent_count = 0
    for doc in patients:
        patient_data = doc.to_dict()
        phone = doc.id
        recovery_plan = patient_data.get("recovery_plan", {})
        medications = recovery_plan.get("medications", [])
        patient_name = recovery_plan.get("patient_meta", {}).get("name", "there")
        
        if not medications:
            continue
        
        message = format_medication_reminder(patient_name, medications, current_hour)
        
        if message:
            if send_whatsapp_message(phone, message):
                sent_count += 1
                # Update last reminder time
                db.collection("patients").document(phone).update({
                    "last_reminder": firestore.SERVER_TIMESTAMP
                })
    
    print(f"Sent {sent_count} medication reminders")
    return sent_count
