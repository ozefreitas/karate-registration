from django.contrib import admin
from .models import Member, Team, Classification, MonthlyPersonPayment, MonthlyPersonPaymentConfig, Person, Membership

# Register your models here.

class PersonAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "gender")
    search_fields = ("first_name", "last_name", "club")


class TeamAdmin(admin.ModelAdmin):
    list_display = ("gender", "team_number")
    search_fields = ("gender", "club")


class ClassificationAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


admin.site.register(Member)
admin.site.register(Person, PersonAdmin)
admin.site.register(Membership)
admin.site.register(MonthlyPersonPayment)
admin.site.register(MonthlyPersonPaymentConfig)
admin.site.register(Team, TeamAdmin)
admin.site.register(Classification, ClassificationAdmin)