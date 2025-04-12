from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils.timezone import datetime

from dojos.models import CompetitionDetail
from registration.models import Dojo

import os
from dotenv import load_dotenv


loaded = load_dotenv(".env.dev")
print("Loaded:", loaded)  

class Command(BaseCommand):
    help = "Create competitions data"

    def handle(self, *args, **kwargs):
        # user = User.objects.filter(username=os.getenv("DJANGO_SUPERUSER_USERNAME")).first()
        
        # if not user:
        #     user = User.objects.create_superuser(username=os.getenv("DJANGO_SUPERUSER_USERNAME"), password=os.getenv("DJANGO_SUPERUSER_PASSWORD"))

        competitions = [
            CompetitionDetail(id=slugify("1 Jornada Liga Soshinkai 2425"), name="1 Jornada Liga Soshinkai", location="Fafe", season="2425", start_registration=datetime(2024, 11, 1),
                              end_registration=datetime(2024, 11, 30), retifications_deadline=datetime(2024, 12, 12), competition_date=datetime(2024, 12, 17)),
            CompetitionDetail(id=slugify("2 Jornada Liga Soshinkai 2425"), name="2 Jornada Liga Soshinkai", location="Caldas da Rainha", season="2425", start_registration=datetime(2025, 1, 10),
                              end_registration=datetime(2025, 1, 20), retifications_deadline=datetime(2025, 1, 27), competition_date=datetime(2025, 1, 31)),
            CompetitionDetail(id=slugify("3 Jornada Liga Soshinkai 2425"), name="3 Jornada Liga Soshinkai", location="Águeda", season="2425", start_registration=datetime(2025, 5, 1),
                              end_registration=datetime(2025, 5, 20), retifications_deadline=datetime(2025, 5, 27), competition_date=datetime(2025, 6, 5)),
            CompetitionDetail(id=slugify("Torneio Shihan Mário Águas 2425"), name="Torneio Shihan Mário Águas", location="Matosinhos", season="2425", start_registration=datetime(2025, 6, 1),
                              end_registration=datetime(2025, 6, 16), retifications_deadline=datetime(2025, 6, 25), competition_date=datetime(2025, 6, 30)),                
        ]

        for competition in competitions:
            competition.save()

        dojos = ["SOHINKAI",
                 "SCBOMBARRALENSE",
                 "PROSA-USSINES",
                 "NKSGUIMARAES",
                 "KARATELOUSADA",
                 "KSAGUEDA",
                 "KCALCOBACA",
                 "JCBOAVISTA",
                 "ILHAVO",
                 "HONBUDOJO",
                 "DKMAFAMUDE",
                 "CNKS-NASHINOKI",
                 "CLUBEACADEMICOBRAGANCA",
                 "CKSSUL",
                 "CKSODEMIRA",
                 "CKSNORTE",
                 "CKSCALDASRAINHA",
                 "CKSCADAVAL",
                 "CKRESTAURADORES",
                 "CKSMATOSINHOS",
                 "ASMELRES",
                 "ASKVIZELA",
                 "ASKKV-VAGOS",
                 "AKK-FELGUEIRAS",
                 "AKFAFE",
                 "AKAGUEDA",
                 "AEFCR-SK-PENICHE"]

        Dojo.objects.bulk_create([Dojo(dojo=dojo) for dojo in dojos])