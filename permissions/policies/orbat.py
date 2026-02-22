from orbat.enums import OrbatActions
from orbat.models.sections import Section
from orbat.selectors import get_section_slot, is_user_in_section
from .base import PermissionPolicy
from ..constants import SECTION_LEADER_ACTIONS
from ..models import PermissionModule


class OrbatPolicy(PermissionPolicy):
    module = PermissionModule.ORBAT

class SectionLeaderPolicy(OrbatPolicy):
    actions = SECTION_LEADER_ACTIONS

    def check(self, user, scope):
        if scope is None or not isinstance(scope, Section):
            return None

        slot = get_section_slot(user)
        if not slot or not slot.is_leader:
            return None

        if slot.section == scope.section:
            return True

        return None

class CanLeaveSectionPolicy(OrbatPolicy):
    actions = {OrbatActions.LEAVE_SECTION}

    def check(self, user, scope):
        if scope is None or not isinstance(scope, Section):
            return None

        if is_user_in_section(user, scope):
            return True

        return None
