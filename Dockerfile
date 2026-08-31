FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ agent/
COPY main.py .
COPY docs/guidelines/ docs/guidelines/

ENTRYPOINT ["python", "main.py"]
