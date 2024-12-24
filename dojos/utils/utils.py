import datetime
from ..models import CompetitionsDetails

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