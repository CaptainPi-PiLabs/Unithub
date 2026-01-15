from django.shortcuts import render

from core.views import UnitHubTemplateView


class Custom403View(UnitHubTemplateView):
    template_name = "403.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["page_title"] = "403"

        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": "/"},
            {"name": "403 - Forbidden", "url": None},
        ]

        return context

    def render_to_response(self, context, **response_kwargs):
        return render(self.request, self.template_name, context, status=403)

class Custom404View(UnitHubTemplateView):
    template_name = "404.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["page_title"] = "404"

        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": "/"},
            {"name": "404 - Not Found", "url": None},
        ]

        return context

    def render_to_response(self, context, **response_kwargs):
        return render(self.request, self.template_name, context, status=404)

class Custom503View(UnitHubTemplateView):
    template_name = "503.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["page_title"] = "503"

        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": "/"},
            {"name": "503 - Unavailable", "url": None},
        ]

        return context