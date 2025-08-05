FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including curl for healthchecks
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY status-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY status-service/src /app/src
COPY shared /app/shared

# Expose port
EXPOSE 8003

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"] 