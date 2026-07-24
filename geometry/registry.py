"""Ordered aircraft definitions exposed by the Fusion command."""

from __future__ import annotations

from .aircraft_definition import AircraftDefinition
from .elliptical_loft_prototype import EllipticalLoftPrototypeDefinition
from .sr71_definition import SR71Definition

AIRCRAFT_DEFINITIONS: tuple[AircraftDefinition, ...] = (
    SR71Definition(),
    EllipticalLoftPrototypeDefinition(),
)
