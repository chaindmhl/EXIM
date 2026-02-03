#!/bin/sh
set -e

# =========================
# DJANGO ENV
# =========================
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-Electronic_exam.settings}
export PYTHONUNBUFFERED=1

PORT="${PORT:-8080}"

echo "Starting Django on port $PORT"

# =========================
# MIGRATIONS (OPTIONAL)
# =========================
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput
else
  echo "Skipping migrations"
fi

# =========================
# STATIC FILES
# =========================
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# =========================
# START SERVER
# =========================
exec gunicorn Electronic_exam.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --threads 4 \
  --timeout 300
