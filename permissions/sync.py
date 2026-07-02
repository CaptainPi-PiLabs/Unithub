from integrations.permissions import IntegrationActions
from orbat.enums import OrbatActions
from permissions.models import PermissionRule
from training.enums import TrainingActions

MODULE_ENUMS = {
    "orbat": OrbatActions,
    "training": TrainingActions,
    "integrations": IntegrationActions
}

def sync_permission_rules():
    for module_name, enum_cls in MODULE_ENUMS.items():
        for action in enum_cls:
            PermissionRule.objects.get_or_create(module=module_name, action=action.value)