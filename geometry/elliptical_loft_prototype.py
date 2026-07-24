"""A deliberately generic recipe demonstrating the reusable lofting core."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .aircraft_definition import AircraftDefinition
from .build_context import AircraftBuildContext
from .loft_builder import LoftBuilder
from .station import Station, scale_stations

if TYPE_CHECKING:
    import adsk.fusion


class EllipticalLoftPrototypeDefinition(AircraftDefinition):
    """Generate an editable generic elliptical loft for end-to-end testing.

    This is demonstration geometry only. It intentionally makes no claim to
    represent a real aircraft, and delegates all Fusion feature creation to
    :class:`geometry.loft_builder.LoftBuilder`.
    """

    _DEFAULT_LENGTH_CM = 1_000.0
    _STATIONS = (
        Station(0.000, 3.5, 3.0),
        Station(0.025, 15.0, 12.0),
        Station(0.100, 39.0, 31.0),
        Station(0.300, 66.0, 46.0),
        Station(0.600, 79.0, 54.0),
        Station(0.850, 50.0, 35.0),
        Station(0.975, 11.0, 10.0),
        Station(1.000, 3.0, 2.5),
    )

    @property
    def display_name(self) -> str:
        return "Elliptical Loft Prototype"

    @property
    def default_length_cm(self) -> float:
        return self._DEFAULT_LENGTH_CM

    def generate(self, context: AircraftBuildContext) -> adsk.fusion.Component:
        """Scale the prototype station data and delegate Fusion construction."""
        stations = scale_stations(
            self._STATIONS,
            reference_length_cm=self.default_length_cm,
            requested_length_cm=context.length_cm,
        )
        return LoftBuilder().build(
            context,
            stations,
            default_component_name=self.display_name,
        )
