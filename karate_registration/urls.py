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
from django.contrib.auth import views as auth_views
from dojos import views as dojo_views

class CustomLoginView(auth_views.LoginView):
    def form_invalid(self, form):
        # Change the default error message
        # form.add_error(None, "Credenciais incorretas.")
        return super().form_invalid(form)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("registration.urls")),
    path('register/', include("dojos.urls")),
    path('login/', CustomLoginView.as_view(template_name="dojos/login.html"), name='login'),
    path('logout/', dojo_views.logout_user, name="dojos-logout"),
    path('profile/', dojo_views.profile, name="dojos-profile"),
    ]
