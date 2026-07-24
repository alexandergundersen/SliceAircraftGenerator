"""Fusion-specific construction of an elliptical station loft."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .build_context import AircraftBuildContext, BuildPlacement
from .station import Station, validate_station_sequence

if TYPE_CHECKING:
    import adsk.fusion


ZERO_OFFSET_TOLERANCE_CM = 1e-6


def uses_origin_plane(offset_cm: float) -> bool:
    """Return whether an offset is close enough to reuse the YZ origin plane."""
    return abs(offset_cm) <= ZERO_OFFSET_TOLERANCE_CM


@dataclass
class _BuildTarget:
    """Resolved Fusion target and ownership details for one generation operation."""

    component: adsk.fusion.Component
    owned_occurrence: adsk.fusion.Occurrence | None
    rename_component: bool


@dataclass
class _CreatedFeatures:
    """Objects owned by a root-component generation and eligible for rollback."""

    loft: adsk.fusion.LoftFeature | None = None
    station_sketches: list[adsk.fusion.Sketch] = field(default_factory=list)
    offset_planes: list[adsk.fusion.ConstructionPlane] = field(default_factory=list)


class LoftBuilder:
    """Build named Fusion timeline features from pre-validated station data."""

    def build(
        self,
        context: AircraftBuildContext,
        stations: Iterable[Station],
        *,
        default_component_name: str,
    ) -> adsk.fusion.Component:
        """Create the selected target's station profiles and one native solid loft."""
        ordered_stations = validate_station_sequence(stations)
        feature_name_prefix = context.feature_name_prefix(default_component_name)
        target = self._resolve_target(context, feature_name_prefix)
        created_features = _CreatedFeatures()

        try:
            profiles = self._create_station_profiles(
                target.component,
                ordered_stations,
                context.length_cm,
                feature_name_prefix,
                created_features,
            )
            loft = self._create_solid_loft(target.component, profiles, created_features)
            loft.name = f"{feature_name_prefix} Loft"
            if loft.bodies.count:
                loft.bodies.item(0).name = f"{feature_name_prefix} Body"
            return target.component
        except Exception:
            if target.owned_occurrence is not None:
                self._delete_if_valid(target.owned_occurrence)
            else:
                self._cleanup_root_features(created_features)
            raise

    @staticmethod
    def _resolve_target(context: AircraftBuildContext, feature_name_prefix: str) -> _BuildTarget:
        """Resolve root or internal-component placement before creating geometry."""
        if context.placement is BuildPlacement.ROOT_COMPONENT:
            return _BuildTarget(
                component=context.root_component,
                owned_occurrence=None,
                rename_component=False,
            )

        if context.placement is not BuildPlacement.NEW_INTERNAL_COMPONENT:
            raise ValueError(f"Unsupported aircraft build placement: {context.placement!r}")

        occurrence = None
        try:
            import adsk.core

            occurrence = context.root_component.occurrences.addNewComponent(
                adsk.core.Matrix3D.create()
            )
            if occurrence is None:
                raise RuntimeError("Unable to create the generated component occurrence.")
            component = occurrence.component
            if component is None:
                raise RuntimeError("Unable to access the generated component.")
            component.name = feature_name_prefix
            occurrence.name = feature_name_prefix
            return _BuildTarget(
                component=component,
                owned_occurrence=occurrence,
                rename_component=True,
            )
        except Exception:
            # This operation owns a partially created internal occurrence.
            LoftBuilder._delete_if_valid(occurrence)
            raise

    @staticmethod
    def _create_station_profiles(
        component: adsk.fusion.Component,
        stations: tuple[Station, ...],
        length_cm: float,
        feature_name_prefix: str,
        created_features: _CreatedFeatures,
    ) -> list[adsk.fusion.Profile]:
        """Create closed ellipse profiles on origin or named YZ offset planes."""
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
                if not plane_input.setByOffset(component.yZConstructionPlane, offset_input):
                    raise RuntimeError(
                        f"Station {index:02d}: unable to define offset plane at {offset_cm:g} cm."
                    )

                plane = component.constructionPlanes.add(plane_input)
                if plane is None:
                    raise RuntimeError(
                        f"Station {index:02d}: unable to create offset plane at {offset_cm:g} cm."
                    )
                created_features.offset_planes.append(plane)
                plane.name = f"{feature_name_prefix} Station {index:02d} Plane"
                sketch_plane = plane

            sketch = component.sketches.add(sketch_plane)
            if sketch is None:
                raise RuntimeError(
                    f"Station {index:02d}: unable to create sketch at {offset_cm:g} cm."
                )
            created_features.station_sketches.append(sketch)
            sketch.name = f"{feature_name_prefix} Station {index:02d}"
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
        component: adsk.fusion.Component,
        profiles: list[adsk.fusion.Profile],
        created_features: _CreatedFeatures,
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
        created_features.loft = loft
        return loft

    @staticmethod
    def _cleanup_root_features(created_features: _CreatedFeatures) -> None:
        """Best-effort rollback of only objects created in a root component."""
        LoftBuilder._delete_if_valid(created_features.loft)
        for sketch in reversed(created_features.station_sketches):
            LoftBuilder._delete_if_valid(sketch)
        for plane in reversed(created_features.offset_planes):
            LoftBuilder._delete_if_valid(plane)

    @staticmethod
    def _delete_if_valid(entity: object | None) -> None:
        """Delete a generated Fusion object without masking the original error."""
        try:
            if entity is not None and entity.isValid:
                entity.deleteMe()
        except Exception:
            # Cleanup is deliberately best effort; the originating error is re-raised.
            pass
