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
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

handler500 = 'dojos.views.custom_500'
handler404 = 'dojos.views.custom_404'

urlpatterns = [
    path('admin/', admin.site.urls),

    # API visualization
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Endpoint url patterns
    path('', include("registration.urls")),
    path('', include("dojos.urls")),
    path('', include("draw.urls")),
    path('', include("core.urls")),

    # Account operations
    path('logout/', dojo_views.logout_user, name="dojos-logout"),
    path('register/password_reset/', dojo_views.reset_password, name="dojos-reset-password"),
    path('register/password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name="password/reset_password_done.html"),
        name="dojos-reset-password-done"),
    path('register/password_reset_confirm/<uidb64>/<token>/', dojo_views.password_reset_confirmation, 
        name="dojos-reset-password-confirm"),
    path('register/password_reset_complete/',
        auth_views.PasswordResetCompleteView.as_view(template_name="password/reset_password_complete.html"),
        name="dojos-reset-password-complete"),
    path('register/password_change/', dojo_views.change_password, name="dojos-change-password"),
    path('register/', include('django.contrib.auth.urls')),
    path('test/', dojo_views.test_500_error, name='test_error')
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)