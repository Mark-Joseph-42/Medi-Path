import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.cloud import firestore
import json
from parser import extract_recovery_plan

load_dotenv()

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
                edited_json = st.text_area("Verify and Edit JSON", value=json.dumps(extracted_data, indent=2), height=400)
                
                if st.button("Finalize and Activate Sentry"):
                    try:
                        patient_data = json.loads(edited_json)
                        phone = patient_data.get("patient_meta", {}).get("phone")
                        if not phone:
                            st.error("Phone number is required for activation.")
                        else:
                            db.collection("patients").document(phone).set({
                                "status": "onboarding_pending",
                                "recovery_plan": patient_data,
                                "conversation_history": [],
                                "last_contact": firestore.SERVER_TIMESTAMP
                            })
                            st.balloons()
                            st.success(f"Recovery plan activated for {phone}")
                    except json.JSONDecodeError:
                        st.error("Invalid JSON format. Please fix the JSON before finalizing.")
        else:
            st.error("Failed to extract data. Please try again or check the API key.")
