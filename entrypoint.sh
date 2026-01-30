#!/bin/sh
set -e

# Fail fast if SECRET_KEY not set
if [ -z "$DJANGO_SECRET_KEY" ]; then
  echo "ERROR: DJANGO_SECRET_KEY is not set"
  exit 1
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn Electronic_exam.wsgi:application --bind 0.0.0.0:8080
