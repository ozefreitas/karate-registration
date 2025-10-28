#!/usr/bin/env bash
# Exit on error
set -o errexit

# Modify this line as needed for your package manager (pip, poetry, etc.)
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate

# Create superuser with env variables from render
python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); \
import os; \
if not User.objects.filter(is_superuser=True).exists(): \
    User.objects.create_superuser(os.environ['DJANGO_SUPERUSER_USERNAME'], os.environ['DJANGO_SUPERUSER_EMAIL'], os.environ['DJANGO_SUPERUSER_PASSWORD']); \
else: \
    print('Superuser already exists, skipping creation.')"
