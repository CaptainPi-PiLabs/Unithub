from dataclasses import dataclass
from datetime import datetime

@dataclass
class TimelineEvent:
    event_type: str
    timestamp: datetime
    user: object
    section: object | None = None
    snapshot_name: str = ""
    description: str = ""
    source: object | None = None