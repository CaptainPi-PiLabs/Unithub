from rest_framework.authentication import SessionAuthentication
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from apis.auth import APIKeyAuthentication
from apis.perms import APIPermission
from permissions.models import PermissionModule


class BaseAPIView(APIView):
    renderer_classes = [JSONRenderer]
    authentication_classes = [
        APIKeyAuthentication,
        SessionAuthentication
    ]
    permission_classes = [APIPermission]

    module = None
    object_permission_required = True
    required_permissions = {}
    _object = None

    def get_object(self):
        """
        Return the object to use as the scope for permission checks.
        Override in child views.
        """
        raise NotImplementedError

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        request.effective_user = request.user if getattr(request.user, "is_authenticated", False) else None

        if self.object_permission_required:
            obj = self.get_object()
            self._object = obj
            self.check_object_permissions(request, obj)

class OrbatAPIView(BaseAPIView):
    module = PermissionModule.ORBAT

class TrainingAPIView(BaseAPIView):
    module = PermissionModule.TRAINING