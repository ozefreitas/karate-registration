from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Create a superuser if none exists (idempotent)'

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.NOTICE('Superuser exists — skipping.'))
            return
        User.objects.create_superuser(
            os.environ.get('DJANGO_SUPERUSER_USERNAME'),
            os.environ.get('DJANGO_SUPERUSER_EMAIL'),
            os.environ.get('DJANGO_SUPERUSER_PASSWORD'),
        )
        self.stdout.write(self.style.SUCCESS('Superuser created.'))
