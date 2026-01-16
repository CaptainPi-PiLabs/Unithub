from django import forms

from training.models import Qualification, QualificationCriterion


class QualificationForm(forms.ModelForm):
    class Meta:
        model = Qualification
        fields = ["name", "description", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "class": "w-full border rounded p-2"}),
            "name": forms.TextInput(attrs={"class": "w-full border rounded p-2"}),
            "is_active": forms.CheckboxInput(attrs={"class": "h-4 w-4"}),
        }

class QualificationCriterionForm(forms.ModelForm):
    class Meta:
        model = QualificationCriterion
        fields = ["name", "description", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "w-full border rounded p-2"}),
            "description": forms.Textarea(attrs={"rows": 2, "class": "w-full border rounded p-2"}),
            "order": forms.NumberInput(attrs={"class": "w-20 border rounded p-1"}),
        }