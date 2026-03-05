from core.access.decorators import allow_anonymous
from common.views import UnitHubTemplateView


@allow_anonymous
class DashboardView(UnitHubTemplateView):
    template_name = 'dashboard/dashboard.html'
    breadcrumbs = [
        ("Dashboard", None),
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context
