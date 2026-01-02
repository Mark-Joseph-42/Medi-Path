import os
from google import genai
from google.genai import types
import json

def extract_recovery_plan(pdf_file):
    """
    Extracts structured medical data from a PDF discharge summary using Gemini 2.5 Flash.
    """
    project_id = os.getenv("FIRESTORE_PROJECT_ID")
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location="us-central1"
    )

    system_instruction = (
        "You are an expert medical data archivist. Your goal is to extract a precise Recovery Plan "
        "from the provided discharge summary. Extract only explicit facts. If a field is missing, "
        "return null. Do not infer or hallucinate."
    )

    prompt = """
    Target Schema:
    {
      "patient_meta": { "name": "string", "id": "string", "phone": "E.164_string" },
      "medications": [ 
        { 
          "drug": "string", 
          "dose": "string", 
          "freq": "string (e.g., 'once daily', 'twice daily', 'morning', 'evening', 'with meals')",
          "instructions": "string (any special instructions)"
        } 
      ],
      "red_flags": [ "string", "string" ],
      "follow_up": { "date": "ISO8601_string", "provider": "string" }
    }

    Important: For medications, extract the frequency as precisely as possible (e.g., "twice daily", "every 8 hours", "morning and evening").
    Return the output as a valid JSON object.
    """

    # Read PDF content
    pdf_data = pdf_file.read()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=pdf_data, mime_type="application/pdf"),
            prompt
        ],
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json"
        )
    )
    
    try:
        return json.loads(response.text)
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        return None
