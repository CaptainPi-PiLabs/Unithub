from django import forms
from django.contrib import admin
from django.contrib.auth.models import Permission, Group
from django.utils.html import format_html

from .models import PermissionGroup, PermissionGrant, PermissionGroupMembership


for model in [Permission, Group]:
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass

class MembershipInline(admin.TabularInline):
    model = PermissionGroupMembership
    extra = 1
    autocomplete_fields = ["user"]

# Form for PermissionGrant to handle object vs key
class PermissionGrantForm(forms.ModelForm):
    class Meta:
        model = PermissionGrant
        fields = [
            "group",
            "permission",
            "module",
            "effect",
            "content_type",
            "object_id",
            "scope_key",
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
        "permission",
        "module",
        "effect",
        "content_type",
        "object_id",
        "scope_key",
    )
    # autocomplete_fields = ["content_type"]  # optional, for easier selection

@admin.register(PermissionGrant)
class PermissionGrantAdmin(admin.ModelAdmin):
    form = PermissionGrantForm
    list_display = ("group", "permission", "module", "get_scope_name", "effect")
    list_filter = ("module", "effect", "group")
    search_fields = ("permission", "group__name", "scope_key")

    def get_scope_name(self, obj):
        if obj.content_object:
            return str(obj.content_object)
        elif obj.scope_key:
            return obj.scope_key
        return "-"
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