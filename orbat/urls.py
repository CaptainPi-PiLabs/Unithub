from django.urls import path

from orbat.views import *
from orbat.views.platoon_views import ORBATPlatoonCreate

urlpatterns = [
    path("", ORBATOverviewView.as_view(), name="orbat_overview"),
    path("members/", ORBATMemberView.as_view(), name="orbat_members"),
    path("members/bulk-action", BulkUserActionView.as_view(), name="bulk_user_action"),
    path("timeline/", ORBATTimelineView.as_view(), name="orbat_timeline"),
    path("sections/", ORBATSectionListView.as_view(), name="orbat_section_list"),
    path("sections/create/", ORBATSectionCreateView.as_view(), name="orbat_section_create"),
    path("section/<slug:section_slug>/", ORBATSectionDetailView.as_view(), name="orbat_section_detail"),
    path("section/<slug:section_slug>/history/", ORBATSectionHistoryView.as_view(), name="orbat_section_history"),
    path("section/<slug:section_slug>/edit/", ORBATSectionEditView.as_view(), name="orbat_section_edit"),
    path("section/<slug:section_slug>/slot_save/", save_section_slot, name="orbat_section_slot_save"),
    path("section/<slug:section_slug>/slot_remove/", remove_section_slot, name="orbat_section_slot_remove"),
    path('section/<slug:section_slug>/slot_move_up/', slot_move_up, name='orbat_section_slot-move-up'),
    path('section/<slug:section_slug>/slot_move_down/', slot_move_down, name='orbat_section_slot-move-down'),
    path("applications/", ORBATApplicationOverview.as_view(), name="orbat_applications"),
    path("applications/onboarding/", UnitApplicationOnboarding.as_view(), name="orbat_applications_onboarding_list"),
    path("applications/onboarding/<int:pk>/", UnitApplicationOnboarding.as_view(), name="orbat_applications_onboarding"),
    path("applications/onboarding/<int:pk>/usermanager/", UnitApplicationUserManager.as_view(), name="orbat_applications_onboarding_usermanager"),
    path("application/loa/<int:section_id>/", ORBATApplicationLOA.as_view(), name="orbat_application_loa"),
    path("application/join/<int:section_id>/", ORBATApplicationJoin.as_view(), name="orbat_application_join"),
    path("platoon/create", ORBATPlatoonCreate.as_view(), name="orbat_platoon_create"),
]
