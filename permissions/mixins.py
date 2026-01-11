from django.core.exceptions import PermissionDenied
from .services import user_has_permission


class PermissionRequiredMixin:
    permission = None
    module = None
    scope_getter = None  # function returning instance from self

    def dispatch(self, request, *args, **kwargs):
        scope = self.scope_getter(self) if self.scope_getter else None
        if not user_has_permission(request.user, self.permission, self.module, scope):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)