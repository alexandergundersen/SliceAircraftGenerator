"""Contracts shared by aircraft geometry definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .build_context import AircraftBuildContext

if TYPE_CHECKING:
    import adsk.fusion


class AircraftDefinition(ABC):
    """A named aircraft recipe capable of creating a native Fusion component.

    Implementations receive immutable build inputs and should create parametric
    features, rather than importing opaque mesh or direct B-Rep geometry.
    """

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Return the human-readable name presented in the command dialog."""

    @property
    @abstractmethod
    def default_length_cm(self) -> float:
        """Return the default overall length in Fusion's internal centimetres."""

    @abstractmethod
    def generate(self, context: AircraftBuildContext) -> adsk.fusion.Component:
        """Create and return an editable aircraft component below ``root_component``.

        Args:
            context: Immutable inputs for the requested generation operation.

        Raises:
            ValueError: If the requested dimensions are not physically meaningful.
            RuntimeError: If the definition cannot construct its required geometry.
        """
