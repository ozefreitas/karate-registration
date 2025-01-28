from django.contrib import admin
from .models import Athlete, Dojo, Team, ArchivedAthlete, Coach

# Register your models here.

admin.site.register(Athlete)
admin.site.register(Dojo)
admin.site.register(Team)
admin.site.register(ArchivedAthlete)
admin.site.register(Coach)