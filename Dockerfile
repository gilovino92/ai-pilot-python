# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app/

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    # Remove conflicting packages from requirements.txt
    sed -i '/pyasn1/d' requirements.txt && \
    sed -i '/pyasn1-modules/d' requirements.txt && \
    sed -i '/python-jose/d' requirements.txt && \
    # Install main requirements
    pip install --no-cache-dir -r requirements.txt && \
    # Install conflicting packages with compatible versions
    pip install --no-cache-dir pyasn1==0.4.8 pyasn1-modules==0.2.8 python-jose==3.4.0

# Copy application code
COPY ./app /app/app
COPY ./main.py /app/
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/

# Final stage
FROM python:3.12-slim

WORKDIR /app/

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages and application
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /app /app

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 