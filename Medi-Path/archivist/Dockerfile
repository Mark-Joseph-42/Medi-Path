FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run expects the port to be 8080 by default, 
# but Streamlit defaults to 8501. 
# We'll map it to 8080 or use PORT env var.
EXPOSE 8080

CMD streamlit run app.py --server.port $PORT --server.address 0.0.0.0
