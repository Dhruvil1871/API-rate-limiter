from collections import deque
from enum import Enum
from datetime import datetime

class EventType(Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REDIS_LOST = "REDIS_LOST"
    REDIS_RESTORED = "REDIS_RESTORED"
    FALLBACK_ENABLED = "FALLBACK_ENABLED"
    FALLBACK_DISABLED = "FALLBACK_DISABLED"

class EventManager:
    def __init__(self):
        self.events = deque(maxlen = 100)

    def add_event(self, event_type, message, **extra):
        timestamp = datetime.now().strftime("%H:%M:%S")

        event = {
            "timestamp" : timestamp,
            "type" : event_type.value,
            "message" : message,
        }

        event.update(extra)

        self.events.append(event)

    def get_events(self):
        return list(self.events)

event_manager = EventManager()