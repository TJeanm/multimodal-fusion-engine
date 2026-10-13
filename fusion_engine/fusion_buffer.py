from collections import deque

from fusion_engine.events import InputEvent


class FusionBuffer:
    """Store input events within a configurable time window."""

    def __init__(self, window_s: float = 4.0):
        if window_s <= 0:
            raise ValueError("window_s must be positive")

        self.window_s = window_s
        self._events: deque[InputEvent] = deque()

    def add(self, event: InputEvent) -> None:
        """Add an event and remove expired events."""
        self.expire(event.received_at)
        self._events.append(event)

    def expire(self, now: float) -> None:
        """Remove events older than the fusion window."""
        while (
            self._events
            and now - self._events[0].received_at > self.window_s
        ):
            self._events.popleft()

    def get_events(self, now: float) -> list[InputEvent]:
        """Return non-expired events."""
        self.expire(now)
        return list(self._events)

    def clear(self) -> None:
        """Clear all stored events."""
        self._events.clear()