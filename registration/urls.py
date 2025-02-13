from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="registration-home"),
    path('help/', views.help, name="registration-help"),
    path('athletes/', views.athletes, name="registration-athletes"),
    path('teams/', views.teams, name="registration-teams"),
    path('form/', views.form, name="registration-form"),
    path('teams_form/', views.team_form, name="registration-teams-form"),
    path('wrong/', views.wrong, name="registration-wrong"),
    path('delete/<str:type>/<int:id>/', views.delete, name="registration-delete"),
    path('update_registration/<str:type>/<int:id>/', views.update, name="registration-update"),
]
