#!/bin/sh
set -e

# --- Load environment variables from .env ---
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# --- Set Cloud Run PORT ---
export PORT="${PORT:-8080}"

# --- Start Gunicorn immediately ---
exec gunicorn Electronic_exam.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 0
