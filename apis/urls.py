from django.urls import path, include


urlpatterns = [
    path("arma/", include("apis.views.arma.urls")),
    path("orbat/", include("apis.views.orbat.urls")),
    path("training/", include("apis.views.training.urls")),
    path("users/", include("apis.views.users.urls")),
    path("integration/", include("apis.views.integrations.urls")),
]