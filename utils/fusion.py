"""Small, UI-safe reporting helpers for Fusion add-in code."""

from __future__ import annotations

import adsk.core


def log(message: str) -> None:
    """Write an add-in message to Fusion's Text Commands palette."""
    app = adsk.core.Application.get()
    if app is not None:
        app.log(f"[SliceAircraftGenerator] {message}")


def report_error(summary: str, details: str | None = None) -> None:
    """Log an error and, when possible, display a concise Fusion message box."""
    message = f"{summary}\n\n{details}" if details else summary
    try:
        log(message)
        app = adsk.core.Application.get()
        if app is not None:
            app.userInterface.messageBox(summary)
    except Exception:
        # Avoid propagating errors from error reporting into Fusion event handlers.
        pass
