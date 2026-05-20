FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl gcc \
    && rm -rf /var/lib/apt/lists/*
RUN addgroup --system appuser && adduser --system --group appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chown -R appuser:appuser /app
USER appuser
