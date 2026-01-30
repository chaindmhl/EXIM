#!/bin/sh
set -e

# ----------------------------
# 1️⃣ Fail fast if SECRET_KEY not set
# ----------------------------
if [ -z "$DJANGO_SECRET_KEY" ]; then
  echo "ERROR: DJANGO_SECRET_KEY is not set"
  exit 1
fi

# ----------------------------
# 2️⃣ Wait for Postgres to be ready
# ----------------------------
# Replace $DB_HOST, $DB_PORT, $DB_USER, $DB_NAME with your Cloud Run env vars
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-postgres}"
MAX_RETRIES=20
COUNT=0

echo "Waiting for database at $DB_HOST:$DB_PORT..."

until PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c '\q' 2>/dev/null; do
  COUNT=$((COUNT+1))
  if [ $COUNT -ge $MAX_RETRIES ]; then
    echo "Database not ready after $MAX_RETRIES attempts, exiting."
    exit 1
  fi
  echo "Database not ready yet, retrying in 3 seconds..."
  sleep 3
done

echo "Database is ready!"

# ----------------------------
# 3️⃣ Apply migrations & collect static files
# ----------------------------
echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# ----------------------------
# 4️⃣ Safe superuser creation
# ----------------------------
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

# ----------------------------
# 5️⃣ Start Gunicorn
# ----------------------------
echo "Starting Gunicorn..."
exec gunicorn Electronic_exam.wsgi:application --bind 0.0.0.0:8080
