from datetime import datetime
from registration.models import Member
from core.utils.utils import calc_age

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


def get_real_member(member):
    """will return the first member based on identity fields, by creation date. Always returns the same object by member

    Args:
        member (Member): a Member object

    Returns:
        Member: the first appearing Member object with common identity fields as the one provided
    """
    return Member.objects.filter(
        first_name=member.first_name,
        last_name=member.last_name,
        birth_date=member.birth_date,
        id_number=member.id_number,
    ).order_by("creation_date").first()


def get_identity_members(member, qs_object = False):
    """Returns all the members with the same identity fields. Can give both a Member object or a dictionary with the needed fields

    Args:
        member (Member): a Member object
        qs_object (bool, optional): _description_. Defaults to False.

    Returns:
        Member: the first appearing Member object with common identity fields as the one provided
    """
    if qs_object:
        return Member.objects.filter(
        first_name=member.first_name,
        last_name=member.last_name,
        birth_date=member.birth_date,
        id_number=member.id_number,
    ).exclude(id=member.id)

    return Member.objects.filter(
        first_name=member.get("first_name"),
        last_name=member.get("last_name"),
        birth_date=member.get("birth_date"),
        id_number=member.get("id_number"),
    ).exclude(id=member.get("id"))


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