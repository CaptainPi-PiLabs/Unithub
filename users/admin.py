from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from permissions.models import PermissionGroupMembership, PermissionGroup
from users.models import CustomUser


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
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ("username", "email", "is_staff", "is_active", "date_joined")

    fieldsets = (
        (None, {"fields": ("display_name", "username", "email", "password", "date_joined", "theme")}),
        ("Orbat", {"fields": ("membership", "rank", "section_name", "callsign", "status")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "permission_groups")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("display_name", "username", "email", "password1", "password2", "is_staff", "is_active"),
        }),
    )

    def display_name(self, obj):
        return str(obj)

    def save_model(self, request, obj, form, change):
        # If no password is set, mark it as unusable
        if not obj.password:
            obj.set_unusable_password()
        super().save_model(request, obj, form, change)