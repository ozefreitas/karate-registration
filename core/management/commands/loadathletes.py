from django.core.management import BaseCommand, call_command
from registration.models import Member
import os
import json

class Command(BaseCommand):
    help = 'Create accounts and athletes'

    def handle(self, *args, **options):
        fixture_path = os.path.join('core', 'fixtures', 'converted_athletes.json')

        if not Member.objects.exists():
            self.stdout.write(self.style.SUCCESS("Loading athletes fixture..."))
            call_command('loaddata', fixture_path)
        else:
            self.stdout.write(self.style.WARNING("Athletes already exist — skipping load."))