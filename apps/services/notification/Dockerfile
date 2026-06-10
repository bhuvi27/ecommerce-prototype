FROM python:3.12-slim
WORKDIR /app
COPY apps/services/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/api /monolith
COPY apps/services/shared ./shared
COPY apps/services/notification/worker.py ./worker.py
ENV PYTHONPATH=/monolith:/app
CMD ["python", "worker.py"]
