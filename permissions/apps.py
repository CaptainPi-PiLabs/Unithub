import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)

class PermissionsConfig(AppConfig):
    name = 'permissions'

    def ready(self):
        from django.contrib.auth.models import AnonymousUser

        def anon_has_permission(self, permission, module, scope=None):
            logger.debug(
                f"AnonymousUser attempted has_permission(permission={permission}, "
                f"module={module}, scope={scope})"
            )
            return False
        AnonymousUser.has_permission = anon_has_permission