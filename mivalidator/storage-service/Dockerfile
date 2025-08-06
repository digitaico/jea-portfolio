FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including procps for pgrep healthchecks
RUN apt-get update && apt-get install -y \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY storage-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared code
COPY shared /app/shared

# Add shared code to PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Copy source code
COPY storage-service/src /app/src

# Create uploads and archive directories
RUN mkdir -p /app/uploads /app/archive

# Run the application
CMD ["python", "src/main.py"]
