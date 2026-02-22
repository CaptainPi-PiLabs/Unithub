from django.urls import path

from apis.views.orbat.platoon import *
from apis.views.orbat.section import *
from apis.views.orbat.slot import *
from apis.views.orbat.unitapplication import UnitApplicationAPI

urlpatterns = [
    path("platoon/", PlatoonAPI.as_view(), name="api-orbat-platoon"),
    path("platoon/<int:pk>/", PlatoonDetailAPI.as_view(), name="api-orbat-platoon-detail"),
    path("platoon/<int:pk>/move/", PlatoonAPI.as_view(), name="api-orbat-platoon-move"),
    path("section/", SectionAPI.as_view(), name="api-orbat-section"),
    path("section/<int:section_id>/", SectionDetailAPI.as_view(), name="api-orbat-section-detail"),
    path("section/<int:section_id>/move/", MoveSectionAPI.as_view(), name="api-orbat-section"),
    path("section/<int:section_id>/slot/", SlotAPI.as_view(), name="api-orbat-section-slot"),
    path("section/<int:section_id>/slot/<int:slot_id>detail", SlotDetailAPI.as_view(), name="api-orbat-section-slot"),
    path("unitapplication/", UnitApplicationAPI.as_view(), name="api-orbat-unitapplication"),
]