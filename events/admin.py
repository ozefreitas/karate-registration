from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Event, FeedbackData, Announcement, Discipline

# Register your models here.

class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "season")
    search_fields = ("name", "location")
    ordering = ("start_registration", "event_date")


admin.site.register(Event, EventAdmin)
admin.site.register(Discipline)
admin.site.register(FeedbackData)
admin.site.register(Announcement)