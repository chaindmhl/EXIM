# Base image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcairo2 libcairo-gobject2 libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 libffi-dev libharfbuzz0b libfribidi0 \
    libjpeg62-turbo libopenjp2-7 shared-mime-info \
    fonts-dejavu-core fonts-liberation fonts-freefont-ttf \
    libglib2.0-0 libgl1 curl git && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn python-dotenv

# Copy project code
COPY . .

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port for Cloud Run
EXPOSE 8080

# Use entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
