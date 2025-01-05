from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from registration.models import Dojo  # Update with your model name

class Command(BaseCommand):
    help = "Send reminder emails to all registered athletes"

    def handle(self, *args, **kwargs):
        dojos = Dojo.objects.all()  # Adjust filter if needed
        for dojo in dojos:
            send_mail(
                subject="Karate Tournament Reminder",
                message=f"Dear {dojo.dojo},\n\n"
                        "This is a friendly reminder that the karate tournament is just a few days away! "
                        "We are excited to see you there.\n\n"
                        "Thank you for registering!\nKarate Tournament Team",
                from_email='jpsfreitas12@gmail.com',
                recipient_list=['jpsfreitas19@gmail.com'],
                fail_silently=False,
            )
        self.stdout.write(self.style.SUCCESS("Successfully sent emails to all athletes."))