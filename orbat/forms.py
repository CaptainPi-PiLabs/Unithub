from django import forms
from django.db.models import Q
from django.utils import timezone

from users.models import CustomUser
from .models import Section, SectionAssignment


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['name', 'shorthand', 'description', 'type', 'max_size', 'platoon', 'leader']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Limit leader choices to active users
        if self.instance.pk:
            # Editing existing section
            active_assignments = SectionAssignment.objects.filter(
                section=self.instance,
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=timezone.now())
            ).select_related('user')
        else:
            # Creating new section (no section yet)
            active_assignments = SectionAssignment.objects.none()

        self.fields['leader'].queryset = CustomUser.objects.filter(
            id__in=[a.user_id for a in active_assignments]
        )
        self.fields['leader'].required = False

        # Optional: make platoon blankable
        self.fields['platoon'].required = False