import datetime
from django.shortcuts import render
from django.core import serializers
from django.db import transaction
from .models import Event, Notification
import json
from registration.models import Team
from core.models import User
from decouple import config


class NoListedCompetitionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        competition_details = Event.objects.all()
        # if not settings.DEBUG:
        if request.path == "/" and len(competition_details) == 0:
            return render(request, 'error/no_comps_error.html', status=403)
        return self.get_response(request)


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
                            dojo=child,
                            notification=(
                                f'O Evento "{comp_detail.name}" acabou. '
                                "Por favor, dirija-se à área do Evento para o classificar."
                            ),
                            urgency="orange",
                            type="rate_event",
                            can_remove=True
                        )
                        for child in childrens
                    ]

                    with transaction.atomic():
                        Notification.objects.bulk_create(notifications)

                    # individuals = Individual.objects.filter(competition=comp_detail.id)
                    # teams = Team.objects.filter(competition=comp_detail.id)
                    # indiv_data = serializers.serialize("json", individuals)
                    # team_data = serializers.serialize("json", teams)
                    
                    # combined_data = {
                    #                 "individuals": json.loads(indiv_data),
                    #                 "teams": json.loads(team_data)
                    #             }
                    
                    # with open("archived_comps.json", "a") as out:
                    #     if out.tell() > 0:  # If the file is not empty, add a separator
                    #         out.write(",\n")
                    #     json.dump(combined_data, out, indent=4)
                    
                    # individuals.delete()
                    # teams.delete()

        return self.get_response(request)


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # if admin panels this is ignored
        if request.path.startswith('/admin/'):
            return self.get_response(request)
        
        # Check if maintenance mode is enabled
        try:
            if not request.user.is_superuser:
                with open('/home/karatescorappregistration/karate-registration/maintenance.flag', 'r') as flag:
                    if flag.read().strip() == 'on':
                        return render(request, 'error/maintenance.html')
        except FileNotFoundError:
            pass
        return self.get_response(request)