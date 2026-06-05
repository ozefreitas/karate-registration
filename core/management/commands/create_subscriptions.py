from django.core.management.base import BaseCommand
from datetime import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model
from clubs.models import ClubSubscription, ClubSubscriptionConfig

User = get_user_model()

class Command(BaseCommand):
    help = "Creates yearly subscriptions for all clubs."

    def handle(self, *args, **kwargs):
        now = timezone.now()
        year = now.year + 1 if now.month > 8 else now.year

        last_day_of_year = datetime(year=now.year, month=12, day=31, tzinfo=timezone.get_current_timezone())

        clubs = User.objects.filter(role__in=["free_club", "subed_club"])

        created = 0

        for club in clubs:
            admin = club.parent  
            if not admin:
                continue

            amount = ClubSubscriptionConfig.get_amount_for(admin)

            obj, was_created = ClubSubscription.objects.get_or_create(
                club=club,
                year=year,
                due_date=last_day_of_year,
                defaults={"amount": amount},
            )

            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(f"{created} subscriptions created for {year}.")
        )
