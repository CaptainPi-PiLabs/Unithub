from orbat.views import ORBATBaseView


class ORBATTimelineView(ORBATBaseView):
    template_name = "orbat_timeline.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["breadcrumbs"] = [
            {"name": "ORBAT", "url": "/orbat/"},
            {"name": "Timeline", "url": None},
        ]

        return context