from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin, TabularInline

from orbat.models.sections import SectionSlotAssignment
from permissions.models import PermissionGroupMembership, PermissionGroup
from users.models import CustomUser, MembershipPromotions, UnitMembership


class SectionSlotAssignmentInline(TabularInline):
    model = SectionSlotAssignment
    fk_name = "user"
    classes = ('collapse',)
    extra = 0
    can_delete = False
    ordering = ("-start_date",)

    fields = (
        "section_link",
        "slot",
        "start_date",
        "end_date",
    )

    readonly_fields = fields

    def section_link(self, obj):
        if not obj.slot or not obj.slot.section:
            return "-"
        url = reverse(
            "admin:orbat_section_change",
            args=[obj.slot.section.pk]
        )
        return format_html('<a href="{}">{}</a>', url, obj.slot.section)

    section_link.short_description = "Section"

    def has_add_permission(self, request, obj=None):
        return False


class CustomUserCreationForm(forms.ModelForm):
    """Form for creating new users."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput, required=False)

    class Meta:
        model = CustomUser
        fields = ('display_name', 'username', 'email', 'status', 'is_staff', 'is_active')

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("Passwords don't match")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        if commit:
            user.save()
        return user

class CustomUserChangeForm(forms.ModelForm):
    """Form for updating users."""
    password = ReadOnlyPasswordHashField(label="Password", help_text="Raw passwords are not stored.")

    permission_groups = forms.ModelMultipleChoiceField(
        queryset=PermissionGroup.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("Permission Groups", is_stacked=False),
        label=""
    )

    class Meta:
        model = CustomUser
        fields = ('display_name', 'username', 'email', 'status', 'is_staff', 'is_active', 'password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # pre-fill the user's groups
            self.fields['permission_groups'].initial = PermissionGroup.objects.filter(
                memberships__user=self.instance
            )

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # update memberships
            selected_groups = self.cleaned_data['permission_groups']
            # remove any memberships not in selected_groups
            PermissionGroupMembership.objects.filter(user=user).exclude(group__in=selected_groups).delete()
            # add any new memberships
            existing_group_ids = set(user.group_memberships.values_list('group_id', flat=True))
            for group in selected_groups:
                if group.id not in existing_group_ids:
                    PermissionGroupMembership.objects.create(user=user, group=group)
        return user

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ("username", "is_staff", "is_active")
    inlines = [SectionSlotAssignmentInline,]
    search_fields = (
        "username",
        "display_name",
    )

    fieldsets = (
        (None, {"fields": ("display_name", "username", "unit_membership_link", "discord_account_link", "password", "theme")}),
        ("Orbat", {"fields": ("current_membership_display", "rank", "status")}),
        ("Site Permissions", {
            "classes": ("collapse",),
            "fields": ("is_active", "permission_groups")
        }),
        ("Admin Permissions", {
            "classes": ("collapse",),
            "fields": ("is_staff", "is_superuser", "groups", "user_permissions")
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("display_name", "username", "email", "password1", "password2", "is_staff", "is_active"),
        }),
    )

    readonly_fields = ("is_superuser", "discord_account_link", "unit_membership_link", "current_membership_display")

    def discord_account_link(self, obj):
        discord_account = getattr(obj, "discordaccount_account", None)
        if discord_account:
            url = reverse("admin:external_auth_discordaccount_change", args=[discord_account.pk])
            return format_html('<a href="{}">{}</a>', url, discord_account.username)
        return "-"

    discord_account_link.short_description = "Discord Account"

    def unit_membership_link(self, obj):
        memberships = UnitMembership.get_for_user(obj)
        if not memberships.exists():
            add_url = (reverse("admin:users_unitmembership_add") + f"?user={obj.pk}")
            return format_html('<a class="button" href="{}">Add Membership</a>', add_url)

        links = []

        for membership in memberships:
            url = reverse("admin:users_unitmembership_change", args=[membership.pk])
            links.append((url, membership.date_range_display()))

        return format_html_join(
            mark_safe("<br>"),
            '<a href="{}">{}</a>',
            links
        )

    unit_membership_link.short_description = "Unit Membership"

    def current_membership_display(self, obj):
        return obj.get_current_membership_display()

    current_membership_display.short_description = "Current Membership"


    def display_name(self, obj):
        return str(obj)

    def save_model(self, request, obj, form, change):
        # If no password is set, mark it as unusable
        if not obj.password:
            obj.set_unusable_password()
        super().save_model(request, obj, form, change)

class MembershipPromotionsInline(TabularInline):
    model = MembershipPromotions
    extra = 0
    fields = ("rank", "date_awarded")

@admin.register(UnitMembership)
class UnitMembershipAdmin(ModelAdmin):
    list_display = ("user", "start_date", "end_date")
    inlines = (MembershipPromotionsInline, )
    autocomplete_fields = ("user",)

    search_fields = (
        "user__username",
        "user__display_name",
    )