FROM python:3.13

# Create and set TMPDIR to use /data/tmp for builds to avoid /tmp filling up
RUN mkdir -p /data/tmp
ENV TMPDIR=/data/tmp

WORKDIR /app

# Install system dependencies for psycopg and Rust compilation
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 4000

CMD ["python", "main.py"]