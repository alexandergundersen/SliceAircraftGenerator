"""Fusion 360 entry point for the Slice Aircraft Generator add-in."""

from __future__ import annotations

import traceback

import adsk.core

from commands.slice_aircraft import SliceAircraftCommand
from utils.fusion import report_error


_command: SliceAircraftCommand | None = None


def run(context: str) -> None:
    """Load the add-in and register its Fusion command."""
    del context  # Fusion supplies this value; this add-in does not need it.
    global _command

    try:
        # Fusion can call run again while reloading an add-in. Make re-entry safe.
        if _command is not None:
            _command.stop()

        _command = SliceAircraftCommand()
        _command.start()
    except Exception:
        report_error("Unable to start Slice Aircraft Generator", traceback.format_exc())


def stop(context: str) -> None:
    """Unload the add-in and release all Fusion UI and event resources."""
    del context
    global _command

    try:
        if _command is not None:
            _command.stop()
            _command = None
    except Exception:
        report_error("Unable to stop Slice Aircraft Generator", traceback.format_exc())
