from django.contrib import admin
from django.db.models import Max
from django.shortcuts import redirect, get_object_or_404
from django.utils.html import format_html

from dashboard.models import NavShortcut
from unithub.mixins.admin_mixin import OrderedModelAdminMixin, OrderedAdminMixin


# Register your models here.
@admin.register(NavShortcut)
class NavShortcutAdmin(OrderedModelAdminMixin, OrderedAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'url', 'move_up', 'move_down')
