from django.core.exceptions import PermissionDenied
from permissions.engine import has_permission


class PermissionRequiredMixin:
    permission = None
    module = None
    scope_getter = None  # function returning instance from self

    def dispatch(self, request, *args, **kwargs):
        scope = self.scope_getter(self) if self.scope_getter else None
        if not has_permission(request.user, self.module, self.permission, scope):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)