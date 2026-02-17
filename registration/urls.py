from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'persons', views.PersonsViewSet, basename='persons')
router.register(r'memberships', views.MemberShipsViewSet, basename='member-ships')
router.register(r'monthly_payments', views.MonthlyMemberPaymentViewSet, basename='monthly-payments')
router.register(r'teams', views.TeamsViewSet, basename='teams')
router.register(r'classifications', views.ClassificationsViewSet, basename='classifications')
router.register(r"monthly_member_payment_configs", views.MonthlyMemberPaymentConfigViewSet, basename="monthly-member-payment-configs")

urlpatterns = [
    path('', include(router.urls)),
]
