from django.urls import path

from apis.views.intergrations.events import *

urlpatterns = [
    path("open/", IntergrationsOpenEventsView.as_view(), name="api-intergrations-open"),
    path("<int:pk>/claim/", IntergrationsClaimEventView.as_view(), name="api-intergrations-claim"),
    path("<int:pk>/success/", IntergrationsSuccessEventView.as_view(), name="api-intergrations-success"),
    path("<int:pk>/error/", IntergrationsErrorEventView.as_view(), name="api-intergrations-error"),
]