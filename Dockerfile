# Build stage for development tools
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install development dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libffi-dev \
    libnacl-dev \
    libopus0 \
    opus-tools \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -r -s /bin/bash botuser && \
    chown -R botuser:botuser /app

# Copy requirements and install production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs && \
    chown -R botuser:botuser /app/data /app/logs

# Make scripts executable
RUN chmod +x start.sh run.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app:${PATH}"

# Switch to non-root user
USER botuser

# Create volume mount points
VOLUME ["/app/data", "/app/logs"]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Command to run the bot
CMD ["./start.sh"]
