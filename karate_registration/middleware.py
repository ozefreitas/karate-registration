import datetime
from django.conf import settings
from django.shortcuts import render

class RegistrationClosedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        deadline_str = getattr(settings, 'REGISTRATION_DEADLINE', None)
        if deadline_str:
            deadline_date = datetime.datetime.strptime(deadline_str, '%Y-%m-%d').date()
            today = datetime.date.today()

            if today > deadline_date:
                # Render a custom page for registration closure
                return render(request, 'templates/error/registrations_closed.html', status=403)

        return self.get_response(request)


class TeamsNotAvailableMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        next_comp = getattr(settings, 'NEXT_COMPETITION', None)
        if request.path == '/teams/':
            if "Liga" in next_comp:
                # Render a custom page for registration closure
                return render(request, 'templates/error/teams_not_available.html', status=403)

        return self.get_response(request)