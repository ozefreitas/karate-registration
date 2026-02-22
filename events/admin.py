from django.contrib import admin
from .models import Event, FeedbackData, Announcement, Discipline, DisciplineMember, DisciplineTeam

# Register your models here.

class EventAdmin(admin.ModelAdmin):
    readonly_fields = ("id",)
    list_display = ("name", "location", "season")
    search_fields = ("name", "location")
    ordering = ("start_registration", "event_date")


admin.site.register(Event, EventAdmin)
admin.site.register(Discipline)
admin.site.register(DisciplineMember)
admin.site.register(DisciplineTeam)
admin.site.register(FeedbackData)
admin.site.register(Announcement)