from django.urls import path, include
from . import views
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'bracket', views.BracketViewSet, basename='bracket')
router.register(r'match', views.MatchViewSet, basename='match')

urlpatterns = [
    path('', include(router.urls))
    ]