from django.core.management import BaseCommand, call_command
from django.contrib.auth import get_user_model
import os
import json

class Command(BaseCommand):
    help = 'Create accounts and athletes'

    def handle(self, *args, **options):
        User = get_user_model()
        fixture_path = os.path.join('core', 'fixtures', 'users.json')

        existing_usernames = set(User.objects.values_list('username', flat=True))

        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        new_users = [entry for entry in data if entry['fields']['username'] not in existing_usernames]

        if new_users:
            self.stdout.write(self.style.SUCCESS(f"Loading fixture ({len(new_users)} new user(s))..."))
            call_command('loaddata', fixture_path)
        else:
            self.stdout.write(self.style.WARNING("All users already exist — skipping load."))