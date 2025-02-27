from django.urls import path
from . import views
from dojos.views import rules

urlpatterns = [
    path('', views.home, name="registration-home"),
    path('help/', views.help, name="registration-help"),
    path('rules/', rules, name="registration-rules"),
    path('athletes/', views.AthletesView.as_view(), name="registration-athletes"),
    path('coaches/', views.AthletesView.as_view(), name="registration-athletes"),
    path('individuals/<str:comp_id>/', views.IndividualsView.as_view(), name="registration-individual"),
    path('individuals/athletes_preview/<str:comp_id>/', views.athletes_preview, name="registration-athletes-preview"),
    path('teams/<str:comp_id>/', views.TeamView.as_view(), name="registration-teams"),
    path('form/', views.form, name="registration-form"),
    path('teams_form/<str:match_type>/<str:comp_id>/', views.team_form, name="registration-teams-form"),
    path('delete/<str:type>/<str:id>/<str:comp_id>/', views.delete, name="registration-delete"),
    path('update_registration/<str:type>/<str:match_type>/<str:id>/<str:comp_id>/', views.update, name="registration-update"),
    path('comp_detail/<str:comp_id>', views.comp_details, name="registration-comp"),
]
