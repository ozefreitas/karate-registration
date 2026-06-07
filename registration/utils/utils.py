from datetime import datetime
from core.utils.utils import calc_age
import math


def get_comp_age(date_of_birth: datetime) -> int:
    """Function that return the current age of an athlete, in real time

    Args:
        date_of_birth (datetime): The birth date of the athlete. Must be an instance of datetime 

    Returns:
        int: The age as an int
    """
    year_of_birth = date_of_birth.year
    date_now = datetime.now()
    current_age = date_now.year - year_of_birth
    if (date_now.month, date_now.day) < (date_of_birth.month, date_of_birth.day):
        current_age -= 1
    return current_age


def athlete_age(member, age_method, season):
    """Computes the age of a Member based on the age calc method provided by env vars

    Args:
        member (Member): a Member object
        age_method (string): age method provided in env vars
        season (string): year to be used as base for calculation

    Returns:
        string: age of the Member 
    """
    return (
        get_comp_age(member.birth_date)
        if age_method == "true"
        else calc_age(age_method, member.birth_date, season)
    )


def next_power_of_2(n):
    return 1 if n == 0 else 2 ** math.ceil(math.log2(n))