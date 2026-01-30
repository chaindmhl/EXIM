#!/bin/sh
set -e

# Fail fast if SECRET_KEY is not set
if [ -z "$DJANGO_SECRET_KEY" ]; then
  echo "ERROR: DJANGO_SECRET_KEY is not set"
  exit 1
fi

# Optional: export runtime environment vars
export DJANGO_SECRET_KEY
export DEBUG=${DEBUG:-False}
export ALLOWED_HOSTS=${ALLOWED_HOSTS:-localhost}

# Make migrations (optional, can remove in production)
python manage.py makemigrations
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn Electronic_exam.wsgi:application --bind 0.0.0.0:8080 --workers 3
