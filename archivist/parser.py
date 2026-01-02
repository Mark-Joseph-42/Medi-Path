import os
import google.generativeai as genai
import json

def extract_recovery_plan(pdf_file):
    """
    Extracts structured medical data from a PDF discharge summary using Gemini 1.5 Flash.
    """
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')

    system_instruction = (
        "You are an expert medical data archivist. Your goal is to extract a precise Recovery Plan "
        "from the provided discharge summary. Extract only explicit facts. If a field is missing, "
        "return null. Do not infer or hallucinate."
    )

    prompt = f"""
    {system_instruction}

    Target Schema:
    {{
      "patient_meta": {{ "name": "string", "id": "string", "phone": "E.164_string" }},
      "medications": [ {{ "drug": "string", "dose": "string", "freq": "string" }} ],
      "red_flags": [ "string", "string" ],
      "follow_up": {{ "date": "ISO8601_string", "provider": "string" }}
    }}

    Return the output as a valid JSON object.
    """

    # Gemini 1.5 Flash supports PDF bytes directly
    response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": pdf_file.read()}])
    
    try:
        # Extract JSON from response text (handling potential markdown formatting)
        content = response.text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
        
        return json.loads(content)
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        return None
