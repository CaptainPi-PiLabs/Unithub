from django.urls import path

from orbat.views import *


urlpatterns = [
    path("", ORBATOverviewView.as_view(), name="orbat_overview"),
    path("members/", ORBATMemberView.as_view(), name="orbat_members"),
    path("members/bulk-action", BulkUserActionView.as_view(), name="bulk_user_action"),
    path("timeline/", ORBATTimelineView.as_view(), name="orbat_timeline"),
    path("section/<str:section_name>/", ORBATSectionDetailView.as_view(), name="orbat_section_detail"),
    path("section/<str:section_name>/history/", ORBATSectionHistoryView.as_view(), name="orbat_section_history"),
    path("section/<str:section_name>/edit/", ORBATSectionEditView.as_view(), name="orbat_section_edit"),
    path('section/<str:section_name>/management/slot/<int:slot_id>/moveup/', slot_move_up, name='orbat_section_slot-move-up'),
    path('section/<str:section_name>/management/slot/<int:slot_id>/movedown/', slot_move_down, name='orbat_section_slot-move-down'),
    path("applications/", ORBATApplicationOverview.as_view(), name="orbat_applications"),
    path("applications/onboarding/", UnitApplicationOnboarding.as_view(), name="orbat_applications_onboarding_list"),
    path("applications/onboarding/<int:pk>/", UnitApplicationOnboarding.as_view(), name="orbat_applications_onboarding"),
    path("applications/onboarding/<int:pk>/usermanager/", UnitApplicationUserManager.as_view(), name="orbat_applications_onboarding_usermanager"),
    path("application/loa/<int:section_id>/", ORBATApplicationLOA.as_view(), name="orbat_application_loa"),
    path("application/join/<int:section_id>/", ORBATApplicationJoin.as_view(), name="orbat_application_join"),
]
