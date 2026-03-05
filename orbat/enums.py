from enum import Enum


class OrbatActions(str, Enum):
    CREATE_PLATOON = "create_platoon"
    READ_PLATOON = "read_platoon"
    MODIFY_PLATOON = "modify_platoon"
    REMOVE_PLATOON = "remove_platoon"
    CREATE_SECTION = "create_section"
    READ_SECTION = "read_section"
    MODIFY_SECTION = "modify_section"
    REMOVE_SECTION = "remove_section"
    ASSIGN_SECTION_LEADER = "assign_section_leader"
    VIEW_SECTION_APPLICATIONS = "view_section_applications"
    MANAGE_SECTION_APPLICATIONS = "manage_section_applications"
    APPROVE_SECTION_APPLICATION = "approve_section_applications"
    DENY_SECTION_APPLICATIONS = "deny_section_applications"
    CREATE_SECTION_APPLICATIONS = "create_section_applications"
    VIEW_UNIT_APPLICATIONS = "view_unit_applications"
    MANAGE_UNIT_APPLICATIONS = "manage_unit_applications"
    APPROVE_UNIT_APPLICATIONS = "approve_unit_applications"
    DENY_UNIT_APPLICATIONS = "deny_unit_applications"
    CREATE_UNIT_APPLICATIONS = "create_unit_applications"
    LEAVE_SECTION = "leave_section"