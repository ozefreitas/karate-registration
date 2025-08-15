from django.urls import path, include
from . import views
from dojos.views import rules
from rest_framework import routers

from rest_framework.authtoken.views import obtain_auth_token

router = routers.DefaultRouter()
router.register(r'categories', views.CategoriesViewSet, basename='categories')
router.register(r'request_acount', views.RequestedAcountViewSet, basename='request-acount')

urlpatterns = [
    path('', include(router.urls)),
    path('generate_token/', views.sign_up_token, name="generate-token"),
    path('get_token_username/', views.get_token_username, name="token-username"),
    path('get_token_by_username/', views.get_token_by_username, name="username-token"),
    path('register_user/', views.RegisterView.as_view(), name="register-with-token"),
    path('current_season/', views.current_season, name="current-season"),
    path('login/', obtain_auth_token, name="user-login"),
    path('me/', views.UserDetailView.as_view(), name="user-detail"),
    path('logout/', views.LogoutView.as_view(), name="user-logout"),
]