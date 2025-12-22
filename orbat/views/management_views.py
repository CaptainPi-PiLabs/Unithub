from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator

from orbat.models import Section, SectionSlot
from orbat.views.orbat_base_views import ORBATBaseView


@method_decorator(login_required, name="dispatch")
class ORBATManagementOverviewView(ORBATBaseView):
    template_name = "orbat/orbat_management_overview.html"

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if not user.is_staff:
            # check if user owns any sections
            owned_sections = Section.objects.filter(leader=user)
            if owned_sections.exists():
                # redirect straight to first owned section
                return redirect(f"/orbat/management/{owned_sections.first().name}/")
            messages.error(request, "You don't have access to ORBAT management.")
            return redirect("/orbat/")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"name": "ORBAT", "url": "/orbat/"},
            {"name": "Management", "url": None},
        ]
        context["sections"] = Section.objects.all()
        context["show_create"] = True
        return context

@method_decorator(login_required, name="dispatch")
class ORBATSectionManagementView(ORBATBaseView):
    template_name = "orbat/orbat_management_section.html"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        section_name = kwargs.get("section_name")
        section = Section.objects.filter(name=section_name).first()
        if not section:
            messages.error(request, f"Section '{section_name}' not found.")
            return redirect("/orbat/")

        # Only admin or section owner can access
        if not user.is_staff and section.leader != user:
            return redirect("/")  # or raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": "/"},
            {"name": "ORBAT", "url": "/orbat/"},
            {"name": "Management", "url": "/orbat/management/"},
            {"name": self.section.name, "url": None},
        ]
        context["section"] = self.section
        return context


def slot_move_up(request, section_name, slot_id):
    slot = get_object_or_404(SectionSlot, pk=slot_id)
    slot.move_up()
    return redirect(request.META.get('HTTP_REFERER', f'/orbat/section/{section_name}/management/'))

def slot_move_down(request, section_name, slot_id):
    slot = get_object_or_404(SectionSlot, pk=slot_id)
    slot.move_down()
    return redirect(request.META.get('HTTP_REFERER', f'/orbat/section/{section_name}/management/'))
