#!/bin/sh
# Fail fast if SECRET_KEY is not set
if [ -z "$DJANGO_SECRET_KEY" ]; then
  echo "ERROR: DJANGO_SECRET_KEY is not set"
  exit 1
fi

# Collect static files at runtime (with runtime env vars)
python manage.py collectstatic --noinput

# Start Gunicorn
exec gunicorn Electronic_exam.wsgi:application --bind 0.0.0.0:8080

