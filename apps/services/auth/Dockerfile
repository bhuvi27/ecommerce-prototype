FROM python:3.12-slim
WORKDIR /app
COPY apps/services/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/api /monolith
COPY apps/services/shared ./shared
COPY apps/services/auth/main.py ./main.py
ENV PYTHONPATH=/monolith:/app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
