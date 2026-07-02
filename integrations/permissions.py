from enum import Enum


class IntegrationActions(str, Enum):
    VIEW_EVENTS = "view_events"
    MANAGE_EVENTS = "manage_events"