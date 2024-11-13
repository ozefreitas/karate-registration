from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="registration-home"),
    path('login/', views.login, name="registration-login"),
    path('form/', views.form, name="registration-form"),
    path('help/', views.help, name="registration-help"),
    path('thanks/', views.thanks, name="registration-thanks"),
    path('wrong/', views.wrong, name="registration-wrong"),
]
