"""Contracts shared by aircraft geometry definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod

import adsk.fusion


class AircraftDefinition(ABC):
    """A named aircraft recipe capable of creating a native Fusion component.

    Implementations must create parametric features (rather than importing a mesh
    or a direct B-Rep) so that the resulting model is visible and editable in
    Fusion's timeline.
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
    def generate(
        self, root_component: adsk.fusion.Component, length_cm: float
    ) -> adsk.fusion.Component:
        """Create and return an editable aircraft component below ``root_component``.

        Args:
            root_component: Design root where the generated occurrence is placed.
            length_cm: Requested overall aircraft length in Fusion internal units.

        Raises:
            ValueError: If the requested dimensions are not physically meaningful.
            RuntimeError: If the definition cannot construct its required geometry.
        """
