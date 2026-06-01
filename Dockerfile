# Dockerfile for the Flask API
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY api ./api
COPY data ./data

ENV PORT=8080
ENV GAMEMATCH_DATA_PATH=/app/data/processed/games_features.csv

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "api.app:app"]
