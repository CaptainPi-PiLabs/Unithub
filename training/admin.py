from django.contrib import admin

from training.models import Qualification, UserQualification, QualificationCriterion, QualificationTrainer


class QualificationCriteriaInline(admin.TabularInline):
    model = QualificationCriterion
    extra = 0
    fields = ("name", "description", "order")
    ordering = ("order",)

class QualificationTrainerInline(admin.TabularInline):
    model = QualificationTrainer
    extra = 0
    autocomplete_fields = ("user",)

@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)

    inlines = [
        QualificationCriteriaInline,
        QualificationTrainerInline,
    ]

@admin.register(UserQualification)
class UserQualificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'qualification')