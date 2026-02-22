from django.conf import settings
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib import messages


class UnitHubContextMixin:
    title = "Unit Hub"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["theme"] = getattr(user, "theme", "theme-light")

        nav_links = [
            {"name": "Dashboard", "url": "/"},
            {"name": "ORBAT", "url": "/orbat/"},
            {"name": "Events", "url": "/events/"},
            {"name": "Training", "url": "/training/"},
        ]

        if not getattr(settings, "ENABLE_EVENTS", False):
            nav_links = [l for l in nav_links if l["name"] != "Events"]
        if not getattr(settings, "ENABLE_TRAINING", False):
            nav_links = [l for l in nav_links if l["name"] != "Training"]

        context["nav_links"] = nav_links
        context.setdefault("breadcrumbs", [])
        context["title"] = getattr(self, "title", "UnitHub")

        return context

    def add_message(self, message, level=messages.INFO):
        """
        Helper to add a message prompt to the user.
        Can be called from any view inheriting this base.
        """
        messages.add_message(self.request, level, message)

class UnitHubTemplateView(UnitHubContextMixin, TemplateView):
    pass

class UnitHubListView(UnitHubContextMixin, ListView):
    pass

class UnitHubDetailView(UnitHubContextMixin, DetailView):
    pass

class UnitHubCreateView(UnitHubContextMixin, CreateView):
    pass

class UnitHubUpdateView(UnitHubContextMixin, UpdateView):
    pass