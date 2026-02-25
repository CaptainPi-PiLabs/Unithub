from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from apis.views.orbat.platoon import PlatoonAPI, PlatoonDetailAPI, MovePlatoonAPI
from apis.views.orbat.section import MoveSectionAPI, SectionAPI, SectionDetailAPI
from apis.views.orbat.slot import SlotDetailAPI, SlotAPI
from apis.views.wrapper import call_api_view
from orbat.models.sections import Section


@require_POST
def create_platoon(request):
    call_api_view(
        PlatoonAPI,
        request,
        success_message="Platoon created."
    )
    return redirect("orbat_section_list")

@require_POST
def edit_platoon(request, pk):
    call_api_view(
        PlatoonDetailAPI,
        request,
        method="PUT",
        pk=pk,
        success_message="Changes saved."
    )
    return redirect("orbat_section_list")

@require_POST
def move_platoon(request, pk):
    call_api_view(
        MovePlatoonAPI,
        request,
        pk=pk
    )
    return redirect("orbat_section_list")

@require_POST
def create_section(request):
    response, success = call_api_view(
        SectionAPI,
        request,
        success_message="Section created."
    )
    if success:
        section_id = response.data["id"]
        section = Section.objects.get(pk=section_id)
        return redirect("orbat_section_detail", section_slug=section.slug)
    return redirect("orbat_section_list")

@require_POST
def edit_section(request, section_id):
    response, success = call_api_view(
        SectionDetailAPI,
        request,
        method="PUT",
        section_id=section_id,
    )
    return redirect("orbat_section_list")

@require_POST
def move_section(request, section_id):
    response, success = call_api_view(
        MoveSectionAPI,
        request,
        section_id = section_id
    )
    section = Section.objects.get(pk=section_id)
    return redirect("orbat_section_detail", section_slug=section.slug)

@require_POST
def create_slot(request, section_id):
    call_api_view(
        SlotAPI,
        request,
        section_id=section_id,
        success_message="Slot created."
    )
    section = Section.objects.get(pk=section_id)
    return redirect("orbat_section_detail", section_slug=section.slug)

@require_POST
def edit_slot(request, section_id, slot_id):
    call_api_view(
        SlotDetailAPI,
        request,
        section_id=section_id,
        slot_id=slot_id,
        method="PUT",
        success_message="Changes saved."
    )
    section = Section.objects.get(pk=section_id)
    return redirect("orbat_section_detail", section_slug=section.slug)