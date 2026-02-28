from django.contrib import admin
from django.db import transaction
from django.forms import modelform_factory
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html


class BaseTemporalInline(admin.TabularInline):
    extra = 0
    ordering = ("-start_date",)
    show_change_link = True
    classes = ("collapse",)

    date_fields = ("start_date", "end_date")

    def get_max_num(self, request, obj=None, **kwargs):
        return 20

    def view_all_history(self, obj):
        url = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist"
        ) + f"?slot={obj.pk}"

class BaseTemporalAdmin(admin.ModelAdmin):
    change_date_template = "admin/temporal/change_dates.html"
    readonly_fields = ("change_dates_link")
    fields = ("start_date", "end_date", "change_dates_link")

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/change-dates/",
                self.admin_site.admin_view(self.change_dates_view),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_change_dates",
            ),
        ]
        return custom + urls

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        return ()

    def change_dates_view(self, request, object_id):
        obj = self.get_object(request, object_id)

        if request.method == "POST":
            form = self.get_date_change_form(obj, data=request.POST)

            if form.is_valid():
                new_obj = form.save(commit=False)

                clashes = self.model.objects.analyze_clashes(new_obj)

                if not clashes:
                    new_obj.save()
                    self.message_user(request, "Dates updated successfully")
                    return redirect(
                        reverse(
                            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                            args=[obj.pk],
                        )
                    )

                if "confirm" in request.POST:
                    with transaction.atomic():
                        self.model.objects.resolve_by_trimming(new_obj)
                        new_obj.save()

                    self.message_user(request, "Dates updated successfully")

                    return redirect(
                        reverse(
                            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                            args=[obj.pk],
                        )
                    )

                return TemplateResponse(
                    request,
                    self.change_date_template,
                    {
                        "form": form,
                        "object": obj,
                        "clashes": clashes,
                    },
                )
        else:
            form = self.get_date_change_form(obj)

        return TemplateResponse(
            request,
            self.change_date_template,
            {
                "form": form,
                "object": obj,
            },
        )

    def get_date_change_form(self, obj, data=None):
        FormClass = modelform_factory(
            obj.__class__,
            fields=("start_date", "end_date"),
        )
        return FormClass(data=data, instance=obj)

    def change_dates_link(self, obj):
        url = reverse(
            f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change_dates",
            args=[obj.pk],
        )
        return format_html('<a href="{}">Change dates</a>', url)

    change_dates_link.short_description = "Dates"