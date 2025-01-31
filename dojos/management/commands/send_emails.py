from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from dojos.utils.utils import get_next_competition
from dojos.models import CompetitionDetail
from registration.models import Athlete
from smtplib import SMTPException


class Command(BaseCommand):
    help = "Send reminder emails to all registered dojos"

    def handle(self, *args, **kwargs):
        today = now().date()
        next_week = today + timedelta(days=10)

        # Find competitions happening next week
        competitions = CompetitionDetail.objects.filter(competition_date=next_week)
        if not competitions.exists():
            self.stdout.write("No competitions happening next week.")
            return
        
        next_comp = get_next_competition()
        user_dojos = User.objects.all()
        for dojo in user_dojos:
            if not dojo.is_superuser:
                dojo_athletes = Athlete.objects.filter(dojo=dojo.id)
                # TODO: add the number of unique registered athletes
                try:
                    send_mail(
                        subject=f"Aproximação da {next_comp.name}",
                        message=f"Caro Dojo {dojo.username},\n\n"
                                f"Este email serve para relembrar que a {next_comp.name} da época {next_comp.season}, se irá realizer dentro de poucos dias, em {next_comp.location}!\n"
                                "Estamos muito entusiasmados em recebê-lo.\n\n"
                                f"Informo que, até à data deste email, tem cerca de {len(dojo_athletes)} inscrições submetidas com sucesso.\n"
                                "Estas ainda podem ser editadas sem qualquer problema, até ao fim do período permitido.\n"
                                "Aproveito para relembrar também que ainda dispõe de 3 dias para submeter/editar as suas inscrições, "
                                "apelando assim para não o fazer no dia da prova.\n"
                                "Obrigado por se ter registado pela Karate Score App!\n\n"
                                "Atenciosamente,\n\n"
                                "A equipa da Karate Score App:\n"
                                "José Freitas\n\n"
                                "Contactos:\n- jpsfreitas12@gmail.com / 917479331\n- info@skiportugal.pt",
                        from_email='jpsfreitas12@gmail.com',
                        recipient_list=[dojo.email],
                        fail_silently=False,
                    )
                except Exception as exc:
                    raise SMTPException(exc)
        self.stdout.write(self.style.SUCCESS("Successfully sent emails to all dojos."))