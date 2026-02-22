from django import forms

from orbat.models.sections import Section


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['name', 'shorthand', 'description', 'max_size', 'platoon']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Optional: make platoon blankable
        self.fields['platoon'].required = False