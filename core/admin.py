from django.contrib import admin
from .models import User, SignupToken, RequestedAcount

# Register your models here.

admin.site.register(User)
admin.site.register(RequestedAcount)
admin.site.register(SignupToken)