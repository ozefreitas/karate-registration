from django.contrib import admin
from .models import User, SignupToken, RequestedAcount, RequestPasswordReset

# Register your models here.

class RequestPasswordResetAdmin(admin.ModelAdmin):
    readonly_fields = ('dojo_user',)

admin.site.register(User)
admin.site.register(RequestedAcount)
admin.site.register(SignupToken)
admin.site.register(RequestPasswordReset, RequestPasswordResetAdmin)