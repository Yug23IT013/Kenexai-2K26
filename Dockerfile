# Multi-stage Dockerfile for Football Analytics Platform
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
COPY streamlit_app/backend/requirements.txt ./backend_requirements.txt

# Create requirements combined file
RUN cat requirements.txt backend_requirements.txt > combined_requirements.txt && \
    sort combined_requirements.txt | uniq > final_requirements.txt

# ─────────────────────────────────────────────────────────────────
# Production Stage
# ─────────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /app/final_requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r final_requirements.txt

# Copy application code
COPY . .

# Create directories for caching
RUN mkdir -p /app/.cache /app/.streamlit

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_LOGGER_LEVEL=warning

# Expose ports
EXPOSE 8501 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8501/_stcore/health')" || exit 1

# Run the application using a startup script
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
