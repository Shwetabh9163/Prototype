# =============================================================
# Traffic Management Backend — Dockerfile
# =============================================================
# This Dockerfile creates a lightweight Python container running
# a FastAPI server via Uvicorn. Three identical copies of this
# container run simultaneously, each with a different SERVER_ID.
#
# Build context: ./backend/
# =============================================================

# Use Python 3.11 slim image — smaller than full image (~150MB vs ~900MB)
FROM python:3.11-slim

# Set a label for identification
LABEL maintainer="traffic-management" \
      description="FastAPI Backend Server"

# Prevent Python from writing .pyc files and enable unbuffered output
# (so we see logs immediately in Docker)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy requirements first (Docker layer caching optimization)
# If requirements.txt hasn't changed, Docker reuses the cached layer
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose port 8000 (Uvicorn default)
EXPOSE 8000

# Run the FastAPI app using Uvicorn
# --host 0.0.0.0 makes it accessible from outside the container
# --port 8000 is the default Uvicorn port
# --workers 1 is fine for a prototype (each container = 1 server)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
