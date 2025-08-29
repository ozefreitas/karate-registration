import datetime
from ..models import Event
from django.utils import timezone

def get_next_competition():
    today = datetime.date.today()
    competition_details = Event.objects.all()
    min_date = float("inf")
    next_comp = None
    for comp_detail in competition_details:
        days_to_comp = comp_detail.event_date - today
        if int(days_to_comp.days) > 0 and min_date > int(days_to_comp.days):
            min_date = int(days_to_comp.days)
            next_comp = comp_detail.name
    next_comp = Event.objects.filter(name=next_comp).first()
    return next_comp


def change_current_season(date = None):
    date = date or timezone.now().date()
    if date.month >= 8:
        # From August to December, season is current_year/current_year+1
        season_start = date.year
        season_end = date.year + 1
    else:
        # From January to July, season is previous_year/current_year
        season_start = date.year - 1
        season_end = date.year
    return f"{season_start}/{season_end}"


def range_decoder(min_age: int, max_age: int):
    """Function that returns a range 

    Args:
        min_age (int): minimum age from category
        max_age (int): maximum age from category

    Returns:
        range object: The range from the given range
    """
    some_range = range(min_age, max_age + 1)
    return some_range


def calc_age(method: str, birth_date) -> int:
    print(method)
    year_of_birth = birth_date.year
    current_season = change_current_season()
    age_at_comp = int(current_season.split("/")[0]) - year_of_birth
    if method == "season":
        if (birth_date.month, birth_date.day) > (8, 31):
            age_at_comp -= 1
        return age_at_comp
    elif method == "civil":
        return age_at_comp
