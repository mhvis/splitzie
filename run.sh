#!/usr/bin/env bash
set -e

# This script needs to be executed in the directory with the source files.
#
# It will put a virtual environment and some log files in the current
# directory.
#
# Set application configuration using the environment variables, before
# executing the script.

port="65463"

echo "Creating virtual environment"
python -m venv venv
./venv/bin/pip install -U pip
./venv/bin/pip install -r requirements/common.txt -r requirements/prod.txt

echo "Stop server if running"
pkill -F pid || true

echo "Collect static files"
./venv/bin/python manage.py collectstatic --noinput

echo "Apply migrations"
./venv/bin/python manage.py migrate --noinput

echo "Start server"
./venv/bin/gunicorn \
  --workers 2 \
  --bind 0.0.0.0:$port \
  --daemon \
  --log-file log \
  --pid pid \
  splitzie.wsgi
