from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'competitions', views.CompetitionViewSet, basename='competitions')

urlpatterns = [
    path('', include(router.urls)),
    path('dojos/', views.notifications, name="notifications"),
    path('current_season/', views.current_season, name="current-season"),
    path('register_user/', views.register_user, name="dojos-register"),
    path('login/', views.login_user, name="dojos-login"),
    path('feedback/', views.feedback, name="dojos-feedback"),
    path('update_profile/', views.update_dojo_account, name="dojos-update-account"),
    path('delete_account/', views.delete_dojo_account, name="dojos-delete-account"),
]
