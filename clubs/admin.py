from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Profile, ClubRatingAudit, Club

# Register your models here.

class ClubsRatingAuditAdmin(admin.ModelAdmin):
    readonly_fields = ("club", "event", "rating")

admin.site.register(Club)
admin.site.register(Profile)
admin.site.register(ClubRatingAudit, ClubsRatingAuditAdmin)