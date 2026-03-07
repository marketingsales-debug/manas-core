"""
EventBus — The Nervous System of Manas.

When one agent detects something, the whole brain reacts.
Example: WorldMonitor detects crisis → SecurityAgent starts scanning
→ FinancialAgent pauses risky trades → SurvivalAgent creates backup.
"""

import logging
import threading
from typing import Callable, Dict, List

logger = logging.getLogger(__name__)


class EventBus:
    """
    Central event dispatcher. Agents emit events, other agents react.
    Thread-safe and supports wildcard listeners.
    """

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()
        self.total_events_emitted = 0
        self.total_events_handled = 0
        self.event_log: List[dict] = []

    def on(self, event_name: str, callback: Callable):
        """Register a listener for an event."""
        with self._lock:
            if event_name not in self._listeners:
                self._listeners[event_name] = []
            self._listeners[event_name].append(callback)
            logger.debug(f"EventBus: Registered listener for '{event_name}'")

    def off(self, event_name: str, callback: Callable):
        """Unregister a listener."""
        with self._lock:
            if event_name in self._listeners:
                self._listeners[event_name] = [
                    cb for cb in self._listeners[event_name] if cb != callback
                ]

    def emit(self, event_name: str, data: dict = None):
        """
        Emit an event. All registered listeners are called.
        Listeners run in the same thread (synchronous) simply because
        they should be fast reactions (reflexes), not long tasks.
        """
        data = data or {}
        self.total_events_emitted += 1
        self.event_log.append({"event": event_name, "data_keys": list(data.keys())})
        # Keep only last 100 events
        if len(self.event_log) > 100:
            self.event_log = self.event_log[-100:]

        with self._lock:
            listeners = list(self._listeners.get(event_name, []))
            # Also call wildcard listeners
            listeners += list(self._listeners.get("*", []))

        for callback in listeners:
            try:
                callback(event_name, data)
                self.total_events_handled += 1
            except Exception as e:
                logger.warning(f"EventBus: Listener error on '{event_name}': {e}")

    def get_status(self) -> str:
        registered = sum(len(v) for v in self._listeners.values())
        return (
            f"⚡ EventBus Status:\n"
            f"  Registered listeners: {registered}\n"
            f"  Events emitted: {self.total_events_emitted}\n"
            f"  Events handled: {self.total_events_handled}\n"
            f"  Event types: {', '.join(self._listeners.keys()) or 'None'}"
        )
