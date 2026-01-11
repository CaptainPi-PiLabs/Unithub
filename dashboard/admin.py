from django.contrib import admin

from dashboard.models import NavShortcut
from core.mixins.admin_mixin import OrderedModelAdminMixin, OrderedAdminMixin


# Register your models here.
@admin.register(NavShortcut)
class NavShortcutAdmin(OrderedModelAdminMixin, OrderedAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'url', 'move_up', 'move_down')
