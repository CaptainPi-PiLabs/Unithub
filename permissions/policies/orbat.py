from orbat.enums import OrbatActions
from orbat.models import Section
from .base import PermissionPolicy
from ..constants import SECTION_LEADER_ACTIONS
from ..models import PermissionModule


class OrbatPolicy(PermissionPolicy):
    module = PermissionModule.ORBAT

class SectionLeaderPolicy(OrbatPolicy):
    actions = SECTION_LEADER_ACTIONS

    def check(self, user, scope):

        if scope is None:
            return None

        leader_id = getattr(scope, "leader_id", None)
        if leader_id is None:
            return None

        if leader_id == user.id:
            return True

        return None

class CanLeaveSectionPolicy(OrbatPolicy):
    actions = {OrbatActions.LEAVE_SECTION}

    def check(self, user, scope):
        if scope is None:
            return None

        if not isinstance(scope, Section):
            return None

        if user.section == scope:
            return True

        return None
