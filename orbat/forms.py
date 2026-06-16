from datetime import date
from zoneinfo import available_timezones

from django import forms

from orbat.models.sections import Section
from orbat.models.unit import UnitApplicationQuestionnaire


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['name', 'shorthand', 'description', 'max_size', 'platoon']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Optional: make platoon blankable
        self.fields['platoon'].required = False


POPULAR_TIMEZONES = [
    "Australia/Melbourne",
    "Australia/Sydney",
    "Australia/Brisbane",
    "Australia/Adelaide",
    "Australia/Darwin",
    "Australia/Perth",
    "Pacific/Auckland",
]

all_timezones = sorted(available_timezones())

timezone_choices = [
    (tz, tz)
    for tz in POPULAR_TIMEZONES
    if tz in all_timezones
]

timezone_choices.extend(
    (tz, tz)
    for tz in all_timezones
    if tz not in POPULAR_TIMEZONES
)

class UnitApplicationQuestionnaireForm(forms.ModelForm):
    birth_year = forms.TypedChoiceField(
        choices=[
            ("", "---------"),
            *[
                (year, year)
                for year in range(date.today().year - 13, 1940, -1)
            ],
        ],
        coerce=lambda v: int(v) if v not in ("", None) else None,
        empty_value=None,
        required=False,
    )

    timezone = forms.ChoiceField(
        choices=timezone_choices,
        widget=forms.Select(attrs={"class": "searchable-select"}),
    )

    OPTIONAL_FIELDS = {
        "areas_of_interest",
        "referral_source",
        "previous_groups",
    }

    class Meta:
        model = UnitApplicationQuestionnaire
        fields = [
            "preferred_display_name",
            "owns_arma3",
            "has_used_tfar",
            "has_used_ace",
            "birth_year",
            "timezone",
            "seriousness_ranking",
            "areas_of_interest",
            "referral_source",
            "previous_groups",
        ]

        widgets = {
            "seriousness_ranking": forms.NumberInput(
                attrs={
                    "type": "range",
                    "min": 1,
                    "max": 10,
                    "step": 1,
                }
            ),
            "areas_of_interest": forms.CheckboxSelectMultiple(),
            "previous_groups": forms.Textarea(attrs={"rows": 4}),
        }