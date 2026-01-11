from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.contrib.auth import get_user_model
from django.forms import ModelForm, ModelChoiceField, Form
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils.html import format_html

from orbat.models import *
from core.mixins.admin_mixin import OrderedModelAdminMixin, OrderedAdminMixin


User = get_user_model()

class EndDateFilter(SimpleListFilter):
    title = "End Date"
    parameter_name = "end_date_status"

    def lookups(self, request, model_admin):
        return (
            ("empty", "Active"),
            ("set", "Old Assignment"),
        )

    def queryset(self, request, queryset):
        if self.value() == "empty":
            return queryset.filter(end_date__isnull=True)
        if self.value() == "set":
            return queryset.filter(end_date__isnull=False)
        return queryset

class SectionInLine(OrderedModelAdminMixin, admin.TabularInline):
    model = Section
    fields = ["name", "max_size", "leader", "move_up", "move_down", "edit_link"]
    readonly_fields = ["leader", "move_up", "move_down", "edit_link"]
    can_delete = False
    extra = 0

    def edit_link(self, obj):
        if obj.pk:
            url = reverse(
                f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
                args = [obj.pk],
            )
            return format_html('<a href="{}">Edit</a>', url)
        return "-"
    edit_link.short_description = ""

class SectionAdminForm(ModelForm):
    class Meta:
        model = Section
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "leader" in self.fields:
            section = getattr(self.instance, "pk", None)
            if section:
                self.fields["leader"].queryset = SectionAssignment.objects.filter(
                    section=self.instance,
                    end_date__isnull=True
                ).select_related("user").values_list("user", flat=True)
                # Set queryset to actual users
                from django.contrib.auth import get_user_model
                self.fields["leader"].queryset = User.objects.filter(pk__in=self.fields["leader"].queryset)
            else:
                self.fields["leader"].queryset = SectionAssignment.objects.none()

class AssignSectionUserForm(Form):
    user = ModelChoiceField(queryset=User.objects.none(), label="Select User")


class SectionSlotInlineForm(ModelForm):
    class Meta:
        model = SectionSlot
        fields = ['name', 'user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        slot = getattr(self.instance, 'pk', None)
        if slot:
            section = self.instance.section
            # Only show users currently assigned to the section
            active_user_ids = SectionAssignment.objects.filter(
                section=section,
                end_date__isnull=True
            ).values_list('user_id', flat=True)
            self.fields['user'].queryset = User.objects.filter(pk__in=active_user_ids)
        else:
            self.fields['user'].queryset = User.objects.none()

class SectionSlotInline(OrderedModelAdminMixin, admin.TabularInline):
    model = SectionSlot
    form = SectionSlotInlineForm
    fields = ['name', 'colour', 'user', 'move_up', 'move_down']
    readonly_fields = ['move_up', 'move_down']
    extra = 0
    can_delete = False

#TODO Add RoleSlotAssignmentInlineForm to limit selection of section slots. Only one rank etc

class RoleSlotAssignementInline(admin.TabularInline):
    model = RoleSlotAssignment
    fields = ['section_slot']
    extra = 0
    can_delete = False


@admin.register(Platoon)
class PlatoonAdmin(OrderedModelAdminMixin, OrderedAdminMixin, admin.ModelAdmin):
    fields = ["name", "description"]
    list_display = ("name", "move_up", "move_down")
    readonly_fields = ["move_up", "move_down"]
    inlines = (SectionInLine,)

@admin.register(Section)
class SectionAdmin(OrderedAdminMixin, admin.ModelAdmin):
    list_display = ("name", "order", "platoon", "leader", "max_size",)
    list_filter = ("platoon",)
    search_fields = ("name",)
    move_redirect = "platoon"
    inlines = [SectionSlotInline,]
    form = SectionAdminForm
    change_form_template = "admin/section_change_form.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:section_id>/remove_assignment/<uuid:user_id>/",
                self.admin_site.admin_view(self.remove_assignment),
                name="orbat_section-remove-assignment",
            ),
            path(
                "<int:section_id>/add_assignment/",
                self.admin_site.admin_view(self.add_assignment),
                name="orbat_section-add-assignment",
            ),
        ]
        return custom_urls + urls

    def change_view(self, request, object_id=None, form_url=None, extra_context=None):
        extra_context = extra_context or {}
        section = None
        active_count = 0
        if object_id:
            section = Section.objects.get(pk=object_id)
            active_count = SectionAssignment.objects.filter(
                section=section,
                end_date__isnull=True
            ).count()
        extra_context['active_assignment_count'] = active_count
        extra_context['section'] = section
        return super().changeform_view(request, object_id, form_url, extra_context=extra_context)

    def remove_assignment(self, request, section_id, user_id):
        assignment = get_object_or_404(SectionAssignment, section_id=section_id, user_id=user_id)
        assignment.end_date = timezone.now()
        assignment.save(update_fields=["end_date"])
        messages.success(request, f"Removed {assignment.user} from section.")
        return redirect(request.META.get("HTTP_REFERER", f"/admin/app/section/{section_id}/change/"))

    def add_assignment(self, request, section_id):
        section = get_object_or_404(Section, pk=section_id)
        active_count = SectionAssignment.objects.filter(section=section, end_date__isnull=True).count()

        if active_count >= section.max_size:
            messages.warning(request, "Section is full, cannot add more users.")
            return redirect(f"/admin/orbat/section/{section_id}/change/")

        active_user_ids = SectionAssignment.objects.filter(
            end_date__isnull=True
        ).values_list("user_id", flat=True)
        eligible_users = User.objects.exclude(pk__in=active_user_ids)

        if request.method == "POST":
            form = AssignSectionUserForm(request.POST)
            form.fields["user"].queryset = eligible_users
            if form.is_valid():
                user = form.cleaned_data["user"]
                SectionAssignment.objects.create(
                    section=section,
                    user=user,
                    start_date=timezone.now()
                )
                messages.success(request, f"Added {user} to section.")
                return redirect(f"/admin/orbat/section/{section_id}/change/")
        else:
            form = AssignSectionUserForm()
            form.fields["user"].queryset = eligible_users

        return self.render_add_user_form(request, form, section)

    def render_add_user_form(self, request, form, section):
        # Simple template rendering
        from django.template.response import TemplateResponse
        return TemplateResponse(
            request,
            "admin/section_add_user.html",
            {"form": form, "section": section}
        )

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name",)
    inlines = (RoleSlotAssignementInline,)

@admin.register(SectionAssignment)
class SectionAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "section", "start_date", "end_date",)
    list_filter = ("section",EndDateFilter)
    search_fields = ("user__username",)

@admin.register(SectionSlot)
class SectionSlotAdmin(OrderedAdminMixin, admin.ModelAdmin):
    move_redirect = "section"
    def has_module_permission(self, request):
        return False

@admin.register(RoleSlotAssignment)
class RoleSlotAssignmentAdmin(admin.ModelAdmin):
    list_display = ("display_name", "role", "section_slot", "start_date", "end_date",)

    def display_name(self, obj):
        return f"{obj.section_slot} ({obj.role})"

@admin.register(UnitApplication)
class UnitApplicationAdmin(admin.ModelAdmin):
    list_display = ("external_account", "user", "date", "actioned_by", "denied")

@admin.register(SectionApplication)
class SectionApplicationAdmin(admin.ModelAdmin):
    pass