from django.urls import path

from orbat.views.api_wrappers import *
from orbat.views.applications.onboarding import UnitApplicationOnboarding
from orbat.views.applications.overview import ORBATApplicationOverview
from orbat.views.history_views import ORBATTimelineView
from orbat.views.overview_views import ORBATOverviewView, ORBATMemberView, ORBATSectionListView
from orbat.views.section_views import ORBATSectionDetailView, ORBATSectionHistoryView, ORBATSectionEditView

urlpatterns = [
    # Post mutation endpoints
    path("platoon/create/", create_platoon, name="orbat_platoon_create"),
    path("platoon/<int:pk>/edit/", edit_platoon, name="orbat_platoon_edit"),
    path("platoon/<int:pk>/move/", move_platoon, name="orbat_platoon_move"),
    path("section/create/", create_section, name="orbat_section_create"),
    path("section/<int:section_id>/edit/", edit_section, name="orbat_section_edit"),
    path("section/<int:section_id>/move/", move_section, name="orbat_section_move"),
    path("section/<int:section_id>/slot/create/", create_slot, name="orbat_slot_create"),
    path("section/<int:section_id>/slot/<int:slot_id>/edit/", edit_slot, name="orbat_slot_edit"),

    path("", ORBATOverviewView.as_view(), name="orbat_overview"),
    path("members/", ORBATMemberView.as_view(), name="orbat_members"),
    path("timeline/", ORBATTimelineView.as_view(), name="orbat_timeline"),
    path("sections/", ORBATSectionListView.as_view(), name="orbat_section_list"),
    path("section/<slug:section_slug>/", ORBATSectionDetailView.as_view(), name="orbat_section_detail"),
    path("section/<slug:section_slug>/history/", ORBATSectionHistoryView.as_view(), name="orbat_section_history"),
    path("section/<slug:section_slug>/edit/", ORBATSectionEditView.as_view(), name="orbat_section_edit"),
    path("applications/", ORBATApplicationOverview.as_view(), name="orbat_applications"),
    path("applications/onboarding/", UnitApplicationOnboarding.as_view(), name="orbat_applications_onboarding_list"),
    path("applications/onboarding/<int:pk>/", UnitApplicationOnboarding.as_view(), name="orbat_applications_onboarding"),
]
