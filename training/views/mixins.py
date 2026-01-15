from django.conf import settings

from core.exceptions import WIPFeatureError


class TrainingContextMixin:
    title = "Training"

    def dispatch(self, request, *args, **kwargs):
        if not getattr(settings, "ENABLE_TRAINING", False):
            raise WIPFeatureError
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["sidebar"] = [
            {"name": "Overview", "path": "/training/"},
            {"name": "Matrix", "path": "/training/matrix/"},
            # {"name": "Events", "path": "/events/training/"},
            {"name": "Qualifications", "path": "/training/qualifications/"}
        ]

        return context
