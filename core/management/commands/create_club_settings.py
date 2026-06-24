from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from clubs.models import ClubSettings

User = get_user_model()

class Command(BaseCommand):
    help = "Creates settings for clubs."

    def handle(self, *args, **kwargs):
        for user in User.objects.exclude(
            role__in=["superuser", "main_admin", "person", "technician"]
        ):
            ClubSettings.objects.get_or_create(
                club=user,
                billing_day=1
            )
        self.stdout.write(self.style.SUCCESS('Club Settings created.'))