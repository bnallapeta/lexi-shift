# Build stage for dependencies
FROM --platform=$BUILDPLATFORM python:3.11-slim as deps

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    git \
    cmake \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip --version \
    && gcc --version

# Create and activate virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies in layers for better caching
COPY requirements.txt /tmp/requirements.txt

# Install CPU-only PyTorch first (faster to build)
RUN pip3 install --no-cache-dir torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu

# Install core dependencies
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Runtime stage
FROM python:3.11-slim as runtime

# Copy virtual environment from deps stage
COPY --from=deps /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /tmp/nllb_models && \
    chown -R appuser:appuser /app /tmp/nllb_models

# Copy application code
COPY --chown=appuser:appuser . /app/

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    MODEL_DOWNLOAD_ROOT=/tmp/nllb_models \
    LOG_LEVEL=INFO

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"] 