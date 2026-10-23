# ==============================================================================
# SMART ECO BIN — Backend Production Dockerfile (Google Cloud Run Ready)
# Multi-stage lightweight build with PyTorch CPU-only & non-root user
# ==============================================================================

FROM python:3.11-slim AS builder

WORKDIR /install

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Pre-install lightweight CPU-only PyTorch & TorchVision (avoids huge CUDA bloat)
RUN pip install --no-cache-dir --prefix=/install/deps \
    torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copy the backend requirements file from the repository-root build context.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --prefix=/install/deps -r requirements.txt

# ------------------------------------------------------------------------------
# Production Runtime Stage
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

WORKDIR /app

# Create unprivileged application user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy installed python dependencies from builder
COPY --from=builder /install/deps /usr/local

# Copy AI model weights and metadata
COPY ml/model/waste_model.pth /app/ml/model/waste_model.pth
COPY ml/model/waste_detector.pt* /app/ml/model/
COPY ml/metadata/model_metadata.json /app/ml/metadata/model_metadata.json

# Copy backend application source code
COPY backend/ /app/backend/

# Create data directory with write permissions for local emulation fallback
RUN mkdir -p /app/backend/data && chown -R appuser:appgroup /app

# Set working directory to backend package
WORKDIR /app/backend

# Switch to non-root user
USER appuser

# Environment configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    MODEL_PATH=/app/ml/model/waste_model.pth \
    DETECTOR_MODEL_PATH=/app/ml/model/waste_detector.pt \
    METADATA_PATH=/app/ml/metadata/model_metadata.json \
    PORT=8080 \
    ENVIRONMENT=production \
    ALLOW_DEV_AUTH=false \
    STORAGE_PROVIDER=local

# Cloud Run dynamic port binding
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request, os; urllib.request.urlopen('http://127.0.0.1:' + str(os.environ.get('PORT', 8080)) + '/health')" || exit 1

# Launch uvicorn listening on Cloud Run provided PORT.
# Note: For ML serverless workloads, 1 worker per container avoids duplicated in-memory
# PyTorch model allocations (~350-500MB RAM per worker). Cloud Run manages autoscaling
# across container instances horizontally.
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1
