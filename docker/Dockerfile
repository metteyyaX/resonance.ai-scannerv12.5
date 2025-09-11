# Docker configuration for Resonance.ai Scanner v13
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Create data directories
RUN mkdir -p /app/data/universe/coinbase \
    /app/data/detections \
    /app/data/db

# Set environment variables (can be overridden)
ENV PYTHONUNBUFFERED=1

# Default command - can be overridden in docker-compose
CMD ["python", "resonance_scannerv13_3_ws.py"]
