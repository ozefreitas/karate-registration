from django.contrib import admin
from .models import Event, FeedbackData, Profile, Notification, Announcement, DojosRatingAudit, User, Discipline

# Register your models here.

class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "season")
    search_fields = ("name", "location")
    ordering = ("start_registration", "event_date")

class DojosRatingAuditAdmin(admin.ModelAdmin):
    readonly_fields = ("dojo", "event", "rating")

admin.site.register(User)
admin.site.register(Event, EventAdmin)
admin.site.register(Discipline)
admin.site.register(FeedbackData)
admin.site.register(Profile)
admin.site.register(Notification)
admin.site.register(Announcement)
admin.site.register(DojosRatingAudit, DojosRatingAuditAdmin)