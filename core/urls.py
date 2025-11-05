from django.urls import path, include
from django.urls import path
from . import views

from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import TokenRefreshView


router = routers.DefaultRouter()
router.register(r'categories', views.CategoriesViewSet, basename='categories')
router.register(r'request_acount', views.RequestedAcountViewSet, basename='request-acount')
router.register(r'notifications', views.NotificationViewSet, basename='notifications')

urlpatterns = [
    path('', include(router.urls)),
    path("auth/token/", views.CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('sign_up/generate_token/', views.sign_up_token, name="generate-token"),
    path('sign_up/get_token_username/', views.get_token_username, name="token-username"),
    path('sign_up/get_token_by_username/', views.get_token_by_username, name="username-token"),
    path('sign_up/register_user/', views.RegisterView.as_view(), name="register-with-token"),
    path('password_recovery/list_requests/', views.get_password_requests, name="password-requests"),
    path('password_recovery/request/', views.request_password_reset, name="request-password-reset"),
    path('password_recovery/generate_url/', views.generate_password_recovery_url, name="generate-password-recovery-url"),
    path(
        'password_recovery/confirm/<uidb64>/<token>/',
        views.PasswordResetConfirmAPI.as_view(),
        name="password_reset_confirm"
    ),
    path('current_season/', views.current_season, name="current-season"),
    path('login/', views.CustomAuthToken.as_view(), name="user-login"),
    path('me/', views.UserDetailView.as_view(), name="user-detail"),
    path('logout/', views.LogoutView.as_view(), name="user-logout"),
    path('users/', views.users, name="users"),

    path('club_notifications/', views.notifications, name="notifications"),
]
