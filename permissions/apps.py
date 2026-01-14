import logging

from django.apps import AppConfig


logger = logging.getLogger(__name__)

class PermissionsConfig(AppConfig):
    name = 'permissions'

    def ready(self):
        from django.db.utils import OperationalError, ProgrammingError
        try:
            from permissions.sync import sync_permission_rules
            sync_permission_rules()
        except (OperationalError, ProgrammingError):
            pass