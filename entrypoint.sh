#!/bin/sh
set -e

# =========================
# CONFIGURATION
# =========================
MAX_ATTEMPTS=30
SLEEP_TIME=3
PORT="${PORT:-8080}"  # Cloud Run sets this automatically

# Optional flags
RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"
CREATE_SUPERUSER="${CREATE_SUPERUSER:-false}"  # set true via env if needed

# =========================
# WAIT FOR DATABASE
# =========================
wait_for_db() {
  echo "Waiting for database..."
  attempts=0
  until python - <<END
import sys
from django.db import connections
try:
    connections['default'].ensure_connection()
except Exception as e:
    print("Database connection failed:", e)
    sys.exit(1)
END
  do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge "$MAX_ATTEMPTS" ]; then
      echo "Database not ready after $MAX_ATTEMPTS attempts"
      exit 1
    fi
    echo "Database not ready yet, retrying in $SLEEP_TIME seconds..."
    sleep "$SLEEP_TIME"
  done
  echo "Database is ready."
}

wait_for_db

# =========================
# RUN MIGRATIONS
# =========================
if [ "$RUN_MIGRATIONS" = "true" ]; then
  echo "RUN_MIGRATIONS=true → running migrations"
  python manage.py migrate --noinput
else
  echo "Skipping migrations"
fi

# =========================
# COLLECT STATIC FILES
# =========================
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# =========================
# CREATE SUPERUSER
# =========================
if [ "$CREATE_SUPERUSER" = "true" ] && \
   [ -n "$DJANGO_SUPERUSER_USERNAME" ] && \
   [ -n "$DJANGO_SUPERUSER_EMAIL" ] && \
   [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then

  echo "Ensuring superuser exists..."
  python manage.py shell <<END
from django.contrib.auth import get_user_model
import os
User = get_user_model()
email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print("Superuser created")
else:
    print("Superuser already exists")
END

else
  echo "Superuser creation skipped"
fi

# =========================
# START GUNICORN
# =========================
echo "Starting Gunicorn..."
exec gunicorn Electronic_exam.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 3 \
  --timeout 300
