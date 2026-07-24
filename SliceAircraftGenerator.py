"""Fusion entry point for the Slice Aircraft Generator add-in."""

from __future__ import annotations

import traceback
from typing import Any

from .commands.slice_aircraft import SliceAircraftCommand
from .utils.fusion import report_error

_command: SliceAircraftCommand | None = None


def run(context: dict[str, Any]) -> None:
    """Load the add-in and register its Fusion command."""
    del context
    global _command

    try:
        # Detach the previous instance before attempting cleanup so that a
        # cleanup error cannot leave a stale global reference.
        previous_command = _command
        _command = None

        if previous_command is not None:
            previous_command.stop()

        new_command = SliceAircraftCommand()

        try:
            new_command.start()
        except Exception:
            # Best-effort cleanup if startup registered only some resources.
            try:
                new_command.stop()
            except Exception:
                pass
            raise

        _command = new_command

    except Exception:
        report_error(
            "Unable to start Slice Aircraft Generator",
            traceback.format_exc(),
        )


def stop(context: dict[str, Any]) -> None:
    """Unload the add-in and release all Fusion UI and event resources."""
    del context
    global _command

    command = _command
    _command = None

    if command is None:
        return

    try:
        command.stop()
    except Exception:
        report_error(
            "Unable to stop Slice Aircraft Generator",
            traceback.format_exc(),
        )
