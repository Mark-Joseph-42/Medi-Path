from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import firestore
import os
from triage import analyze_patient_input
from concierge import book_appointment

app = FastAPI()
db = firestore.Client(project=os.getenv("FIRESTORE_PROJECT_ID"))

@app.post("/webhook")
async def whatsapp_webhook(From: str = Form(...), Body: str = Form(""), MediaUrl0: str = Form(None)):
    """
    Handle incoming WhatsApp messages from Twilio.
    """
    # Normalize phone number
    phone = From.replace("whatsapp:", "")
    
    # Retrieve patient context
    patient_ref = db.collection("patients").document(phone)
    doc = patient_ref.get()
    
    if not doc.exists:
        response = MessagingResponse()
        response.message("Welcome to Medi-Path. Please visit the Archivist portal to enroll your profile.")
        return Response(content=str(response), media_type="application/xml")

    patient_data = doc.to_dict()
    recovery_plan = patient_data.get("recovery_plan", {})
    history = patient_data.get("conversation_history", [])

    # Process input with Gemini 2.5 Flash
    ai_result = analyze_patient_input(Body, MediaUrl0, recovery_plan, history)
    
    # Check for Red Flag
    if ai_result.get("red_flag_detected"):
        patient_name = recovery_plan.get("patient_meta", {}).get("name", "Patient")
        booking = book_appointment(patient_name, ai_result.get("reasoning", "Red flag detected"))
        if booking:
            escalation_msg = (
                f"\n\n⚠️ I have scheduled an emergency consult.\n"
                f"🕒 Time: {booking['time']}\n"
                f"📅 Event: {booking['link']}"
            )
        else:
            escalation_msg = (
                "\n\n⚠️ Please contact your clinic immediately for an urgent review."
            )
        ai_result["response_to_patient"] += escalation_msg
    
    # Update Firestore
    history.append({"role": "user", "content": Body})
    history.append({"role": "assistant", "content": ai_result["response_to_patient"]})
    
    patient_ref.update({
        "conversation_history": history,
        "last_contact": firestore.SERVER_TIMESTAMP,
        "status": "escalated" if ai_result.get("red_flag_detected") else "active"
    })

    # Respond via Twilio (TwiML XML)
    response = MessagingResponse()
    response.message(ai_result["response_to_patient"])
    return Response(content=str(response), media_type="application/xml")

if __name__ == "__main__":
    import uvicorn
    # Respect the Cloud Run PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
