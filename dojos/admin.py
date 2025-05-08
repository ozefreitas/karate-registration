from django.contrib import admin
from .models import CompetitionDetail, FeedbackData, Profile, Notification, Announcement

# Register your models here.

class CompetitionDetailAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "season")
    search_fields = ("name", "location")
    ordering = ("start_registration", "competition_date")

admin.site.register(CompetitionDetail, CompetitionDetailAdmin)
admin.site.register(FeedbackData)
admin.site.register(Profile)
admin.site.register(Notification)
admin.site.register(Announcement)