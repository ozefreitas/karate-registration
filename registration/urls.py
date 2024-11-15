from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="registration-home"),
    path('form/', views.form, name="registration-form"),
    path('help/', views.help, name="registration-help"),
    path('thanks/', views.thanks, name="registration-thanks"),
    path('wrong/', views.wrong, name="registration-wrong"),
    path('delete/<int:athlete_id>/', views.delete, name="registration-delete"),
    path('update_registration/<int:athlete_id>/', views.update, name="registration-update"),
]
