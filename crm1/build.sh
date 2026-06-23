#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Render build script
# Render runs this once before starting the web service.
# ---------------------------------------------------------------------------
set -o errexit   # exit immediately if any command fails

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate
