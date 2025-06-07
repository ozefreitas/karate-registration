from django.contrib import admin
from .models import Athlete, Dojo, Team, Classification

# Register your models here.

class AthleteAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "category", "match_type", "gender")
    search_fields = ("first_name", "last_name", "category", "match_type", "dojo")


class TeamAdmin(admin.ModelAdmin):
    list_display = ("category", "match_type", "gender", "team_number")
    search_fields = ("category", "match_type", "gender", "dojo")


class ClassificationAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


admin.site.register(Athlete, AthleteAdmin)
admin.site.register(Dojo)
admin.site.register(Team, TeamAdmin)
admin.site.register(Classification, ClassificationAdmin)