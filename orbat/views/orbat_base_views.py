from orbat.models import Section
from core.views.base import UnitHubBaseView


class ORBATBaseView(UnitHubBaseView):
    title = "Orbat"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            context["show_management"] = any(
                user.has_permission("modify", module="orbat", scope=s)
                for s in Section.objects.all()
            ) or user.has_permission("modify", module="orbat", scope=None)

        context["sidebar"] = [
            {"name": "Overview", "path": "/orbat/"},
            {"name": "Sections", "path": "/orbat/sections/"},
            {"name": "Members", "path": "/orbat/members/"},
            {"name": "Timeline", "path": "/orbat/timeline/"},
            {"name": "Applications", "path": "/orbat/applications/"},
        ]

        if context["show_management"]:
            context["sidebar"].append({"name": "Management", "path": "/orbat/management/"})

        return context