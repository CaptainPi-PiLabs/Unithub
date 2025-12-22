from django.shortcuts import get_object_or_404, redirect

from dashboard.models import NavShortcut
from unithub.views import UnitHubBaseView


class DashboardView(UnitHubBaseView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": None},
        ]

        return context
