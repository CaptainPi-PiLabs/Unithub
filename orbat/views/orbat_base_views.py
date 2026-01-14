from core.views.base import UnitHubBaseView
from orbat.permission_helpers import can_manage_orbat


class ORBATBaseView(UnitHubBaseView):
    title = "Orbat"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            context["show_management"] = can_manage_orbat(user)

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