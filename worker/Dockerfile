FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY config.py queue_client.py db.py models.py handlers.py worker.py ./
EXPOSE 0
CMD ["python", "worker.py"]
