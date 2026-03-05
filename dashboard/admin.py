from django.contrib import admin
from unfold.admin import ModelAdmin

from dashboard.models import NavShortcut
from common.mixins.admin_mixin import OrderedModelAdminMixin, OrderedAdminMixin


@admin.register(NavShortcut)
class NavShortcutAdmin(OrderedModelAdminMixin, OrderedAdminMixin, ModelAdmin):
    list_display = ('name', 'url', 'move_up', 'move_down')
