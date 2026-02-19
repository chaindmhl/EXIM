#!/bin/sh
set -e

PORT="${PORT:-8080}"

echo "Starting Django on port $PORT"

if [ "$RUN_MIGRATIONS" = "true" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

exec gunicorn Electronic_exam.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --threads 4 \
  --timeout 300
