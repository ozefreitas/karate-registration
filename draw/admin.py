from django.contrib import admin
from .models import Bracket, Match, FoulType, KataResult, KumiteResult, KumiteFoul

# Register your models here.

admin.site.register(Bracket)
admin.site.register(Match)
admin.site.register(FoulType)
admin.site.register(KataResult)
admin.site.register(KumiteResult)
admin.site.register(KumiteFoul)