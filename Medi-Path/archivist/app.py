import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.cloud import firestore
import json
from parser import extract_recovery_plan

# load_dotenv()

# Configure APIs
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
db = firestore.Client(project=os.getenv("FIRESTORE_PROJECT_ID"))

st.set_page_config(page_title="Medi-Path Archivist", layout="wide")

st.title("📂 Medi-Path Archivist")
st.markdown("### High-Fidelity Discharge Ingestion")

uploaded_file = st.file_uploader("Upload Patient Discharge Summary (PDF)", type="pdf")

if uploaded_file:
    with st.spinner("Transmuting document to structured schema..."):
        extracted_data = extract_recovery_plan(uploaded_file)
        
        if extracted_data:
            st.success("Extraction Complete!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Original Document")
                # Using st.download_button as a simple way to show the file exists
                st.download_button("Download Uploaded PDF", data=uploaded_file.getvalue(), file_name="discharge.pdf")
                st.info("In production, use a PDF viewer component.")
                
            with col2:
                st.subheader("Extracted Data")
                
                # Extract phone from JSON initially to pre-fill
                initial_phone = extracted_data.get("patient_meta", {}).get("phone", "")
                phone_input = st.text_input("Patient WhatsApp Number (e.g. +1234567890)", value=initial_phone)
                st.subheader("Final Verification")
                
                # NEW: Dedicated Phone Number Input
                initial_phone = extracted_data.get("patient_meta", {}).get("phone", "") if extracted_data else ""
                phone_input = st.text_input("Patient WhatsApp Number (e.g. +14155552671)", value=initial_phone)
                
                edited_json = st.text_area("Recovery Plan Details (JSON)", value=json.dumps(extracted_data, indent=2), height=300)
                
                if st.button("Finalize and Activate Sentry"):
                    try:
                        patient_data = json.loads(edited_json)
                        if not phone_input:
                            st.error("Please enter a WhatsApp number to continue.")
                        else:
                            # Update the JSON with the manual phone input
                            if "patient_meta" not in patient_data:
                                patient_data["patient_meta"] = {}
                            patient_data["patient_meta"]["phone"] = phone_input

                            db.collection("patients").document(phone_input).set({
                                "status": "onboarding_pending",
                                "recovery_plan": patient_data,
                                "conversation_history": [],
                                "last_contact": firestore.SERVER_TIMESTAMP
                            })
                            st.balloons()
                            st.success(f"Success! Sentry activated for {phone_input}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.error("Failed to extract data. Please try again or check the API key.")
