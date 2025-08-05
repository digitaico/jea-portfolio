FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including procps for pgrep healthchecks
RUN apt-get update && apt-get install -y \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY validator-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared code
COPY shared /app/shared

# Add shared code to PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Copy source code
COPY validator-service/src /app/src

# Create uploads directory
RUN mkdir -p /app/uploads

# Run the application
CMD ["python", "src/main.py"] 