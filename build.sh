#!/usr/bin/env bash
set -o errexit  # Exit on any command failure
set -o pipefail # Fail on pipe commands
set -o nounset  # Treat unset variables as error

echo "-----> Starting Django deployment build process..."

# Install system dependencies
echo "-----> Installing system dependencies"
apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from requirements.txt
echo "-----> Installing Python dependencies"
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
echo "-----> Collecting static files"
python manage.py collectstatic --noinput --clear

# Run database migrations
echo "-----> Applying database migrations"
python manage.py migrate --noinput

# Verify installation
echo "-----> Verifying installation"
python manage.py check --deploy

echo "-----> Build completed successfully"