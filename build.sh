#!/usr/bin/env bash
# Render build script for GUCAIR.
set -o errexit
set -o pipefail

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Waiting for the Neon PostgreSQL database..."
python manage.py wait_for_db

echo "Applying database migrations..."
python manage.py migrate --noinput

if [ "${SEED_DEMO:-False}" = "True" ]; then
  echo "Seeding questions, resources and clearly-labelled demo institutions..."
  python manage.py seed_data --demo
else
  echo "Seeding questions and resources..."
  python manage.py seed_data
fi

echo "Bootstrapping the administrator account (skips when variables are unset)..."
python manage.py create_admin

echo "Build completed successfully."
