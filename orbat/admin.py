from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.contrib.auth import get_user_model
from django.forms import ModelChoiceField, Form
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from common.mixins.admin_mixin import OrderedModelAdminMixin, OrderedAdminMixin
from common.temporal.admin import BaseTemporalInline, BaseTemporalAdmin
from orbat.models.sections import Section, Platoon, SectionSlotAssignment, SectionSlot, SectionSlotDetail
from orbat.models.unit import UnitApplication


User = get_user_model()

class SectionInLine(OrderedModelAdminMixin, admin.TabularInline):
    model = Section
    fields = ["name", "max_size", "move_up", "move_down", "edit_link"]
    readonly_fields = ["move_up", "move_down", "edit_link"]
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

class SectionSlotInline(admin.TabularInline):
    model = SectionSlot
    extra = 0
    can_delete = False
    show_change_link = True
    template = "admin/temporal/tabular_inline.html"

    fields = ("slot_name", "current_user")
    readonly_fields = ("slot_name", "current_user")

    def slot_name(self, obj):
        return obj.get_name()

    slot_name.short_description = "Slot"

    def current_user(self, obj):
        assignment = obj.get_assignment_at()
        return assignment.user if assignment else "—"

@admin.register(Platoon)
class PlatoonAdmin(OrderedModelAdminMixin, OrderedAdminMixin, admin.ModelAdmin):
    fields = ["name", "description"]
    list_display = ("name", "move_up", "move_down")
    readonly_fields = ["move_up", "move_down"]
    inlines = (SectionInLine,)


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


class AssignSectionUserForm(Form):
    user = ModelChoiceField(queryset=User.objects.none(), label="Select User")

@admin.register(Section)
class SectionAdmin(OrderedAdminMixin, admin.ModelAdmin):
    list_display = ("name", "order", "platoon", "max_size")
    list_filter = ("platoon",)
    search_fields = ("name",)
    inlines = [SectionSlotInline]

    change_form_template = "admin/section_change_form.html"

    def change_view(self, request, object_id=None, form_url=None, extra_context=None):
        extra_context = extra_context or {}
        section = Section.objects.get(pk=object_id)
        active_count = SectionSlotAssignment.objects.filter(
            slot__section=section,
            end_date__isnull=True
        ).count()
        extra_context.update({
            "active_assignment_count": active_count,
            "section": section
        })
        return super().changeform_view(request, object_id, form_url, extra_context=extra_context)

    def remove_assignment(self, request, section_id, user_id):
        assignment = get_object_or_404(
            SectionSlotAssignment,
            slot__section_id=section_id,
            user_id=user_id,
            end_date__isnull=True
        )
        assignment.end_date = timezone.now()
        assignment.save(update_fields=["end_date"])
        messages.success(request, f"Removed {assignment.user} from section.")
        return redirect(request.META.get("HTTP_REFERER"))

    def add_assignment(self, request, section_id):
        section = get_object_or_404(Section, pk=section_id)
        active_count = SectionSlotAssignment.objects.filter(
            slot__section=section,
            end_date__isnull=True
        ).count()
        if active_count >= section.max_size:
            messages.warning(request, "Section is full, cannot add more users.")
            return redirect(request.META.get("HTTP_REFERER"))

        active_user_ids = SectionSlotAssignment.objects.filter(
            end_date__isnull=True
        ).values_list("user_id", flat=True)
        eligible_users = User.objects.exclude(pk__in=active_user_ids)

        if request.method == "POST":
            form = AssignSectionUserForm(request.POST)
            form.fields["user"].queryset = eligible_users
            if form.is_valid():
                user = form.cleaned_data["user"]
                # Assign user to an empty slot automatically
                empty_slot = section.slots.filter(user__isnull=True).first()
                if empty_slot:
                    SectionSlotAssignment.objects.create(
                        slot=empty_slot,
                        user=user,
                        start_date=timezone.now()
                    )
                    messages.success(request, f"Added {user} to section.")
                else:
                    messages.warning(request, "No empty slot available in this section.")
                return redirect(request.META.get("HTTP_REFERER"))
        else:
            form = AssignSectionUserForm()
            form.fields["user"].queryset = eligible_users

        return self.render_add_user_form(request, form, section)

    def render_add_user_form(self, request, form, section):
        from django.template.response import TemplateResponse
        return TemplateResponse(
            request,
            "admin/section_add_user.html",
            {"form": form, "section": section}
        )


class SectionSlotDetailInline(BaseTemporalInline):
    model = SectionSlotDetail
    fields = ("name", "colour", "is_officer", "start_date", "end_date")
    list_display = ("name", "colour", "is_officer", "start_date", "end_date", "change_dates_link")

class SectionSlotAssignmentInline(BaseTemporalInline):
    model = SectionSlotAssignment
    fields = ("user","start_date", "end_date")
    autocomplete_fields = ("user__username",)

@admin.register(SectionSlot)
class SectionSlotAdmin(admin.ModelAdmin):
    list_display = ("section", "current_name", "is_leader")
    readonly_fields = ("section","is_leader")

    inlines = [
        SectionSlotDetailInline,
        SectionSlotAssignmentInline,
    ]

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_leader:
            return False
        return super().has_delete_permission(request, obj)

    @admin.display(description="Name")
    def current_name(self, obj):
        return obj.get_name() or "—"

@admin.register(SectionSlotDetail)
class SectionSlotDetailAdmin(BaseTemporalAdmin):
    fields = ("slot", "name", "colour", "is_officer", "start_date", "end_date", "change_dates_link")
    readonly_fields = ("slot", "start_date", "end_date", "change_dates_link",)
    list_display = ("name", "start_date", "end_date", "change_dates_link")

@admin.register(SectionSlotAssignment)
class SectionSlotAssignmentAdmin(BaseTemporalAdmin):
    list_display = ("user", "start_date", "end_date", "change_dates_link")

    fields = (
        "slot",
        "user",
        "first_joined",
        "start_date",
        "end_date",
        "change_dates_link",
    )

    readonly_fields = (
        "first_joined",
        "change_dates_link",
    )

@admin.register(UnitApplication)
class UnitApplicationAdmin(admin.ModelAdmin):
    list_display = ("external_account", "user", "date", "actioned_by", "status")
