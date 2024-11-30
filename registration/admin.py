from django.contrib import admin
from .models import Athlete, Dojo, Teams

# Register your models here.

admin.site.register(Athlete)
admin.site.register(Dojo)
admin.site.register(Teams)