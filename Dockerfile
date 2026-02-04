# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Copy ALL frontend files first to ensure fresh build
COPY frontend/ ./

# Debug: list hooks and types directories
RUN echo "=== Contents of src/hooks ===" && ls -la src/hooks/ && \
    echo "=== Contents of src/types ===" && ls -la src/types/

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

# Debug: verify file structure
RUN echo "=== Backend structure ===" && ls -la && ls -la app/

# Expose port (Railway may override via PORT env var)
EXPOSE 8003

# Use shell form to allow PORT env var substitution
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8003}

