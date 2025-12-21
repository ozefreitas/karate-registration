from django.contrib import admin
from .models import User, SignupToken, RequestedAcount, RequestPasswordReset, Category, Notification, MonthlyPaymentPlan, MemberValidationRequest

# Register your models here.

class RequestPasswordResetAdmin(admin.ModelAdmin):
    readonly_fields = ('club_user',)

admin.site.register(User)
admin.site.register(RequestedAcount)
admin.site.register(SignupToken)
admin.site.register(RequestPasswordReset, RequestPasswordResetAdmin)
admin.site.register(Category)
admin.site.register(Notification)
admin.site.register(MonthlyPaymentPlan)
admin.site.register(MemberValidationRequest)