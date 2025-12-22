from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from django.contrib import messages

class UnitHubBaseView(TemplateView):
    title = "UnitHub"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["show_management"] = user.is_authenticated and user.is_staff

        # Default navigation links
        context["nav_links"] = [
            {"name": "Dashboard", "url": "/"},
            {"name": "ORBAT", "url": "/orbat/"},
            {"name": "Events", "url": "/events/"},
            {"name": "Training", "url": "/training/"},
        ]

        # Default breadcrumbs (can be overridden in child views)
        context.setdefault("breadcrumbs", [])

        context["title"] = self.title
        # Theme can be set in session or user preference
        context["theme"] = getattr(user, "theme", "theme-light")

        return context

    def add_message(self, message, level=messages.INFO):
        """
        Helper to add a message prompt to the user.
        Can be called from any view inheriting this base.
        """
        messages.add_message(self.request, level, message)


class Custom404View(UnitHubBaseView):
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

class Custom403View(UnitHubBaseView):
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
