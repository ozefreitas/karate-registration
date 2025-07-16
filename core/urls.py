from django.urls import path, include
from . import views
from dojos.views import rules
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'categories', views.CategoriesViewSet, basename='categories')

urlpatterns = [
    path('', include(router.urls)),
]
