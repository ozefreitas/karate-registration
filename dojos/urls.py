from django.urls import path
from . import views

urlpatterns = [
    path('register_user/', views.register_user, name="dojos-register"),
    path('login/', views.login_user, name="dojos-login"),
    path('feedback/', views.feedback, name="dojos-feedback"),
    path('add_competition/', views.add_competition, name="dojos-competition"),
    path('update_profile/', views.update_dojo_account, name="dojos-update-account"),
    path('delete_account/', views.delete_dojo_account, name="dojos-delete-account"),
]
