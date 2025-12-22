from django.urls import path

from .views import *

urlpatterns = [
    path("orbat/section/<int:section_id>/slot/<int:slot_id>/", SectionSlotAPI.as_view()),
    path("orbat/section/<int:section_id>/slot/", SectionSlotAPI.as_view()),
    path("orbat/section/<int:section_id>/role_options/", SectionRoleOptions.as_view()),
    path("orbat/section/<int:section_id>/members/", SectionMembersAPI.as_view()),
]