FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

COPY backend /app/backend
COPY storage /app/storage

ENV PYTHONPATH=/app/backend/src
EXPOSE 8000

CMD ["uvicorn", "recursive_osint.main:app", "--host", "0.0.0.0", "--port", "8000"]
