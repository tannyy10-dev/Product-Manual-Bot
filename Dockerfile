# Backend Dockerfile for FastAPI application
FROM python:3.12-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install UV for faster dependency installation
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies using UV
RUN uv pip install --system --no-cache -r <(poetry export -f requirements.txt --without-hashes 2>/dev/null || echo "") || \
    pip install --no-cache-dir fastapi uvicorn langchain langchain-google-genai asyncpg sqlalchemy psycopg2-binary pydantic pypdf2 pdfplumber python-multipart httpx sse-starlette tiktoken

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
