from django.urls import path, include
from . import views
from dojos.views import rules
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'athletes', views.AthletesViewSet, basename='athletes')
router.register(r'teams', views.TeamsViewSet, basename='teams')
router.register(r'classifications', views.ClassificationsViewSet, basename='classifications')

urlpatterns = [
    path('', include(router.urls)),
]
