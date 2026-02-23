FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY ariadne/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and common module
COPY ariadne/ .
COPY common/ /app/common

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4000/health')" || exit 1

EXPOSE 4000

CMD ["python", "app.py"]
