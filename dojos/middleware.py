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
    next_comp = CompetitionsDetails.objects.filter(name=next_comp).first()
    return next_comp

class NoListedCompetitions:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        competition_details = CompetitionsDetails.objects.all()
        if not settings.DEBUG:
            if request.path == "/athletes/" or request.path == "/teams/" or request.path == "/":
                if len(competition_details) == 0:
                    return render(request, 'error/no_comps_error.html', status=403)
        return self.get_response(request)


class RegistrationClosedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        today = datetime.date.today()
        next_comp = get_next_competition()
        if next_comp != None and (request.path == "/athletes/" or request.path == "/teams/"):
            if next_comp.start_registration > today and today > next_comp.end_registration:
                # Render a custom page for registration closure
                return render(request, 'error/registrations_closed.html', status=403)

        return self.get_response(request)


class TeamsNotAvailableMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        next_comp = get_next_competition()
        if next_comp != None and request.path == "/teams/" and "Liga" in next_comp.name:
            # Render a custom page for registration not available
            return render(request, 'error/teams_not_available.html', status=403)

        return self.get_response(request)