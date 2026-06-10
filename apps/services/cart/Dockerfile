FROM python:3.12-slim
WORKDIR /app
COPY apps/services/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/api /monolith
COPY apps/services/shared ./shared
COPY apps/services/cart/main.py ./main.py
COPY apps/services/cart/catalog_patch.py ./cart/catalog_patch.py
COPY apps/services/cart/__init__.py ./cart/__init__.py
ENV PYTHONPATH=/monolith:/app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
