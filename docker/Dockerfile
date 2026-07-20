FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY README.md .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e ".[dev]" || pip install --no-cache-dir fastapi uvicorn sqlalchemy asyncpg motor qdrant-client neo4j langgraph scikit-learn pandas numpy streamlit loguru pydantic pydantic-settings python-dotenv faker httpx tenacity

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8000 8501
