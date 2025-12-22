from django.contrib.auth.views import LogoutView
from django.urls import path, include

from training.views import UserTrainingView
from .views import *

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("toggle-theme/", toggle_theme, name="toggle_theme"),
    path("profile/", MyProfileView.as_view(), name="my_profile"),
    path("profile/edit/", MyProfileEditView.as_view(), name="my_profile_edit"),
    path("profile/users/", UserListView.as_view(), name="users"),
    path("profile/<uuid:user_id>/", UserProfileView.as_view(), name="user_profile"),
    path("profile/<uuid:user_id>/edit/", UserProfileEditView.as_view(), name="user_profile_edit"),
    path("profile/<uuid:user_id>/timeline/", ORBATTimelineView.as_view(), name="user_timeline"),
    path("profile/<uuid:user_id>/training/", UserTrainingView.as_view(), name="user_profile_training"),
]