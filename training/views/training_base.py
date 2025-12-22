from unithub.views import UnitHubBaseView


class TrainingBaseView(UnitHubBaseView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["show_management"] = user.is_authenticated and user.is_staff

        context["title"] = "Training"

        context["sidebar"] = [
            {"name": "Overview", "path": "/training/"},
            {"name": "Matrix", "path": "/training/matrix/"},
            {"name": "Events", "path": "/events/training/"},
        ]

        if context["show_management"]:
            context["sidebar"].append({"name": "Management", "path": "/training/management/"})

        return context