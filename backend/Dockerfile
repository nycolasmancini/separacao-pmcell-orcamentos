# Dockerfile for Railway deployment
# Uses Python 3.11 with PostgreSQL client libraries

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files (will be run again in Procfile, but good for build)
RUN python manage.py collectstatic --noinput || true

# Expose port (Railway will set $PORT env var)
EXPOSE 8000

# Command will be overridden by Procfile
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "separacao_pmcell.asgi:application"]
