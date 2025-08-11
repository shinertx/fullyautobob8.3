from __future__ import annotations
import os, json, time
from typing import Dict, Any, Optional
from loguru import logger

class EventStore:
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.events_path = os.path.join(self.log_dir, "events.ndjson")

    def emit(self, event_type: str, payload: Dict[str, Any], ts: Optional[float] = None):
        try:
            event = {"ts": ts or time.time(), "type": event_type, "payload": payload}
            with open(self.events_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, default=str) + "\n")
            return event
        except Exception as e:
            logger.error(f"Failed to emit event {event_type}: {e}")
            return None
