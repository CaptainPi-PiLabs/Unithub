from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator

from common.views import UnitHubTemplateView, UnitHubDetailView
from orbat.models.sections import Section
from orbat.views.mixins import ORBATContextMixin


@method_decorator(login_required, name="dispatch")
class ORBATManagementOverviewView(ORBATContextMixin, UnitHubTemplateView):
    template_name = "orbat/management_overview.html"
    breadcrumbs = [
        ("ORBAT", "/orbat/"),
        ("Management", None),
    ]

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
        context["sections"] = Section.objects.all()
        context["show_create"] = True
        return context

@method_decorator(login_required, name="dispatch")
class ORBATSectionManagementView(ORBATContextMixin, UnitHubDetailView):
    template_name = "orbat/management_section.html"

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

    def get_breadcrumbs(self):
        section = self.section
        return self.build_breadcrumbs(
            ("Dashboard", "/"),
            ("ORBAT", "/orbat/"),
            ("Management", "/orbat/management/"),
            (section.name, None)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["section"] = self.section
        return context
