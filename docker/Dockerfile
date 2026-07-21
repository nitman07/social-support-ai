FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir fastapi uvicorn sqlalchemy asyncpg motor qdrant-client neo4j \
        langgraph langchain langchain-community langchain-ollama \
        scikit-learn pandas numpy joblib shap \
        pypdf pytesseract pdf2image pillow python-docx openpyxl \
        langfuse streamlit \
        pydantic pydantic-settings python-dotenv faker httpx tenacity loguru injector \
        celery redis pyjwt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8000 8501
