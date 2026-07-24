"""Immutable inputs used to build one aircraft definition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import adsk.fusion


@dataclass(frozen=True)
class AircraftBuildContext:
    """Inputs shared by a single aircraft-generation operation.

    Length is expressed in Fusion's internal centimetres. ``component_name`` can
    override a definition's default browser name when an application needs to
    distinguish multiple generated instances.
    """

    root_component: adsk.fusion.Component
    length_cm: float
    component_name: str | None = None

    def __post_init__(self) -> None:
        if self.length_cm <= 0:
            raise ValueError("Aircraft length must be greater than zero.")

    def resolved_component_name(self, default_name: str) -> str:
        """Return the explicit name when supplied, otherwise ``default_name``."""
        return self.component_name or default_name
