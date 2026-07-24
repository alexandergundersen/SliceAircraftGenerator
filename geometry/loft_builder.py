"""Fusion-specific construction of an elliptical station loft."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from .build_context import AircraftBuildContext
from .station import Station, validate_station_sequence

if TYPE_CHECKING:
    import adsk.fusion


ZERO_OFFSET_TOLERANCE_CM = 1e-6


def uses_origin_plane(offset_cm: float) -> bool:
    """Return whether an offset is close enough to reuse the YZ origin plane."""
    return abs(offset_cm) <= ZERO_OFFSET_TOLERANCE_CM


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
        if occurrence is None:
            raise RuntimeError("Unable to create the generated component occurrence.")
        component = occurrence.component
        if component is None:
            raise RuntimeError("Unable to access the generated component.")
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
            offset_cm = station.position * length_cm
            sketch_plane = component.yZConstructionPlane
            if not uses_origin_plane(offset_cm):
                plane_input = component.constructionPlanes.createInput()
                if plane_input is None:
                    raise RuntimeError(
                        f"Station {index:02d}: unable to create offset plane input at "
                        f"{offset_cm:g} cm."
                    )
                offset_input = adsk.core.ValueInput.createByReal(offset_cm)
                if offset_input is None:
                    raise RuntimeError(
                        f"Station {index:02d}: unable to create offset value at {offset_cm:g} cm."
                    )
                plane_defined = plane_input.setByOffset(
                    component.yZConstructionPlane,
                    offset_input,
                )
                if not plane_defined:
                    raise RuntimeError(
                        f"Station {index:02d}: unable to define offset plane at {offset_cm:g} cm."
                    )

                plane = component.constructionPlanes.add(plane_input)
                if plane is None:
                    raise RuntimeError(
                        f"Station {index:02d}: unable to create offset plane at {offset_cm:g} cm."
                    )
                plane.name = f"{component_name} Station {index:02d} Plane"
                sketch_plane = plane

            sketch = component.sketches.add(sketch_plane)
            if sketch is None:
                raise RuntimeError(
                    f"Station {index:02d}: unable to create sketch at {offset_cm:g} cm."
                )
            sketch.name = f"{component_name} Station {index:02d}"
            LoftBuilder._add_ellipse(sketch, station, index, offset_cm)
            if sketch.profiles.count != 1:
                raise RuntimeError(f"Station {index:02d}: no closed profile at {offset_cm:g} cm.")
            profile = sketch.profiles.item(0)
            if profile is None:
                raise RuntimeError(
                    f"Station {index:02d}: unable to retrieve profile at {offset_cm:g} cm."
                )
            profiles.append(profile)
        return profiles

    @staticmethod
    def _add_ellipse(
        sketch: adsk.fusion.Sketch,
        station: Station,
        station_index: int,
        offset_cm: float,
    ) -> None:
        """Add one closed ellipse in local sketch coordinates."""
        import adsk.core

        centre = adsk.core.Point3D.create(0, 0, 0)
        major_axis_point = adsk.core.Point3D.create(station.half_width_cm, 0, 0)
        minor_axis_point = adsk.core.Point3D.create(0, station.half_height_cm, 0)
        ellipse = sketch.sketchCurves.sketchEllipses.add(centre, major_axis_point, minor_axis_point)
        if ellipse is None:
            raise RuntimeError(
                f"Station {station_index:02d}: unable to create ellipse at {offset_cm:g} cm."
            )

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
        if loft_input is None:
            raise RuntimeError("Unable to create the solid loft input.")
        loft_input.isSolid = True
        for station_index, profile in enumerate(profiles, start=1):
            loft_section = loft_input.loftSections.add(profile)
            if loft_section is None:
                raise RuntimeError(f"Unable to add loft section for station {station_index:02d}.")
        loft = loft_features.add(loft_input)
        if loft is None:
            raise RuntimeError("Unable to create the solid elliptical loft feature.")
        return loft
