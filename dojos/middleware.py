import datetime
from django.conf import settings
from django.shortcuts import render
from .models import CompetitionDetail
from registration.models import Individual, ArchivedIndividual, Team, ArchivedTeam
from .utils.utils import get_next_competition


class NoListedCompetitionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        competition_details = CompetitionDetail.objects.all()
        # if not settings.DEBUG:
        if request.path == "/" and len(competition_details) == 0:
            return render(request, 'error/no_comps_error.html', status=403)
        return self.get_response(request)


class CompetitionEndedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        today = datetime.date.today()
        competition_details = CompetitionDetail.objects.filter(has_ended=False)
        for comp_detail in competition_details:
                # if competition day passes by, "has ended" go true
                if comp_detail.competition_date < today:
                    comp_detail.has_ended=True
                    comp_detail.save()

                    individuals = Individual.objects.all()
                    teams = Team.objects.all()
                    
                    for individual in individuals:
                        individual_data = {"competition": comp_detail}
                        for field in individual._meta.fields:
                            if field != "id":
                                individual_data[field.name] = getattr(individual, field.name)
                        ArchivedIndividual.objects.create(**individual_data)
                    for team in teams:
                        team_data = {"competition": comp_detail}
                        for field in team._meta.fields:
                            if field != "id":
                                team_data[field.name] = getattr(team, field.name)
                        ArchivedTeam.objects.create(**team_data)
                        
                    
                    individuals.delete()
                    teams.delete()

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
            with open('/home/karatescorappregistration/karate-registration/maintenance.flag', 'r') as flag:
                if flag.read().strip() == 'on':
                    return render(request, 'error/maintenance.html')
        except FileNotFoundError:
            pass
        return self.get_response(request)