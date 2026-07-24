"""Aircraft-definition adapter for the recognizable SR-71 approximation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .aircraft_definition import AircraftDefinition
from .build_context import AircraftBuildContext
from .sr71_builder import SR71Builder
from .sr71_data import DEFAULT_MODEL_LENGTH_CM, SR71_DATA

if TYPE_CHECKING:
    import adsk.fusion


class SR71Definition(AircraftDefinition):
    """Create a native, editable, multi-body SR-71-inspired display model.

    The source proportions live in ``sr71_data``; Fusion feature creation lives
    in ``sr71_builder``. This definition deliberately represents a recognizable
    fabrication approximation, not a restoration- or engineering-accurate model.
    """

    @property
    def display_name(self) -> str:
        return "SR-71 Blackbird"

    @property
    def default_length_cm(self) -> float:
        return DEFAULT_MODEL_LENGTH_CM

    def generate(self, context: AircraftBuildContext) -> adsk.fusion.Component:
        """Scale normalized SR-71 data and build native Fusion bodies."""
        return SR71Builder().build(
            context,
            SR71_DATA.scale(context.length_cm),
            default_component_name=self.display_name,
        )
