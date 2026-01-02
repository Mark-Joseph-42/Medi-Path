import os
from google import genai
from google.genai import types
import json
import requests

def analyze_patient_input(text, image_url, recovery_plan, history):
    """
    Analyzes patient input using Gemini 2.5 Flash via Vertex AI.
    """
    project_id = os.getenv("FIRESTORE_PROJECT_ID")
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location="us-central1"
    )

    system_instruction = (
        "You are an expert post-operative triage nurse. Your goal is to monitor the patient's recovery "
        "and detect 'Red Flags' defined in their recovery plan. "
        "Be empathetic but precise. Use internal reasoning to avoid false positives."
    )

    prompt = f"""
    Patient Recovery Plan:
    {json.dumps(recovery_plan, indent=2)}

    Conversation History:
    {json.dumps(history[-5:], indent=2)}

    Current Patient Input: "{text}"
    Attached Image: {"Yes" if image_url else "No"}

    Task:
    1. Reason through the input. Is this a red flag? Check meds, symptoms, and the plan.
    2. If an image is provided, analyze it for infection.
    3. Determine if "red_flag_detected" is true.
    1. Determine if a "red_flag_detected" (boolean) is present.
    2. Provide internal "reasoning".
    3. Provide a "response_to_patient" (string).

    Constraint: Return ONLY a JSON object with these three keys.
    """

    contents = [prompt]
    if image_url:
        img_resp = requests.get(image_url)
        if img_resp.status_code == 200:
            contents.append(types.Part.from_bytes(data=img_resp.content, mime_type="image/jpeg"))

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction="You are an expert post-operative triage nurse.",
            response_mime_type="application/json"
        )
    )
    
    try:
        result = json.loads(response.text)
        # Ensure keys exist to prevent crashes
        if "response_to_patient" not in result:
            result["response_to_patient"] = "I have received your message and am reviewing your plan."
        if "red_flag_detected" not in result:
            result["red_flag_detected"] = False
        return result
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        return {
            "red_flag_detected": False,
            "response_to_patient": "I'm processing your update. Please wait a moment."
        }
