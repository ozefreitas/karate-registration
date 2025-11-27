from django.urls import path, include
from . import views
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'clubs', views.ClubsViewSet, basename='clubs')
router.register(r'club_subscription', views.ClubSubscriptionsViewSet, basename='club-subscriptions')

urlpatterns = [
    path('', include(router.urls)),
    path('users/members/', views.club_members, name="clubs-members"),
    # path('feedback/', views.feedback, name="dojos-feedback"),
]
