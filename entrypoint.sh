#!/bin/sh
set -e

# -------------------------
# DJANGO ENV
# -------------------------
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-Electronic_exam.settings}
export PYTHONUNBUFFERED=1

PORT="${PORT:-8080}"

echo "Starting Django on port $PORT"

# -------------------------
# WAIT FOR DB
# -------------------------
MAX_ATTEMPTS=30
SLEEP_TIME=3

echo "Waiting for database..."
attempts=0
until python - <<END
import sys, os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE"))
django.setup()
from django.db import connections
try:
    connections['default'].ensure_connection()
except Exception as e:
    print("Database not ready:", e)
    sys.exit(1)
END
do
  attempts=$((attempts + 1))
  if [ "$attempts" -ge "$MAX_ATTEMPTS" ]; then
    echo "Database not ready after $MAX_ATTEMPTS attempts, exiting"
    exit 1
  fi
  echo "Database not ready, retrying in $SLEEP_TIME seconds..."
  sleep "$SLEEP_TIME"
done
echo "Database ready."

# -------------------------
# MIGRATIONS (optional)
# -------------------------
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput
else
  echo "Skipping migrations"
fi

# -------------------------
# STATIC FILES
# -------------------------
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# -------------------------
# START GUNICORN
# -------------------------
echo "Starting Gunicorn..."
exec gunicorn Electronic_exam.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --threads 4 \
  --timeout 300
