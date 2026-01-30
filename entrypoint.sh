#!/bin/sh
set -e

# Optional: wait for database
echo "Waiting for database..."
attempts=0
until python manage.py check >/dev/null 2>&1; do
  attempts=$((attempts+1))
  if [ $attempts -ge 30 ]; then
    echo "Database not ready after 30 attempts, exiting."
    exit 1
  fi
  echo "Database not ready yet, retrying in 3 seconds..."
  sleep 3
done

echo "Database is ready, continuing..."

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run your separate superuser creation script
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "Checking/creating superuser via create_superuser.py..."
  python create_superuser.py
fi

echo "Starting Gunicorn..."
exec gunicorn Electronic_exam.wsgi:application --bind 0.0.0.0:$PORT --workers 3
