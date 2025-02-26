from django import template

register = template.Library()

@register.filter
def startswith(text, starts):
    if isinstance(text, str):
        if text == "/":
            return 1
        elif text.startswith(starts):
            return 2
    return 0