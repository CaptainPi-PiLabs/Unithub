from orbat.helpers import get_section_for_user
from orbat.permission_helpers import can_manage_orbat


class ORBATContextMixin:
    title = "ORBAT"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["show_management"] = (
            user.is_authenticated and can_manage_orbat(user)
        )

        sidebar = [
            {"name": "Overview", "path": "/orbat/"},
            {"name": "Sections", "path": "/orbat/sections/"},
            {"name": "Members", "path": "/orbat/members/"},
            # {"name": "Timeline", "path": "/orbat/timeline/"},
            {"name": "Applications", "path": "/orbat/applications/"},
        ]

        section = get_section_for_user(user)
        if section:
            sidebar.append(
                {"name": f"{section.name} Section Home", "path": "/orbat/section/" + section.slug + "/"}
            )

        if context["show_management"]:
            sidebar.append(
                {"name": "Management", "path": "/orbat/management/"}
            )

        context["sidebar"] = sidebar
        context["title"] = getattr(self, "title", "ORBAT")

        return context