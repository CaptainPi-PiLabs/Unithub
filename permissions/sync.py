from integrations.permissions import IntegrationActions
from orbat.enums import OrbatActions
from permissions.models import PermissionRule
from permissions.permission_modules.ArmaActions import ArmaActions
from training.enums import TrainingActions

MODULE_ENUMS = {
    "arma": ArmaActions,
    "orbat": OrbatActions,
    "training": TrainingActions,
    "integrations": IntegrationActions
}

def sync_permission_rules():
    for module_name, enum_cls in MODULE_ENUMS.items():
        for action in enum_cls:
            PermissionRule.objects.get_or_create(module=module_name, action=action.value)