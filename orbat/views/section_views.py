from django.core.exceptions import PermissionDenied
from django.urls import reverse

from common.views import UnitHubDetailView, UnitHubListView, UnitHubUpdateView
from orbat.enums import OrbatActions
from orbat.forms import SectionForm
from orbat.helpers import get_section_slot_snapshots
from orbat.models.sections import Section
from orbat.permission_helpers import is_eligible_for_section_application
from orbat.selectors import is_user_in_section
from orbat.views.mixins import ORBATContextMixin
from permissions.engine import has_orbat_permission


class ORBATSectionDetailView(ORBATContextMixin, UnitHubDetailView):
    model = Section
    template_name = 'orbat/section_detail.html'
    slug_field = 'slug'
    slug_url_kwarg = 'section_slug'
    context_object_name = 'section'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        section = self.object
        user = self.request.user

        can_manage = has_orbat_permission(user, OrbatActions.MODIFY_SECTION, section)

        context.update({
            "is_member": is_user_in_section(user, section),
            "can_request_join": is_eligible_for_section_application(user),
            "can_edit_section": can_manage,
            "can_manage_slots": can_manage,
        })

        context["breadcrumbs"] = [
            {"name": "ORBAT", "url": "/orbat/"},
            {"name": "Sections", "url": "/orbat/"},
            {"name": section.name, "url": None},
        ]

        context["slot_snapshots"] = get_section_slot_snapshots(section)

        slots_json = {}
        for slot in context["slot_snapshots"]:
            slots_json[slot.id] = {
                "id": slot.id,
                "name": slot.name,
                "colour": slot.colour,
                "is_officer": slot.is_officer,
                "user_id": slot.user.id if slot.user else None,
                "user_display_name": slot.user.display_name if slot.user else None,
            }

        context["slots_json"] = slots_json

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