#!/bin/sh
set -e

# Ensure SECRET_KEY is set
if [ -z "$DJANGO_SECRET_KEY" ]; then
  echo "ERROR: DJANGO_SECRET_KEY is not set"
  exit 1
fi

# Apply migrations safely (will retry DB connection)
echo "Applying migrations..."
python manage.py migrate --noinput || echo "Warning: migrations failed, continuing..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Warning: collectstatic failed, continuing..."

# Start Gunicorn immediately
echo "Starting Gunicorn on port $PORT..."
exec gunicorn Electronic_exam.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --timeout 120
