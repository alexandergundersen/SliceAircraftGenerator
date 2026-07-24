"""Immutable inputs used to build one aircraft definition."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import adsk.fusion


class BuildPlacement(Enum):
    """The component target selected by the Fusion command layer."""

    ROOT_COMPONENT = "root_component"
    NEW_INTERNAL_COMPONENT = "new_internal_component"

    @property
    def owns_target_component(self) -> bool:
        """Return whether this generation operation owns the target component."""
        return self is BuildPlacement.NEW_INTERNAL_COMPONENT

    @property
    def renames_target_component(self) -> bool:
        """Return whether the target component should receive the generated name."""
        return self is BuildPlacement.NEW_INTERNAL_COMPONENT


@dataclass(frozen=True)
class AircraftBuildContext:
    """Inputs shared by a single aircraft-generation operation.

    Length is expressed in Fusion's internal centimetres. ``component_name``
    supplies a feature-name prefix and, for internal-component placement, the
    browser name of the generated component and occurrence.
    """

    root_component: adsk.fusion.Component
    length_cm: float
    placement: BuildPlacement
    component_name: str | None = None

    def __post_init__(self) -> None:
        if self.length_cm <= 0:
            raise ValueError("Aircraft length must be greater than zero.")
        if not isinstance(self.placement, BuildPlacement):
            raise ValueError("Aircraft build placement must be a BuildPlacement value.")

    def feature_name_prefix(self, default_name: str) -> str:
        """Return the explicit feature prefix when supplied, otherwise ``default_name``."""
        return self.component_name or default_name
