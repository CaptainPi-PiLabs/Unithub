def get_event_type_scopes():
    from events.models import Event
    return {key for key, _ in Event.EVENT_TYPE_CHOICES}

PERMISSIONS = {
    "training": {
        "modifyqualification": {"allowed_scopes": ["qualification"]},
        "addqualification": {"allowed_scopes": ["qualification"]},
        "removequalification": {"allowed_scopes": ["qualification"]},
        "addcriteria": {"allowed_scopes": ["qualification", "qualificationcriterion"]},
        "removecriteria": {"allowed_scopes": ["qualification", "qualificationcriterion"]},
        "modifycriteria": {"allowed_scopes": ["qualification", "qualificationcriterion"]},
        "grantqualification": {"allowed_scopes": ["qualification"]},
    },
    "events": {
        "create": {"allowed_scopes": lambda: get_event_type_scopes() | {None}},
        "modify": {"allowed_scopes": lambda: get_event_type_scopes() | {None}},
        "delete": {"allowed_scopes": lambda: get_event_type_scopes() | {None}},
    },
    "orbat": {
        "create": {"allowed_scopes": ["platoon", "section"]},
        "modify": {"allowed_scopes": ["platoon", "section"]},
        "delete": {"allowed_scopes": ["platoon", "section"]},
    },
}

INHERITED_RULES = [
    {
        "module": "orbat",
        "permissions": ["changedescription", "approve_application"],
        "check": lambda user, scope: getattr(scope.leader, "id", None) == user.id
    },
]