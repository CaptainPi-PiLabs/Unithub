from enum import Enum


class IntergrationActions(str, Enum):
    VIEW_EVENTS = "view_events"
    MANAGE_EVENTS = "manage_events"