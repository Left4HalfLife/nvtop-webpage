# Multi-stage build for nvtop-webpage
# Stage 1: Builder - install dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create venv and install Python deps
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime - minimal image
FROM python:3.11-slim AS runtime

# Create non-root user for least privilege
RUN groupadd --gid 1000 nvtop \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home nvtop

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

# Copy application files (excluding gitignored)
COPY --chown=nvtop:nvtop app.py config.py .gitignore ./
COPY --chown=nvtop:nvtop instance/ instance/

# Create log directory
RUN mkdir -p /app/logs && \
    chown -R nvtop:nvtop /app

# Switch to non-root user
USER nvtop

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/status')" || exit 1

CMD ["python", "app.py"]
