import datetime

from django.conf import settings
from django.shortcuts import render
from .models import CompetitionsDetails

def get_next_competition():
    today = datetime.date.today()
    competition_details = CompetitionsDetails.objects.all()
    min_date = float("inf")
    next_comp = None
    for comp_detail in competition_details:
        days_to_comp = comp_detail.competition_date - today
        if int(days_to_comp.days) > 0 and min_date > int(days_to_comp.days):
            min_date = int(days_to_comp.days)
            next_comp = comp_detail.name
    next_comp = CompetitionsDetails.objects.filter(name=next_comp)
    return next_comp

class RegistrationClosedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        today = datetime.date.today()
        next_comp = get_next_competition()
        
        if next_comp[0].start_registration > today and today > next_comp[0].end_registration:
            # Render a custom page for registration closure
            return render(request, 'templates/error/registrations_closed.html', status=403)

        return self.get_response(request)


class TeamsNotAvailableMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        next_comp = get_next_competition()
        print(next_comp)
        if request.path == "/teams/":
            if "Liga" in next_comp[0].name:
                # Render a custom page for registration not available
                return render(request, 'templates/error/teams_not_available.html', status=403)

        return self.get_response(request)