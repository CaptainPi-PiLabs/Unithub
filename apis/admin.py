from django.contrib import admin
from unfold.admin import TabularInline, ModelAdmin

from apis.models import UserAPIKey, ServiceAPIKey
from permissions.models import PermissionGrant


class UserPermissionGrantInline(TabularInline):
    model = PermissionGrant
    fk_name = "user_api_key"
    extra = 0
    fields = ("rule", "effect", "content_type", "object_id", "scope_key")

class ServicePermissionGrantInline(TabularInline):
    model = PermissionGrant
    fk_name = "service_api_key"
    extra = 0
    fields = ("rule", "effect", "content_type", "object_id", "scope_key")

@admin.register(UserAPIKey)
class UserAPIKeyAdmin(ModelAdmin):
    list_display = ("user", "name", "active", "last_used_at", "last_used_ip")
    readonly_fields = ("user", "last_used_at", "last_used_ip")
    search_fields = ("user__username", "name")
    list_filter = ("active",)
    inlines = [UserPermissionGrantInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

@admin.register(ServiceAPIKey)
class ServiceAPIKeyAdmin(ModelAdmin):
    list_display = ("name", "created_by", "active", "last_used_at", "last_used_ip")
    readonly_fields = ("last_used_at", "last_used_ip", "created_by")
    search_fields = ("name", "created_by__username")
    list_filter = ("active",)
    inlines = [ServicePermissionGrantInline]

    fieldsets = (
        (None, {
            "fields": ("name", "created_by", "allowed_ips", "active")
        }),
        ("Audit", {
            "fields": ("last_used_at", "last_used_ip"),
            "classes": ("collapse",)
        }),
    )

    def save_model(self, request, obj, form, change):
        # Automatically set the creator if creating a new key
        if not change or not obj.created_by:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)
        if hasattr(obj, "_raw_key"):
            self.message_user(request, f"Service API key generated: {obj._raw_key}")