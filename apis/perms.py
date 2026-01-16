from rest_framework.permissions import BasePermission

from apis.models import UserAPIKey, ServiceAPIKey
from permissions.engine import has_permission


class APIPermission(BasePermission):
    def has_permission(self, request, view):
        subject = request.auth or request.user

        if isinstance(subject, UserAPIKey) or isinstance(subject, ServiceAPIKey):
            pass # auth via key → fine
        elif getattr(subject, "is_authenticated", False):
            pass # session user → fine
        else:
            return False

        if view.module is None:
            return False

        actions = view.required_permissions.get(request.method)
        if not actions:
            return False

        if view.object_permission_required:
            return True

        for action in actions:
            if not has_permission(subject, view.module, action):
                return False
        return True

    def has_object_permission(self, request, view, obj):
        subject = request.auth or request.user
        actions = view.required_permissions.get(request.method)
        if not actions:
            return False

        for action in actions:
            if not has_permission(subject, view.module, action, scope=obj):
                return False

        return True