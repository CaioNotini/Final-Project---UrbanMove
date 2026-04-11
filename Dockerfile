FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/logs
ENV LOG_DIR=/app/logs

EXPOSE 8000

CMD ["uvicorn", "src.api.main_api:app", "--host", "0.0.0.0", "--port", "8000"]