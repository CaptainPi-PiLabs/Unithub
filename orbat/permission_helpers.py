from orbat.enums import OrbatActions
from permissions.engine import has_any_permission
from permissions.models import PermissionModule


def can_manage_orbat(user):
    return has_any_permission(user, PermissionModule.ORBAT, OrbatActions.MODIFY_SECTION)

def is_eligible_for_section_application(user):
    if not user or not user.is_authenticated:
        return False

    if user.get_section() is not None:
        return False

    return user.membership in {
        "Junior Operator",
        "Operator",
        "Veteran Operator",
    }