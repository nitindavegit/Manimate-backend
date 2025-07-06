# ✅ Optimized Dockerfile for Manimate App (FastAPI + Manim)
FROM python:3.10-slim

# Prevent prompts from tzdata, etc.
ENV DEBIAN_FRONTEND=noninteractive

# Install system-level dependencies
RUN  apt-get update && apt-get install -y \
    ffmpeg \
    libcairo2-dev \
    libpango1.0-dev \
    texlive-full \
    build-essential \
    pkg-config \
    # Clean up apt cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Expose port (default FastAPI port)
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
