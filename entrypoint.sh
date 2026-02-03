#!/bin/sh
set -e

PORT="${PORT:-8080}"

echo "Starting Django on port $PORT"

# Optional: run migrations (safe)
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput
else
  echo "Skipping migrations"
fi

# Collect static files (never fail startup)
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Start Gunicorn (THIS is what Cloud Run waits for)
exec gunicorn Electronic_exam.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --threads 4 \
  --timeout 300
