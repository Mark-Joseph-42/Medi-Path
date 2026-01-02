# 🏥 Medi-Path

**AI-Powered Post-Operative Care via WhatsApp**

Medi-Path bridges the gap between hospital discharge and home recovery by providing patients with a 24/7 AI companion that monitors their health and detects emergencies.

---

## ✨ Features

- **📄 PDF Ingestion**: Upload discharge summaries and extract structured recovery plans using Gemini 2.5 Flash.
- **💬 WhatsApp Bot**: Patients message via WhatsApp; AI triages symptoms and detects red flags.
- **📅 Auto-Scheduling**: When a red flag is detected, an emergency consult is booked on Google Calendar.
- **🖼️ Image Analysis**: Patients can send wound photos for AI analysis.

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Archivist     │     │     Sentry      │
│   (Streamlit)   │     │    (FastAPI)    │
│   PDF → JSON    │     │   WhatsApp Bot  │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────┐
│            Google Cloud Run             │
└─────────────────────────────────────────┘
         │                       │
         ▼                       ▼
┌───────────────┐  ┌──────────────────────┐
│   Firestore   │  │   Vertex AI (Gemini) │
│   (Database)  │  │   (AI Processing)    │
└───────────────┘  └──────────────────────┘
```

---

## 📋 Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Twilio Account** with WhatsApp Sandbox
3. **Python 3.11+** (for local development)
4. **Google Cloud SDK** (`gcloud` CLI installed)

---

## 🚀 Deployment Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/Mark-Joseph-42/Medi-Path.git
cd Medi-Path
```

### Step 2: Enable Google Cloud APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  firestore.googleapis.com \
  calendar-json.googleapis.com \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com
```

### Step 3: Create Firestore Database

```bash
gcloud firestore databases create --location=us-central1
```

### Step 4: Create Secrets in Secret Manager

```bash
# Replace with your actual values
echo -n "your-project-id" | gcloud secrets create FIRESTORE_PROJECT_ID --data-file=-
echo -n "your-calendar-id@group.calendar.google.com" | gcloud secrets create CALENDAR_ID --data-file=-
```

### Step 5: Grant Permissions to Cloud Run

```bash
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')

# Allow Cloud Run to access secrets
gcloud secrets add-iam-policy-binding FIRESTORE_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding CALENDAR_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Allow Cloud Run to use Vertex AI
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### Step 6: Share Calendar with Service Account

1. Copy this email: `{PROJECT_NUMBER}-compute@developer.gserviceaccount.com`
2. Go to [Google Calendar Settings](https://calendar.google.com/calendar/r/settings)
3. Select your calendar → Share with specific people → Add the email
4. Set permission to **"Make changes to events"**

### Step 7: Deploy Services

```bash
# Deploy Archivist (PDF Ingestor)
gcloud run deploy archivist \
  --source archivist \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets FIRESTORE_PROJECT_ID=FIRESTORE_PROJECT_ID:latest

# Deploy Sentry (WhatsApp Bot)
gcloud run deploy sentry \
  --source sentry \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets FIRESTORE_PROJECT_ID=FIRESTORE_PROJECT_ID:latest,CALENDAR_ID=CALENDAR_ID:latest
```

### Step 8: Configure Twilio Webhook

1. Go to [Twilio Console](https://console.twilio.com/) → Messaging → Try it out → Send a WhatsApp message
2. Join the sandbox by sending the provided code to the Twilio number
3. Set the webhook URL to:
   ```
   https://sentry-{PROJECT_NUMBER}.us-central1.run.app/webhook
   ```
   Method: **POST**

---

## 🧪 Testing

### Test the Archivist
1. Open the Archivist URL from Cloud Run
2. Upload a PDF discharge summary
3. Enter a WhatsApp phone number (e.g., `+14155552671`)
4. Click "Finalize and Activate Sentry"

### Test the Sentry
1. Send a WhatsApp message to the Twilio Sandbox number
2. Try sending: "What are my medications?"
3. Try triggering a red flag: "I have severe chest pain"

### View Live Logs
```bash
gcloud beta run services logs tail sentry --region us-central1
```

---

## 📁 Project Structure

```
Medi-Path/
├── archivist/
│   ├── app.py              # Streamlit web interface
│   ├── parser.py           # Gemini PDF extraction
│   ├── Dockerfile
│   └── requirements.txt
├── sentry/
│   ├── main.py             # FastAPI webhook handler
│   ├── triage.py           # Gemini AI triage logic
│   ├── concierge.py        # Google Calendar booking
│   ├── Dockerfile
│   └── requirements.txt
├── cloudbuild-archivist.yaml
├── cloudbuild-sentry.yaml
└── README.md
```

---

## 🔐 Security Notes

- All secrets are stored in **Google Secret Manager**
- Cloud Run uses **Workload Identity** (no key files)
- Firestore data is encrypted at rest
- All traffic is over HTTPS

For production healthcare deployments, additional HIPAA compliance steps are required.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| AI Model | Gemini 2.5 Flash (Vertex AI) |
| Backend (Bot) | FastAPI + Uvicorn |
| Frontend (Portal) | Streamlit |
| Database | Cloud Firestore |
| Messaging | Twilio WhatsApp API |
| Calendar | Google Calendar API |
| Hosting | Google Cloud Run |
| Secrets | Google Secret Manager |

---

## 📄 License

MIT License

---

## 👥 Contributors

- Mark Joseph
- Neha Benny
