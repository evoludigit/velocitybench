FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY asgi-graphql/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and common module
COPY asgi-graphql/ .
COPY common/ /app/common

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4000/health')" || exit 1

RUN useradd --system --no-create-home appuser

USER appuser

EXPOSE 4000

CMD ["python", "app.py"]
