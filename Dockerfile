# Multi-stage build for MOH MNCAH Dashboard
# Stage 1: Build dependencies
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    FLASK_DEBUG=False \
    PATH="/opt/venv/bin:$PATH"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    libssl3 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create application user for security
RUN groupadd -r moh && useradd -r -g moh -s /bin/bash moh

# Set working directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/uploads \
    /app/exports \
    /app/logs \
    /app/instance \
    && chown -R moh:moh /app

# Copy application files
COPY --chown=moh:moh . .

# Create .env file for production defaults
RUN echo "FLASK_ENV=production" > .env && \
    echo "FLASK_DEBUG=False" >> .env && \
    echo "SECRET_KEY=change_this_in_production" >> .env && \
    chown moh:moh .env

# Install application in development mode
USER moh
RUN pip install -e .

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Expose port
EXPOSE 5000

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "run:app"]

# Alternative commands for development
# CMD ["python", "run.py"]
# CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

# Labels for container metadata
LABEL maintainer="Ministry of Health Uganda <info@health.go.ug>" \
      version="1.0.0" \
      description="MOH MNCAH Dashboard - Maternal, Neonatal, Child and Adolescent Health Analytics" \
      org.opencontainers.image.title="MOH MNCAH Dashboard" \
      org.opencontainers.image.description="Flask application for analyzing MNCAH health indicators in Uganda" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Ministry of Health Uganda" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/moh-uganda/mncah-dashboard"
