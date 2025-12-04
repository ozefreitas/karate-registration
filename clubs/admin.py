from django.contrib import admin
from .models import Profile, ClubRatingAudit, Club, ClubSubscription, ClubSubscriptionConfig

# Register your models here.

class ClubsRatingAuditAdmin(admin.ModelAdmin):
    readonly_fields = ("club", "event", "rating")

class ClubSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("club", "amount", "year")

admin.site.register(Club)
admin.site.register(Profile)
admin.site.register(ClubRatingAudit, ClubsRatingAuditAdmin)
admin.site.register(ClubSubscription, ClubSubscriptionAdmin)
admin.site.register(ClubSubscriptionConfig)