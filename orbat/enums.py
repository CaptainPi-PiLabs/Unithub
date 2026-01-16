from enum import Enum


class OrbatActions(str, Enum):
    CREATE_PLATOON = "create_platoon"
    MODIFY_PLATOON = "modify_platoon"
    REMOVE_PLATOON = "remove_platoon"
    CREATE_SECTION = "create_section"
    MODIFY_SECTION = "modify_section"
    REMOVE_SECTION = "remove_section"
    ASSIGN_SECTION_LEADER = "assign_section_leader"
    APPROVE_SECTION_APPLICATION = "approve_section_application"
    APPROVE_UNIT_APPLICATION = "approve_unit_application"
    DENY_UNIT_APPLICATION = "deny_unit_application"
    LEAVE_SECTION = "leave_section"