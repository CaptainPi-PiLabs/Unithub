from enum import Enum

class TrainingActions(str, Enum):
    GRANT_CERTIFICATE = "grant_certificate"
    CREATE_QUALIFICATION = "create_qualification"
    MODIFY_QUALIFICATION = "modify_qualification"
    REMOVE_QUALIFICATION = "remove_qualification"
    ADD_CRITERIA = "add_criteria"
    MODIFY_CRITERIA = "modify_criteria"
    REMOVE_CRITERIA = "remove_criteria"
    MANAGE_TRAINERS = "manage_trainers"