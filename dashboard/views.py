from core.decorators import allow_anonymous
from core.views import UnitHubBaseView


@allow_anonymous
class DashboardView(UnitHubBaseView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": None},
        ]

        return context
