# Base image
FROM python:3.11-slim

# Python environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
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

# Expose Cloud Run port
EXPOSE 8080

# Run Gunicorn at runtime
CMD ["gunicorn", "Electronic_exam.wsgi:application", "--bind", "0.0.0.0:8080"]
