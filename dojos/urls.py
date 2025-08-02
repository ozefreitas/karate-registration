from django.urls import path, include
from . import views
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'events', views.EventViewSet, basename='events')
router.register(r'disciplines', views.DisciplineViewSet, basename='disciplines')
router.register(r'notifications', views.NotificationViewSet, basename='notifications')
router.register(r'dojos', views.DojosViewSet, basename='dojos')

urlpatterns = [
    path('', include(router.urls)),
    path('users/', views.users, name="users"),
    path('users/athletes/', views.dojos_athletes, name="dojos-athletes"),
    path('dojo_notifications/', views.notifications, name="notifications"),
    path('feedback/', views.feedback, name="dojos-feedback"),
]
