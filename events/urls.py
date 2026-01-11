from django.urls import path

from events.views import *


urlpatterns = [
    path("", EventListView.as_view(), name="event_list"),
    path("calendar/", EventCalendarView.as_view(), name="event_calendar"),
    path("campaigns/", CampaignListView.as_view(), name="campaign_list"),
    path("campaigns/<int:pk>/", CampaignDetailView.as_view(), name="campaign_detail"),
    path("<int:pk>/", EventDetailView.as_view(), name="event_detail"),
    path("<int:pk>/manage/", EventManageView.as_view(), name="event_manage"),
]