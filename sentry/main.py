from fastapi import FastAPI, Request, Form
from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import firestore
import os
import google.generativeai as genai
from triage import analyze_patient_input
from concierge import book_appointment
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
db = firestore.Client(project=os.getenv("FIRESTORE_PROJECT_ID"))

@app.post("/webhook")
async def whatsapp_webhook(From: str = Form(...), Body: str = Form(""), MediaUrl0: str = Form(None)):
    """
    Handle incoming WhatsApp messages from Twilio.
    """
    # Normalize phone number (Twilio format is whatsapp:+15550109999)
    phone = From.replace("whatsapp:", "")
    
    # Retrieve patient context from Firestore
    patient_ref = db.collection("patients").document(phone)
    doc = patient_ref.get()
    
    if not doc.exists:
        response = MessagingResponse()
        response.message("Welcome to Medi-Path. Please contact your clinic to be added to the system.")
        return str(response)

    patient_data = doc.to_dict()
    recovery_plan = patient_data.get("recovery_plan")
    history = patient_data.get("conversation_history", [])

    # Process input with Gemini 2.0 Flash (Thinking Mode)
    # MediaUrl0 will be passed if it's an image
    ai_result = analyze_patient_input(Body, MediaUrl0, recovery_plan, history)
    
    # Check for Red Flag
    if ai_result.get("red_flag_detected"):
        booking = book_appointment(patient_data["patient_meta"]["name"], ai_result["reasoning"])
        if booking:
            escalation_msg = (
                f"\n\n⚠️ Red Flag Detected. I have scheduled an emergency consult for you.\n"
                f"🕒 Time: {booking['time']} today\n"
                f"📹 Video Link: {booking['link']}\n"
                f"Please confirm you can attend."
            )
            ai_result["response_to_patient"] += escalation_msg
    
    # Update Firestore
    history.append({"role": "user", "content": Body, "image": MediaUrl0})
    history.append({"role": "assistant", "content": ai_result["response_to_patient"]})
    
    patient_ref.update({
        "conversation_history": history,
        "last_contact": firestore.SERVER_TIMESTAMP,
        "status": "escalated" if ai_result.get("red_flag_detected") else "active"
    })

    # Respond via Twilio
    response = MessagingResponse()
    response.message(ai_result["response_to_patient"])
    return str(response)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
