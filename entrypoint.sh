#!/bin/sh
set -e

# === CONFIGURATION ===
MAX_ATTEMPTS=30
SLEEP_TIME=3
PORT="${PORT:-8080}"  # Cloud Run sets this automatically

# Optional flags (DO NOT enable on Cloud Run service)
# RUN_MIGRATIONS=true
# CREATE_SUPERUSER=true
# DJANGO_SUPERUSER_USERNAME
# DJANGO_SUPERUSER_EMAIL
# DJANGO_SUPERUSER_PASSWORD

# === WAIT FOR DATABASE ===
wait_for_db() {
  echo "Waiting for database..."
  attempts=0
  until python - <<'END'
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

# === MAIN ===
wait_for_db

# === MIGRATIONS (EXPLICIT OPT-IN ONLY) ===
if [ "$RUN_MIGRATIONS" = "true" ]; then
  echo "RUN_MIGRATIONS=true → running migrations"
  python manage.py migrate --noinput
else
  echo "RUN_MIGRATIONS not enabled → skipping migrations"
fi

# === COLLECT STATIC FILES ===
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# === SUPERUSER (EXPLICIT OPT-IN ONLY) ===
if [ "$CREATE_SUPERUSER" = "true" ] && \
   [ -n "$DJANGO_SUPERUSER_USERNAME" ] && \
   [ -n "$DJANGO_SUPERUSER_EMAIL" ] && \
   [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then

  echo "Ensuring superuser exists..."
  python manage.py shell <<'END'
from django.contrib.auth import get_user_model
User = get_user_model()
email = "$DJANGO_SUPERUSER_EMAIL"
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email,
        password="$DJANGO_SUPERUSER_PASSWORD"
    )
    print("Superuser created")
else:
    print("Superuser already exists")
END
else
  echo "Superuser creation skipped"
fi

# === START SERVER ===
echo "Starting Gunicorn..."
exec gunicorn Electronic_exam.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 3 \
  --timeout 120
