from django.urls import path, include
from . import views
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'events', views.EventViewSet, basename='events')
router.register(r'disciplines', views.DisciplineViewSet, basename='disciplines')

urlpatterns = [
    path('', include(router.urls)),
]
