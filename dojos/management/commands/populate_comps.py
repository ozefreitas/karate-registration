from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dojos.models import CompetitionDetail
import os
from django.utils.timezone import datetime


class Command(BaseCommand):
    help = "Create competitions data"

    def handle(self, *args, **kwargs):
        user = User.objects.filter(username=os.getenv("DJANGO_SUPERUSER_USERNAME")).first()

        if not user:
            user = User.objects.create_superuser(username=os.getenv("DJANGO_SUPERUSER_USERNAME"), password=os.getenv("DJANGO_SUPERUSER_PASSWORD"))

        competitions = [
            CompetitionDetail(name="1 Jornada Liga Soshinkai", location="Fafe", season="2425", start_registration=datetime(2024, 11, 1),
                              end_registration=datetime(2024, 11, 30), retifications_deadline=datetime(2024, 12, 12), competition_date=datetime(2024, 12, 17)),
            CompetitionDetail(name="2 Jornada Liga Soshinkai", location="Caldas da Rainha", season="2425", start_registration=datetime(2025, 1, 10),
                              end_registration=datetime(2025, 1, 20), retifications_deadline=datetime(2025, 1, 27), competition_date=datetime(2025, 1, 31)),
            CompetitionDetail(name="3 Jornada Liga Soshinkai", location="Águeda", season="2425", start_registration=datetime(2025, 5, 1),
                              end_registration=datetime(2025, 5, 20), retifications_deadline=datetime(2025, 5, 27), competition_date=datetime(2025, 6, 5)),
            CompetitionDetail(name="Torneio Shihan Mário Águas", location="Matosinhos", season="2425", start_registration=datetime(2025, 6, 1),
                              end_registration=datetime(2025, 6, 16), retifications_deadline=datetime(2025, 6, 25), competition_date=datetime(2025, 6, 30)),                
        ]

        CompetitionDetail.objects.bulk_create(competitions)