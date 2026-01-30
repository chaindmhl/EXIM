#!/bin/sh

# Fail fast if SECRET_KEY is not set
if [ -z "$DJANGO_SECRET_KEY" ]; then
  echo "ERROR: DJANGO_SECRET_KEY is not set"
  exit 1
fi

# Set Django environment variables for runtime
export DJANGO_SECRET_KEY
export DEBUG=${DEBUG:-False}
export ALLOWED_HOSTS=${ALLOWED_HOSTS:-localhost}

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn Electronic_exam.wsgi:application --bind 0.0.0.0:8080
