import datetime
from django.conf import settings
from django.shortcuts import render
from .models import CompetitionDetail
from registration.models import Athlete, ArchivedAthlete
from .utils.utils import get_next_competition


class NoListedCompetitionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        competition_details = CompetitionDetail.objects.all()
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
            if next_comp.start_registration > today and today > next_comp.retifications_deadline:
                # Render a custom page for registration closure
                return render(request, 'error/registrations_closed.html', status=403)

        return self.get_response(request)


class TeamsNotAvailableMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        next_comp = get_next_competition()
        if not settings.DEBUG:
            if next_comp != None and request.path == "/teams/" and "Liga" in next_comp.name:
                # Render a custom page for registration not available
                competition_details = CompetitionDetail.objects.all()
                return render(request, 'error/teams_not_available.html', {"calendar": competition_details}, status=403)

        return self.get_response(request)


class CompetitionEndedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        today = datetime.date.today()
        competition_details = CompetitionDetail.objects.filter(has_ended=False)
        for comp_detail in competition_details:
                # if competition day passes by, has ended go true
                if comp_detail.competition_date < today:
                    comp_detail.has_ended=True
                    comp_detail.save()

                    athletes = Athlete.objects.all()
                    for athlete in athletes:
                        athlete_data = {"competition": comp_detail}
                        for field in athlete._meta.fields:
                            if field != "id":
                                athlete_data[field.name] = getattr(athlete, field.name)
                        ArchivedAthlete.objects.create(**athlete_data)
                    
                    athletes.delete()

        return self.get_response(request)