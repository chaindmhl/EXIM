#!/bin/sh
set -e

# Fail fast if SECRET_KEY not set
if [ -z "$DJANGO_SECRET_KEY" ]; then
  echo "ERROR: DJANGO_SECRET_KEY is not set"
  exit 1
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser if it doesn't exist..."
python manage.py shell -c "from django.contrib.auth import get_user_model; import os; \
User = get_user_model(); \
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin'); \
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'); \
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'adminpass'); \
User.objects.filter(username=username).exists() or User.objects.create_superuser(username, email, password)"

echo "Starting Gunicorn..."
exec gunicorn Electronic_exam.wsgi:application --bind 0.0.0.0:8080
