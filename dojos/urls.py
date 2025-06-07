from django.urls import path, include
from . import views
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token


router = routers.DefaultRouter()
router.register(r'events', views.CompetitionViewSet, basename='competitions')

urlpatterns = [
    path('', include(router.urls)),
    path('dojos/', views.notifications, name="notifications"),
    path('current_season/', views.current_season, name="current-season"),
    path('register_user/', views.RegisterView.as_view(), name="dojos-register"),
    path('login/', obtain_auth_token, name="dojos-login"),
    path('me/', views.UserDetailView.as_view(), name="dojos-detail"),
    path('logout/', views.LogoutView.as_view(), name="dojos-logout"),
    path('feedback/', views.feedback, name="dojos-feedback"),
    path('update_profile/', views.update_dojo_account, name="dojos-update-account"),
    path('delete_account/', views.delete_dojo_account, name="dojos-delete-account"),
]
