from django.urls import path, include


urlpatterns = [
    path("orbat/", include("apis.views.orbat.urls")),
    path("training/", include("apis.views.training.urls")),
    path("users/", include("apis.views.users.urls")),
    path("intergrations/", include("apis.views.intergrations.urls")),
]