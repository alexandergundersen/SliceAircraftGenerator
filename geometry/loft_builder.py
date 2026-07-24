"""Fusion-specific construction of an elliptical station loft."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from .build_context import AircraftBuildContext
from .station import Station, validate_station_sequence

if TYPE_CHECKING:
    import adsk.fusion


class LoftBuilder:
    """Build named Fusion timeline features from pre-validated station data."""

    def build(
        self,
        context: AircraftBuildContext,
        stations: Iterable[Station],
        *,
        default_component_name: str,
    ) -> adsk.fusion.Component:
        """Create a child component, station profiles, and one native solid loft.

        Fusion imports live inside this method so this module remains importable
        by pure-Python tests and tooling outside Fusion 360.
        """
        import adsk.core
        import adsk.fusion

        ordered_stations = validate_station_sequence(stations)
        component_name = context.resolved_component_name(default_component_name)
        occurrence = context.root_component.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        component = occurrence.component
        component.name = component_name
        occurrence.name = component_name

        try:
            profiles = self._create_station_profiles(
                component, ordered_stations, context.length_cm, component_name
            )
            loft = self._create_solid_loft(component, profiles)
            loft.name = f"{component_name} Loft"
            if loft.bodies.count:
                loft.bodies.item(0).name = f"{component_name} Body"
            return component
        except Exception:
            # Avoid leaving a partial occurrence in the browser or timeline.
            if occurrence.isValid:
                occurrence.deleteMe()
            raise

    @staticmethod
    def _create_station_profiles(
        component: adsk.fusion.Component,
        stations: tuple[Station, ...],
        length_cm: float,
        component_name: str,
    ) -> list[adsk.fusion.Profile]:
        """Create closed ellipse profiles on named YZ offset planes."""
        import adsk.core

        profiles: list[adsk.fusion.Profile] = []
        for index, station in enumerate(stations, start=1):
            plane_input = component.constructionPlanes.createInput()
            plane_defined = plane_input.setByOffset(
                component.yZConstructionPlane,
                adsk.core.ValueInput.createByReal(station.position * length_cm),
            )
            if not plane_defined:
                raise RuntimeError(f"Unable to define station {index:02d} plane offset.")

            plane = component.constructionPlanes.add(plane_input)
            if plane is None:
                raise RuntimeError(f"Unable to create station {index:02d} plane.")
            plane.name = f"{component_name} Station {index:02d} Plane"

            sketch = component.sketches.add(plane)
            if sketch is None:
                raise RuntimeError(f"Unable to create station {index:02d} sketch.")
            sketch.name = f"{component_name} Station {index:02d}"
            LoftBuilder._add_ellipse(sketch, station)
            if sketch.profiles.count != 1:
                raise RuntimeError(f"Station {index:02d} did not produce a closed profile.")
            profiles.append(sketch.profiles.item(0))
        return profiles

    @staticmethod
    def _add_ellipse(sketch: adsk.fusion.Sketch, station: Station) -> None:
        """Add one closed ellipse in local sketch coordinates."""
        import adsk.core

        centre = adsk.core.Point3D.create(0, 0, 0)
        major_axis_point = adsk.core.Point3D.create(station.half_width_cm, 0, 0)
        minor_axis_point = adsk.core.Point3D.create(0, station.half_height_cm, 0)
        sketch.sketchCurves.sketchEllipses.add(centre, major_axis_point, minor_axis_point)

    @staticmethod
    def _create_solid_loft(
        component: adsk.fusion.Component, profiles: list[adsk.fusion.Profile]
    ) -> adsk.fusion.LoftFeature:
        """Create one native solid LoftFeature from ordered profile sections."""
        import adsk.fusion

        loft_features = component.features.loftFeatures
        loft_input = loft_features.createInput(
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        loft_input.isSolid = True
        for profile in profiles:
            loft_input.loftSections.add(profile)
        loft = loft_features.add(loft_input)
        if loft is None:
            raise RuntimeError("Unable to create the elliptical loft.")
        return loft
