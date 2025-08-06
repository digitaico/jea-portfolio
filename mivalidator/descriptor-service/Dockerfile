FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including procps for pgrep healthchecks
RUN apt-get update && apt-get install -y \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY descriptor-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY descriptor-service/src /app/src
COPY shared /app/shared

# Add shared code to PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Create directories
RUN mkdir -p /app/uploads /app/archive

# Run the application
CMD ["python", "src/main.py"] 