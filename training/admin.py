from django.contrib import admin

from training.models import QualificationCriterion, Qualification, QualificationEvent, \
    UserQualification


@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(UserQualification)
class UserQualificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'qualification')