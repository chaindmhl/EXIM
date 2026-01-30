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

# Safe superuser creation
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "Checking if superuser exists..."
  python - <<END
from django.contrib.auth import get_user_model
User = get_user_model()
username = "$DJANGO_SUPERUSER_USERNAME"
email = "$DJANGO_SUPERUSER_EMAIL"
password = "$DJANGO_SUPERUSER_PASSWORD"
if not User.objects.filter(email=email).exists():
    print("Creating superuser", username)
    User.objects.create_superuser(email=email, password=password)
else:
    print("Superuser", username, "already exists")
END
fi

echo "Starting Gunicorn..."
# Replace the shell with Gunicorn
exec gunicorn Electronic_exam.wsgi:application --bind 0.0.0.0:$PORT --workers 3
