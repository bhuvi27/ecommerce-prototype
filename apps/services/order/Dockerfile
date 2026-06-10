FROM python:3.12-slim
WORKDIR /app
COPY apps/services/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/api /monolith
COPY apps/services/shared ./shared
COPY apps/services/order/main.py ./main.py
COPY apps/services/order/routes_micro.py ./order/routes_micro.py
COPY apps/services/order/__init__.py ./order/__init__.py
ENV PYTHONPATH=/monolith:/app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
