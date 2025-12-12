# =============================================================================
# DepShield - Dependency Vulnerability Scanner
# =============================================================================
# Multi-stage Docker build for optimized production image
#
# Build: docker build -t depshield .
# Run:   docker run -p 5000:5000 depshield
#
# Author: Elif Sude ATES
# GitHub: https://github.com/elifsudeates/depshield
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# -----------------------------------------------------------------------------
# Stage 2: Production
# -----------------------------------------------------------------------------
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd --gid 1000 depshield && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home depshield

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=depshield:depshield . .

# Switch to non-root user
USER depshield

# Expose the Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/', timeout=5)" || exit 1

# Set labels for container metadata
LABEL maintainer="Elif Sude ATES <github.com/elifsudeates>" \
      version="1.0.0" \
      description="DepShield - Dependency Vulnerability Scanner" \
      org.opencontainers.image.source="https://github.com/elifsudeates/depshield"

# Run the application with Gunicorn for production
# Use --worker-class=gthread for SSE support
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--worker-class", "gthread", "--timeout", "120", "app:app"]
