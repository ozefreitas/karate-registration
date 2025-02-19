from datetime import date
from .utils.utils import get_next_competition, change_current_season


def upcoming_dates(request):
    """Function that checks if we are inside the retifications period"""
    today = date.today()
    upcoming_message = False
    next_comp = get_next_competition()
    if next_comp:
        if next_comp.end_registration < today and today <= next_comp.retifications_deadline:
        # Check if any dates in YourModel are in the future
            upcoming_message = True
    
    return {'upcoming_message': upcoming_message}


def current_season(request):
    return {'current_season': change_current_season()}