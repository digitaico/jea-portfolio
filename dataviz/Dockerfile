# report/Dockerfile
FROM public.ecr.aws/docker/library/python:3.12-slim

ENV PYTHONBUFFERED=1 PYTHONDONTWRITEBYRECODE=1 PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["streamlit", "run", "app/main.py"]



