#!/bin/sh
set -e

# Fail fast if SECRET_KEY not set
if [ -z "$DJANGO_SECRET_KEY" ]; then
  echo "ERROR: DJANGO_SECRET_KEY is not set"
  exit 1
fi

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Safe superuser creation for CustomUser (email-based)
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

echo "Starting Gunicorn..."
exec gunicorn Electronic_exam.wsgi:application --bind 0.0.0.0:8080
