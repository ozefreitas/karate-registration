from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="registration-home"),
    path('help/', views.help, name="registration-help"),
    path('thanks/', views.thanks, name="registration-thanks")
]
