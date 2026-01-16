from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, Http404
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from core.views import UnitHubDetailView, UnitHubListView, UnitHubUpdateView, UnitHubCreateView
from orbat.enums import OrbatActions
from orbat.forms import SectionForm
from orbat.models import Section, SectionAssignment, SectionSlot, RoleSlotAssignment
from orbat.permission_helpers import is_eligible_for_section_application
from orbat.utils import get_section_slot_context
from orbat.views import ORBATContextMixin
from permissions.models import PermissionModule
from permissions.engine import has_permission, has_orbat_permission, has_any_permission


class ORBATSectionDetailView(ORBATContextMixin, UnitHubDetailView):
    model = Section
    template_name = 'orbat_section_detail.html'
    slug_field = 'slug'
    slug_url_kwarg = 'section_slug'
    context_object_name = 'section'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        section = self.object
        user = self.request.user

        is_member = SectionAssignment.objects.filter(
            section=section,
            user=user,
            end_date__isnull=True,
        ).exists()

        context.update({
            "is_member": is_member,
            "can_request_join": is_eligible_for_section_application(user),
            "can_edit_section": has_orbat_permission(user, OrbatActions.MODIFY_SECTION, section),
            "can_manage_slots": has_orbat_permission(user, OrbatActions.MODIFY_SECTION, section),
        })

        context["breadcrumbs"] = [
            {"name": "ORBAT", "url": "/orbat/"},
            {"name": "Sections", "url": "/orbat/"},
            {"name": section.name, "url": None},
        ]

        context.update(get_section_slot_context(section))
        return context

class ORBATSectionHistoryView(ORBATContextMixin, UnitHubListView):
    pass

class ORBATSectionEditView(ORBATContextMixin, UnitHubUpdateView):
    model = Section
    form_class = SectionForm
    template_name = "orbat_section_form.html"
    slug_field = 'slug'
    slug_url_kwarg = 'section_slug'
    context_object_name = 'section'

    def dispatch(self, request, *args, **kwargs):
        section = self.get_object()
        if not has_orbat_permission(request.user, OrbatActions.MODIFY_SECTION, section):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("orbat_section_detail", kwargs={"section_slug": self.object.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        section = self.object
        user = self.request.user

        context["can_manage_members"] = has_orbat_permission(user, OrbatActions.MODIFY_SECTION, section)

        context["self_user_id"] = user.id

        context["breadcrumbs"] = [
            {"name": "ORBAT", "url": "/orbat/sections/"},
            {"name": section.name, "url": reverse("orbat_section_detail", kwargs={"section_slug": section.slug})},
            {"name": "Edit", "url": None},
        ]

        return context

class ORBATSectionCreateView(ORBATContextMixin, UnitHubCreateView):
    model = Section
    form_class = SectionForm
    template_name = "orbat_section_form.html"
    context_object_name = 'section'

    def dispatch(self, request, *args, **kwargs):
        if not has_any_permission(request.user, PermissionModule.ORBAT, OrbatActions.CREATE_SECTION):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("orbat_section_detail", kwargs={"section_slug": self.object.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["breadcrumbs"] = [
            {"name": "ORBAT", "url": "/orbat/sections/"},
            {"name": "New Section", "url": None},
        ]

        return context

def get_section_with_permission_check(request, section_slug, permission):
    section = get_object_or_404(Section, slug=section_slug)
    if not has_orbat_permission(request.user, permission, section):
        raise PermissionDenied
    return section

def get_slot_for_section(request, section_slug):
    section = get_section_with_permission_check(request, section_slug, OrbatActions.MODIFY_SECTION)

    slot_id = request.GET.get("slot_id")
    if not slot_id:
        raise Http404("slot_id missing")
    return get_object_or_404(SectionSlot, pk=slot_id, section=section)

def save_section_slot(request, section_slug):
    section = get_section_with_permission_check(request, section_slug, OrbatActions.MODIFY_SECTION)
    slot_id = request.POST.get("slot_id")
    slot = get_object_or_404(SectionSlot, pk=slot_id, section=section) if slot_id else SectionSlot(section=section)

    slot.name = request.POST["name"]
    slot.colour = request.POST.get("colour") or None

    user_id = request.POST.get("user_id")
    slot.user_id = user_id or None
    slot.save()

    # Clear existing roles
    RoleSlotAssignment.objects.filter(
        section_slot=slot,
        end_date__isnull=True
    ).update(end_date=timezone.now())

    # Apply new roles
    role_ids = request.POST.getlist("role_ids")
    rank_id = request.POST.get("rank_id")

    for rid in filter(None, [rank_id, *role_ids]):
        RoleSlotAssignment.objects.create(
            section_slot=slot,
            role_id=rid
        )

    return redirect("orbat_section_detail", section_slug=section.slug)

def remove_section_slot(request, section_slug):
    slot = get_slot_for_section(request, section_slug)
    slot.delete()
    return redirect(request.META.get('HTTP_REFERER', f'/orbat/section/{section_slug}'))


def slot_move_up(request, section_slug):
    slot = get_slot_for_section(request, section_slug)
    slot.move_up()
    return redirect(request.META.get('HTTP_REFERER', f'/orbat/section/{section_slug}'))


def slot_move_down(request, section_slug):
    slot = get_slot_for_section(request, section_slug)
    slot.move_down()
    return redirect(request.META.get('HTTP_REFERER', f'/orbat/section/{section_slug}'))

