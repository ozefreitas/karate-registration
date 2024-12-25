from django.contrib import admin
from .models import Athlete, Dojo, Teams, ArchivedAthlete

# Register your models here.

admin.site.register(Athlete)
admin.site.register(Dojo)
admin.site.register(Teams)
admin.site.register(ArchivedAthlete)