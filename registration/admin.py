from django.contrib import admin
from .models import Member, Team, Classification, MonthlyMemberPayment, MonthlyMemberPaymentConfig

# Register your models here.

class MemberAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "gender", "member_type")
    search_fields = ("first_name", "last_name", "club")


class TeamAdmin(admin.ModelAdmin):
    list_display = ("category", "match_type", "gender", "team_number")
    search_fields = ("category", "match_type", "gender", "club")


class ClassificationAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


admin.site.register(Member, MemberAdmin)
admin.site.register(MonthlyMemberPayment)
admin.site.register(MonthlyMemberPaymentConfig)
admin.site.register(Team, TeamAdmin)
admin.site.register(Classification, ClassificationAdmin)