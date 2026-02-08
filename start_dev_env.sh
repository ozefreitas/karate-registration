#!/bin/bash
# prepare the local db
python manage.py collectstatic --no-input
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser --no-input
python manage.py spectacular --file ./openapi/schema.json --format openapi-json

# run server
python manage.py runserver 0.0.0.0:8000