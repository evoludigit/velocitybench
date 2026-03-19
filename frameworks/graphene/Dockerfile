FROM python:3.13-slim

# Set TMPDIR to use /data/tmp for builds to avoid /tmp filling up
ENV TMPDIR=/data/tmp
RUN mkdir -p /data/tmp

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY graphene/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and common module
COPY graphene/ .
COPY common/ /app/common

RUN useradd --system --no-create-home appuser

USER appuser

EXPOSE 8000

CMD ["python", "main.py"]
