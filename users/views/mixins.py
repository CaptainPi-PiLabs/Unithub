from users.models import CustomUser


class ProfileContextMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile_id = self.kwargs.get("user_id") or user.id
        context['user_profile'] = CustomUser.objects.filter(id=profile_id).first()

        if user.is_authenticated:
            context["show_management"] = user.is_staff

        context["title"] = "Profile"

        context["sidebar"] = [
            {"name": "Overview", "path": f"/profile/{profile_id}/"},
            {"name": "Training", "path": f"/profile/{profile_id}/training/"},
            # {"name": "Attendance", "path": f"/profile/{profile_id}/attendance/"},
            {"name": "Timeline", "path": f"/profile/{profile_id}/timeline/"},
        ]

        # if context["show_management"]:
        #    context["sidebar"].append({"name": "Management", "path": "/profile/{profile_id}/management/"})

        return context