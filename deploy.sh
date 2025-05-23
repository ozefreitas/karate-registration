#!/bin/bash

# stop the script if an error occurs
set -e

# Pull changes
echo "Pulling the latest changes from the main branch..."
git pull origin main

# Activate venv
echo "Activating the virtual environment..."
source /home/karatescorappregistration/.virtualenvs/venv/bin/activate

# Migrate
echo "Applying database migrations..."
python manage.py migrate

# Remove previous static
echo "Removing previous static_root folder"
rm -r /home/karatescorappregistration/karate-registration/static_root/

# make sure settings DBEUG is set to False

# Collect static
echo "Collecting static files..."
python manage.py collectstatic

# Populate with competitions
python manage.py populate_comps

# Reload server
echo "Restarting the server..."
touch /var/www/karatescorappregistration_pythonanywhere_com_wsgi.py

echo "Deployment complete!"