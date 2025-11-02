import datetime
from django.db import transaction
from .models import Event
from core.models import Notification
from core.models import User
from decouple import config


class CompetitionEndedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        today = datetime.date.today()
        competition_details = Event.objects.filter(has_ended=False)
        for comp_detail in competition_details:
                # if competition day passes by, "has ended" go true
                if comp_detail.event_date < today:
                    comp_detail.has_ended=True
                    comp_detail.save()
                    config_main_admin = config('MAIN_ADMIN')
                    main_admin = User.objects.get(username=config_main_admin)
                    childrens = main_admin.children.all()

                    notifications = [
                        Notification(
                            club_user=child,
                            notification=(
                                f'O Evento "{comp_detail.name}" acabou. '
                                "Por favor, dirija-se à área do Evento para o classificar."
                            ),
                            type="rate_event",
                            can_remove=True
                        )
                        for child in childrens
                    ]

                    with transaction.atomic():
                        Notification.objects.bulk_create(notifications)
                        
        return self.get_response(request)