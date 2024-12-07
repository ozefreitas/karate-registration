from django.contrib import admin
from .models import CompetitionsDetails, FeedbackData, Profile

# Register your models here.

admin.site.register(CompetitionsDetails)
admin.site.register(FeedbackData)
admin.site.register(Profile)