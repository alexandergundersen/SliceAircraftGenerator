"""Safe retention and cleanup of Fusion event handler objects."""

from __future__ import annotations

from typing import Any


class EventSubscriptions:
    """Keeps handlers alive for Fusion and unregisters them deterministically."""

    def __init__(self) -> None:
        self._subscriptions: list[tuple[Any, Any]] = []

    def add(self, event: Any, handler: Any) -> None:
        """Attach and strongly retain a handler for the lifetime of this owner."""
        event.add(handler)
        self._subscriptions.append((event, handler))

    def clear(self) -> None:
        """Detach every tracked handler; tolerate already-destroyed Fusion objects."""
        while self._subscriptions:
            event, handler = self._subscriptions.pop()
            try:
                event.remove(handler)
            except Exception:
                # Fusion may have destroyed a command and its events already.
                pass
