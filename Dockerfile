# Base image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Build-time environment variables
ARG DJANGO_SECRET_KEY
ARG DEBUG
ARG ALLOWED_HOSTS
ARG OPENAI_API_KEY

# Set them as runtime env variables
ENV DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY
ENV DEBUG=$DEBUG
ENV ALLOWED_HOSTS=$ALLOWED_HOSTS
ENV OPENAI_API_KEY=$OPENAI_API_KEY

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8080

# Run entrypoint at container start
ENTRYPOINT ["/app/entrypoint.sh"]
