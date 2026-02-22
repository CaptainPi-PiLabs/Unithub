from django import forms
from django.apps import apps
from django.contrib import admin
from django.contrib.auth.models import Permission, Group
from django.utils.html import format_html

from .models import PermissionGroup, PermissionGrant, PermissionGroupMembership

# -----------------------------
# Inlines
# -----------------------------

class MembershipInline(admin.TabularInline):
    model = PermissionGroupMembership
    extra = 1
    autocomplete_fields = ["user"]

# Form for PermissionGrant to handle object vs key
class PermissionGrantForm(forms.ModelForm):
    class Meta:
        model = apps.get_model("permissions", "PermissionGrant")
        fields = [
            "rule",
            "effect",
            "content_type",
            "object_id",
            "scope_key",
            "group",
        ]

    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get("content_type")
        object_id = cleaned_data.get("object_id")
        scope_key = cleaned_data.get("scope_key")

        if (content_type or object_id) and scope_key:
            raise forms.ValidationError("You can only set either an object OR a scope key, not both.")
        if object_id and not content_type:
            raise forms.ValidationError("object ID requires a object type.")
        return cleaned_data

class PermissionGrantInline(admin.TabularInline):
    model = PermissionGrant
    form = PermissionGrantForm
    extra = 1
    fields = (
        "rule",
        "effect",
        "content_type",
        "object_id",
        "scope_key",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Only show grants for this group
        if hasattr(self, 'parent_object'):
            return qs.filter(group=self.parent_object)
        return qs

    def get_formset(self, request, obj=None, **kwargs):
        self.parent_object = obj  # save the parent group instance
        return super().get_formset(request, obj, **kwargs)

@admin.register(PermissionGrant)
class PermissionGrantAdmin(admin.ModelAdmin):
    form = PermissionGrantForm
    list_display = ("subject_display", "rule", "module", "get_scope_name", "effect")
    list_filter = ("rule__module", "effect", "group")
    search_fields = ("rule__action", "group__name", "scope_key")

    def module(self, obj):
        return obj.rule.module
    module.admin_order_field = "rule__module"

    def subject_display(self, obj):
        """Display the subject of the grant in a human-readable way."""
        if obj.user:
            return format_html('<strong>User:</strong> {}', obj.user)
        if obj.group:
            return format_html('<strong>Group:</strong> {}', obj.group)
        if obj.user_api_key:
            return format_html('<strong>User API Key:</strong> {}', obj.user_api_key.name)
        if obj.service_api_key:
            return format_html('<strong>Service API Key:</strong> {}', obj.service_api_key.name)
        return "-"
    subject_display.short_description = "Subject"

    def get_scope_name(self, obj):
        if obj.content_type and obj.object_id:
            return str(obj.content_type.get_object_for_this_type(id=obj.object_id))
        if obj.scope_key:
            return obj.scope_key
        return "Global"
    get_scope_name.short_description = "Scope"

@admin.register(PermissionGroupMembership)
class PermissionGroupMembershipAdmin(admin.ModelAdmin):
    list_display = ["user_link", "group_link"]
    list_filter = ["group"]
    search_fields = ["user__username", "user__display_name", "group__name"]

    def user_link(self, obj):
        return format_html('<a href="/admin/users/customuser/{}/change/">{}</a>', obj.user.id, obj.user)

    user_link.short_description = "User"
    user_link.admin_order_field = "user"

    def group_link(self, obj):
        return format_html('<a href="/admin/permissions/permissiongroup/{}/change/">{}</a>', obj.group.id, obj.group)

    group_link.short_description = "Group"
    group_link.admin_order_field = "group"

@admin.register(PermissionGroup)
class PermissionGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "member_count", "permission_count"]
    inlines = [MembershipInline, PermissionGrantInline]

    def member_count(self, obj):
        return obj.memberships.count()
    member_count.short_description = "Members"

    def permission_count(self, obj):
        return obj.grants.count()
    permission_count.short_description = "Permissions"