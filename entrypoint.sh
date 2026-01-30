#!/bin/sh
set -e  # Exit on any error

# Fail fast if SECRET_KEY not set
if [ -z "$DJANGO_SECRET_KEY" ]; then
  echo "ERROR: DJANGO_SECRET_KEY is not set"
  exit 1
fi

# Wait for the database to be ready
echo "Waiting for database at $DB_HOST..."
max_attempts=30
attempt=1
until python - <<END
import os, psycopg2
try:
    conn = psycopg2.connect(
        dbname=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT", 5432)
    )
    conn.close()
except Exception as e:
    raise e
END
do
  if [ $attempt -ge $max_attempts ]; then
    echo "Database still not available after $max_attempts attempts. Exiting."
    exit 1
  fi
  echo "Database not ready yet (attempt $attempt/$max_attempts)... retrying in 2s"
  attempt=$((attempt+1))
  sleep 2
done

echo "Database is up!"

# Apply migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Safe superuser creation
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "Checking if superuser exists..."
  python manage.py shell <<END
from django.contrib.auth import get_user_model
User = get_user_model()
email = "$DJANGO_SUPERUSER_EMAIL"
if not User.objects.filter(email=email).exists():
    print("Creating superuser", email)
    User.objects.create_superuser(email=email, password="$DJANGO_SUPERUSER_PASSWORD")
else:
    print("Superuser", email, "already exists")
END
else
  echo "Superuser environment variables not fully set, skipping superuser creation"
fi

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn Electronic_exam.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
