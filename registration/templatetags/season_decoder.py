from django import template

register = template.Library()

@register.filter
def decode_season(season):
    first, second = "20" + season[:2], "20" + season[2:]
    return first + "/" + second