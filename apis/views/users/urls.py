from django.urls import path

from apis.views.users.user import UserSearchApi

urlpatterns = [
    path("search/", UserSearchApi.as_view(), name="api-users-search"),
]