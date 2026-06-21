from django.contrib import admin
from .models import User, Profile, SignupToken, RequestedAcount, RequestPasswordReset, Category, Notification, MonthlyPaymentPlan, MemberValidationRequest, FeedbackData

# Register your models here.

class RequestPasswordResetAdmin(admin.ModelAdmin):
    readonly_fields = ('club_user', "requested_at")

admin.site.register(User)
admin.site.register(Profile)
admin.site.register(RequestedAcount)
admin.site.register(SignupToken)
admin.site.register(RequestPasswordReset, RequestPasswordResetAdmin)
admin.site.register(Category)
admin.site.register(Notification)
admin.site.register(MonthlyPaymentPlan)
admin.site.register(MemberValidationRequest)
admin.site.register(FeedbackData)