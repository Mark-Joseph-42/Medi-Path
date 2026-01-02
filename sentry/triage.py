import os
import google.generativeai as genai
import json
import requests

def analyze_patient_input(text, image_url, recovery_plan, history):
    """
    Analyzes patient input using Gemini 2.0 Flash (Thinking Mode).
    """
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    # Use thinking mode model
    model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')

    system_instruction = (
        "You are an expert post-operative triage nurse. Your goal is to monitor the patient's recovery "
        "and detect 'Red Flags' defined in their recovery plan. "
        "Be empathetic but precise. Use internal reasoning to avoid false positives."
    )

    prompt = f"""
    {system_instruction}

    Patient Recovery Plan:
    {json.dumps(recovery_plan, indent=2)}

    Conversation History:
    {json.dumps(history[-5:], indent=2)}

    Current Patient Input: "{text}"
    Attached Image: {"Yes" if image_url else "No"}

    Task:
    1. Reason through the input. Is this a red flag? Check meds, symptoms, and the plan.
    2. If an image is provided, analyze it for infection (erythema, pus, etc.).
    3. Determine if "red_flag_detected" is true.
    4. Provide a "response_to_patient".

    Output JSON:
    {{
      "red_flag_detected": boolean,
      "reasoning": "string (internal thinking)",
      "response_to_patient": "string"
    }}
    """

    content = [prompt]
    
    if image_url:
        # Fetch image bytes
        img_response = requests.get(image_url)
        if img_response.status_code == 200:
            content.append({"mime_type": "image/jpeg", "data": img_response.content})

    response = model.generate_content(content)
    
    try:
        content = response.text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
        
        return json.loads(content)
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        return {
            "red_flag_detected": False,
            "response_to_patient": "I'm processing your update. Please wait a moment."
        }
