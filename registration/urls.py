from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="registration-home"),
    path('form/', views.form, name="registration-form"),
    path('teams_form/', views.team_form, name="registration-teams-form"),
    path('help/', views.help, name="registration-help"),
    path('thanks/', views.thanks, name="registration-thanks"),
    path('wrong/', views.wrong, name="registration-wrong"),
    path('delete/<str:type>/<int:id>/', views.delete, name="registration-delete"),
    path('update_registration/<str:type>/<int:id>/', views.update, name="registration-update"),
]
