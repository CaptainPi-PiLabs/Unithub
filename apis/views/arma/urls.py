from django.urls import path

from apis.views.arma.check_player import ArmaCheckPlayerAPI
from apis.views.arma.whitelist import ArmaGetWhitelistAPI

urlpatterns = [
    path("check/", ArmaCheckPlayerAPI.as_view(), name="api-arma-check-player"),
    path("whitelist/", ArmaGetWhitelistAPI.as_view(), name="api-arma-get-whitelist"),
]