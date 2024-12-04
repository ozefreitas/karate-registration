from django.urls import path
from . import views

urlpatterns = [
    path('register_user/', views.register_user, name="dojos-register"),
    path('feedback/', views.feedback, name="dojos-feedback"),
]
