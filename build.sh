#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# Install required Python packages
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files for WhiteNoise
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate

# Safely initialize Branch Head and Faculty accounts if database is fresh
python manage.py init_render_data
