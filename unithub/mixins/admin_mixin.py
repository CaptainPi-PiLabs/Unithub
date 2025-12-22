from django.db import models
from django.db.models import Max
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from rest_framework.generics import get_object_or_404


class OrderedModelAdminMixin:
    def move_up(self, obj):
        if not obj.pk:
            return "-"
        url = reverse(
            f"admin:{obj._meta.app_label}_{obj._meta.model_name}-move-up",
            args=[obj.pk],
        )
        return mark_safe(f'<a href="{url}">⬆️</a>')
    move_up.short_description = "Move Up"

    def move_down(self, obj):
        if not obj.pk:
            return "-"
        url = reverse(
            f"admin:{obj._meta.app_label}_{obj._meta.model_name}-move-down",
            args=[obj.pk],
        )
        return mark_safe(f'<a href="{url}">⬇️</a>')
    move_down.short_description = "Move Down"


class OrderedAdminMixin:
    """
    Adds move_up/move_down admin actions for models
    that have an `order` field.
    """
    move_redirect = None

    def get_urls(self):
        urls = super().get_urls()
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        custom_urls = [
            path(
                "<int:object_id>/move_up/",
                self.admin_site.admin_view(self.move_up_view),
                name=f"{app_label}_{model_name}-move-up",
            ),
            path(
                "<int:object_id>/move_down/",
                self.admin_site.admin_view(self.move_down_view),
                name=f"{app_label}_{model_name}-move-down",
            ),
        ]

        return custom_urls + urls

    def move_up_view(self, request, object_id):
        obj = get_object_or_404(self.model, pk=object_id)
        obj.move_up()
        return self._redirect_back(obj)

    def move_down_view(self, request, object_id):
        obj = get_object_or_404(self.model, pk=object_id)
        obj.move_down()
        return self._redirect_back(obj)

    def _redirect_back(self, obj):
        if self.move_redirect:
            parent = getattr(obj, self.move_redirect)
            parent_meta = parent._meta
            return redirect(reverse(f"admin:{parent_meta.app_label}_{parent_meta.model_name}_change",args=[parent.pk],))
        opts = obj._meta
        return redirect(reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist"))
