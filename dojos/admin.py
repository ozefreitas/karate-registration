from django.contrib import admin
from .models import CompetitionDetail, FeedbackData, Profile

# Register your models here.

admin.site.register(CompetitionDetail)
admin.site.register(FeedbackData)
admin.site.register(Profile)