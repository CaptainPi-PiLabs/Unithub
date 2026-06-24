from django.contrib import admin
from unfold.admin import TabularInline, ModelAdmin

from training.models import Qualification, UserQualification, QualificationCriterion, QualificationTrainer


class QualificationCriteriaInline(TabularInline):
    model = QualificationCriterion
    extra = 0
    fields = ("name", "description", "order")
    ordering = ("order",)

class QualificationTrainerInline(TabularInline):
    model = QualificationTrainer
    extra = 0
    autocomplete_fields = ("user",)

@admin.register(Qualification)
class QualificationAdmin(ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)

    inlines = [
        QualificationCriteriaInline,
        QualificationTrainerInline,
    ]

@admin.register(UserQualification)
class UserQualificationAdmin(ModelAdmin):
    fields = ("user", "qualification", "date_awarded", "latest_passed", "granted_by")
    list_display = ('user', 'qualification')

    search_fields = (
        "user__display_name",
        "qualification__name",
    )

    autocomplete_fields = (
        "user",
        "qualification",
        "granted_by"
    )

    def get_readonly_fields(self, request, obj=None):
        # Only allow edit on a new object
        if obj:
            return ("user", "qualification")
        return ()