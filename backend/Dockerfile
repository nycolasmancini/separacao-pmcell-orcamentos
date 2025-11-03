# Dockerfile for Railway deployment
# Uses Python 3.11 with PostgreSQL client libraries
# Updated: 2025-11-03 - PORT variable fix applied

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Create necessary directories
RUN mkdir -p staticfiles

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Expose port (Railway will set $PORT env var)
EXPOSE 8000

# Start command (will use $PORT from Railway)
CMD daphne -b 0.0.0.0 -p ${PORT:-8000} separacao_pmcell.asgi:application
