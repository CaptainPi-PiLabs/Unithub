from django.urls import path, include


urlpatterns = [
    path("orbat/", include("apis.views.orbat.urls")),
    path("training/", include("apis.views.training.urls")),
]