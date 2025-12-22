"""
URL configuration for unithub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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

from unithub.views import Custom403View, Custom404View

urlpatterns = [
    path('admin/', admin.site.urls),
    path("orbat/", include("orbat.urls")),
    path("training/", include("training.urls")),
    path("events/", include("events.urls")),
    path("api/", include("apis.urls")),
    path("auth/", include("external_auth.urls")),
    path("", include("users.urls")),
    path("", include("dashboard.urls")),
]

def custom_403(request, exception=None):
    view = Custom403View.as_view()
    return view(request, exception=exception)

def custom_404(request, exception=None):
    view = Custom404View.as_view()
    return view(request, exception=exception)


handler404 = custom_404
handler403 = custom_403