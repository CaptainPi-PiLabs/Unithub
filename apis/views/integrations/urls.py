from django.urls import path

from apis.views.integrations.events import *

urlpatterns = [
    path("open/", IntegrationsOpenEventsView.as_view(), name="api-integrations-open"),
    path("<int:pk>/claim/", IntegrationsClaimEventView.as_view(), name="api-integrations-claim"),
    path("<int:pk>/success/", IntegrationsSuccessEventView.as_view(), name="api-integrations-success"),
    path("<int:pk>/error/", IntegrationsErrorEventView.as_view(), name="api-integrations-error"),
]