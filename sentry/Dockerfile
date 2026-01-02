FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# Twilio webhooks expect an industry standard 80 port or assigned Cloud Run port
CMD uvicorn main:app --host 0.0.0.0 --port 8080
