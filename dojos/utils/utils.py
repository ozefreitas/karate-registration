import datetime
from ..models import CompetitionDetail
from django.utils import timezone

def get_next_competition():
    today = datetime.date.today()
    competition_details = CompetitionDetail.objects.all()
    min_date = float("inf")
    next_comp = None
    for comp_detail in competition_details:
        days_to_comp = comp_detail.competition_date - today
        if int(days_to_comp.days) > 0 and min_date > int(days_to_comp.days):
            min_date = int(days_to_comp.days)
            next_comp = comp_detail.name
    next_comp = CompetitionDetail.objects.filter(name=next_comp).first()
    return next_comp


def change_current_season(date = None):
    date = date or timezone.now().date()
    if date.month >= 9:
        # From September to December, season is current_year/current_year+1
        season_start = date.year
        season_end = date.year + 1
    else:
        # From January to August, season is previous_year/current_year
        season_start = date.year - 1
        season_end = date.year
    return f"{season_start}/{season_end}"


def check_comp_data(form_data):
    errors = []
    today = datetime.date.today()
    if form_data.cleaned_data["start_registration"] <= today:
        errors.append("Data de início de inscrições é impossível")
    if form_data.cleaned_data["end_registration"] <= today:
        errors.append("Data de fim de inscrições é impossível")
    if form_data.cleaned_data["retifications_deadline"] <= today:
        errors.append("Data de retificações é impossível")
    if form_data.cleaned_data["competition_date"] <= today:
        errors.append("Data da prova é impossível")
    return errors