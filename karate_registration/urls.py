"""
URL configuration for karate_registration project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from dojos import views as dojo_views
from django.conf.urls import handler500, handler404

handler500 = 'dojos.views.custom_500'
handler404 = 'dojos.views.custom_404'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("registration.urls")),
    path('register/', include("dojos.urls")),
    path('register/', include('django.contrib.auth.urls')),
    path('logout/', dojo_views.logout_user, name="dojos-logout"),
    path('profile/', dojo_views.profile, name="dojos-profile"),
    path('test/', dojo_views.test_500_error, name='test_error')
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)