"""Parametric, station-lofted starter model of the SR-71 Blackbird."""

from __future__ import annotations

from dataclasses import dataclass

import adsk.core
import adsk.fusion

from geometry.aircraft_definition import AircraftDefinition


@dataclass(frozen=True)
class _FuselageStation:
    """One elliptical fuselage cross-section at the definition's default scale."""

    position: float
    half_width_cm: float
    half_height_cm: float


class SR71Definition(AircraftDefinition):
    """Create an editable SR-71-inspired fuselage from station-based lofts.

    The model intentionally begins with a clean fuselage B-Rep. Every station is
    a named construction plane and sketch, and the body is a native LoftFeature;
    users can therefore inspect and edit the complete construction sequence in
    the Fusion timeline.
    """

    _DEFAULT_LENGTH_CM = 3_270.0  # 32.70 m, the full-scale SR-71 length.
    _STATIONS = (
        _FuselageStation(0.000, 3.5, 3.0),
        _FuselageStation(0.025, 15.0, 12.0),
        _FuselageStation(0.100, 39.0, 31.0),
        _FuselageStation(0.300, 66.0, 46.0),
        _FuselageStation(0.600, 79.0, 54.0),
        _FuselageStation(0.850, 50.0, 35.0),
        _FuselageStation(0.975, 11.0, 10.0),
        _FuselageStation(1.000, 3.0, 2.5),
    )

    @property
    def display_name(self) -> str:
        return "SR-71 Blackbird"

    @property
    def default_length_cm(self) -> float:
        return self._DEFAULT_LENGTH_CM

    def generate(
        self, root_component: adsk.fusion.Component, length_cm: float
    ) -> adsk.fusion.Component:
        """Create a new component containing the station sketches and loft body."""
        if length_cm <= 0:
            raise ValueError("Aircraft length must be greater than zero.")

        occurrence = root_component.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        component = occurrence.component
        component.name = self.display_name
        occurrence.name = self.display_name

        try:
            profiles = self._create_station_profiles(component, length_cm)
            loft = self._create_fuselage_loft(component, profiles)
            loft.name = "SR-71 Fuselage Loft"
            if loft.bodies.count:
                loft.bodies.item(0).name = "SR-71 Fuselage"
            return component
        except Exception:
            # A failed feature should not leave an empty generated component behind.
            if occurrence.isValid:
                occurrence.deleteMe()
            raise

    def _create_station_profiles(
        self, component: adsk.fusion.Component, length_cm: float
    ) -> list[adsk.fusion.Profile]:
        """Create closed ellipse profiles on offset YZ planes for the fuselage loft."""
        profiles: list[adsk.fusion.Profile] = []
        for index, station in enumerate(self._STATIONS, start=1):
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
            plane.name = f"SR-71 Station {index:02d} Plane"

            sketch = component.sketches.add(plane)
            if sketch is None:
                raise RuntimeError(f"Unable to create station {index:02d} sketch.")
            sketch.name = f"SR-71 Station {index:02d}"
            self._add_ellipse(sketch, station, length_cm / self.default_length_cm)
            if sketch.profiles.count != 1:
                raise RuntimeError(f"Station {index:02d} did not produce a closed profile.")
            profiles.append(sketch.profiles.item(0))
        return profiles

    @staticmethod
    def _add_ellipse(
        sketch: adsk.fusion.Sketch, station: _FuselageStation, scale: float
    ) -> None:
        """Add a closed ellipse in local sketch coordinates for one station."""
        centre = adsk.core.Point3D.create(0, 0, 0)
        major_axis_point = adsk.core.Point3D.create(station.half_width_cm * scale, 0, 0)
        minor_axis_point = adsk.core.Point3D.create(0, station.half_height_cm * scale, 0)
        sketch.sketchCurves.sketchEllipses.add(centre, major_axis_point, minor_axis_point)

    @staticmethod
    def _create_fuselage_loft(
        component: adsk.fusion.Component, profiles: list[adsk.fusion.Profile]
    ) -> adsk.fusion.LoftFeature:
        """Create one solid LoftFeature from ordered station profiles."""
        loft_features = component.features.loftFeatures
        loft_input = loft_features.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        loft_input.isSolid = True
        for profile in profiles:
            loft_input.loftSections.add(profile)
        loft = loft_features.add(loft_input)
        if loft is None:
            raise RuntimeError("Unable to create the SR-71 fuselage loft.")
        return loft
