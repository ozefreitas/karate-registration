from datetime import date
from .models import CompetitionsDetails
from .utils.utils import get_next_competition


def upcoming_dates(request):
    today = date.today()
    upcoming_message = False
    next_comp = get_next_competition()
    if next_comp.end_registration < today and today <= next_comp.retifications_deadline:
    # Check if any dates in YourModel are in the future
        upcoming_message = True
    
    return {'upcoming_message': upcoming_message}