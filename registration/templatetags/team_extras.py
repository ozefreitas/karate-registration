from django import template

register = template.Library()

@register.filter
def valid_athletes(team):
    """Returns a list of non-None athletes from the team model."""
    return [athlete for athlete in [team.athlete1, team.athlete2, team.athlete3, team.athlete4, team.athlete5] if athlete]