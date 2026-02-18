# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Copy ALL frontend files first to ensure fresh build
COPY frontend/ ./

# Install dependencies and build
RUN npm ci && npm run build

# Stage 2: Python backend with built frontend
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for pymupdf and pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmupdf-dev \
    libfreetype6 \
    libjpeg62-turbo \
    libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set working directory to backend for uvicorn
WORKDIR /app/backend

# Expose default port (Railway overrides via PORT env var)
EXPOSE 8003

# Use gunicorn with uvicorn workers for production:
# --max-requests 50: recycle worker after 50 requests to reclaim leaked memory
# --max-requests-jitter 10: stagger restarts to avoid simultaneous recycling
CMD gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 1 \
    --bind 0.0.0.0:${PORT:-8003} \
    --max-requests 50 \
    --max-requests-jitter 10 \
    --timeout 600 \
    --graceful-timeout 30

