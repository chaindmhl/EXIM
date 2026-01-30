# Use lightweight Python image
FROM python:3.11-slim

# Environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# -----------------------------
# TEMP SECRET_KEY for build
# -----------------------------
# This ensures Django can load apps like auth during collectstatic
ENV DJANGO_SECRET_KEY="temporary_build_key_for_build"

# Collect static files
RUN python manage.py collectstatic --noinput

# Cloud Run listens on 8080
EXPOSE 8080

# -----------------------------
# Runtime: Cloud Run injects real SECRET_KEY
# -----------------------------
CMD ["gunicorn", "Electronic_exam.wsgi:application", "--bind", "0.0.0.0:8080"]
