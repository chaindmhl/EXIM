#!/bin/sh
set -e

# === CONFIGURATION ===
MAX_ATTEMPTS=30
SLEEP_TIME=3
PORT="${PORT:-8080}"  # Cloud Run sets $PORT automatically

# Optional: environment variables for superuser
# DJANGO_SUPERUSER_USERNAME
# DJANGO_SUPERUSER_EMAIL
# DJANGO_SUPERUSER_PASSWORD

# === FUNCTION TO WAIT FOR DATABASE ===
wait_for_db() {
  echo "Waiting for database..."
  attempts=0
  until python - <<END
import sys
import psycopg2
from django.conf import settings
try:
    from django.db import connections
    conn = connections['default']
    conn.ensure_connection()
except Exception as e:
    print("Database connection failed:", e)
    sys.exit(1)
END
  do
    attempts=$((attempts+1))
    if [ $attempts -ge $MAX_ATTEMPTS ]; then
      echo "Database not ready after $MAX_ATTEMPTS attempts, exiting."
      exit 1
    fi
    echo "Database not ready yet, retrying in $SLEEP_TIME seconds..."
    sleep $SLEEP_TIME
  done
  echo "Database is ready."
}

# === MAIN SCRIPT ===
wait_for_db

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# === SAFE SUPERUSER CREATION ===
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "Checking/creating superuser..."
  python manage.py shell <<END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email="$DJANGO_SUPERUSER_EMAIL").exists():
    print("Creating superuser: $DJANGO_SUPERUSER_USERNAME")
    User.objects.create_superuser(
        email="$DJANGO_SUPERUSER_EMAIL",
        password="$DJANGO_SUPERUSER_PASSWORD"
    )
else:
    print("Superuser already exists: $DJANGO_SUPERUSER_USERNAME")
END
fi

echo "Starting Gunicorn..."
exec gunicorn Electronic_exam.wsgi:application --bind 0.0.0.0:$PORT --workers 3
