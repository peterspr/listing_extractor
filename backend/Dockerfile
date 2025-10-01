# Backend Dockerfile
FROM python:3.11-slim

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y \
    default-jre \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt .
COPY requirements.txt ./requirements-cli.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-cli.txt

# Copy application code
COPY backend/ ./backend/
COPY src/ ./src/
COPY config.yaml .

# Create temp directories
RUN mkdir -p /tmp/uploads /tmp/results

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=backend/app.py

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "300", "backend.app:create_app()"]
