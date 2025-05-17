from django.contrib import admin
from .models import Athlete, Dojo, Team, Individual

# Register your models here.

class AthleteAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "category", "match_type", "gender", "dojo")
    search_fields = ("first_name", "last_name", "category", "match_type", "dojo")

class IndividualAdmin(admin.ModelAdmin):
    list_display = ("athlete", "dojo")


class TeamAdmin(admin.ModelAdmin):
    list_display = ("category", "match_type", "gender", "team_number")
    search_fields = ("category", "match_type", "gender", "dojo")


admin.site.register(Athlete, AthleteAdmin)
admin.site.register(Dojo)
admin.site.register(Team, TeamAdmin)
# admin.site.register(Individual)
admin.site.register(Individual, IndividualAdmin)