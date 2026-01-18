from django.urls import path

from apis.views.orbat.membership import SectionMembershipAPI, SectionLeaveAPI

urlpatterns = [
    path("section/<slug:section_slug>/membership/",SectionMembershipAPI.as_view(),name="api-orbat-section-membership"),
    path("section/<slug:section_slug>/leave/",SectionLeaveAPI.as_view(),name="api-orbat-section-leave"),
]