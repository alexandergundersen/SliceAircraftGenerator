"""Fusion-native construction of the multi-body SR-71 approximation."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from .build_context import AircraftBuildContext
from .loft_builder import FeatureTransaction, uses_origin_plane
from .sr71_data import (
    ScaledFuselageStation,
    ScaledSR71Geometry,
)

if TYPE_CHECKING:
    import adsk.fusion


class SR71Builder:
    """Build a named, editable multi-body SR-71 approximation in Fusion.

    The geometry follows the coordinate system documented in ``sr71_data``:
    X nose-to-tail, Y lateral, and Z vertical. It intentionally prioritizes a
    recognizable fabrication-oriented silhouette over engineering fidelity.
    """

    def build(
        self,
        context: AircraftBuildContext,
        scaled: ScaledSR71Geometry,
        *,
        default_component_name: str,
    ) -> adsk.fusion.Component:
        """Create fuselage, wing, nacelles, canopy, and canted tail bodies."""
        feature_name_prefix = context.feature_name_prefix(default_component_name)
        transaction = FeatureTransaction(context, feature_name_prefix)

        try:
            self._create_fuselage(transaction, scaled, feature_name_prefix)
            self._create_wing(transaction, scaled, feature_name_prefix)
            self._create_nacelle(
                transaction, scaled, feature_name_prefix, side_name="Right", sign=1
            )
            self._create_nacelle(
                transaction, scaled, feature_name_prefix, side_name="Left", sign=-1
            )
            self._create_canopy(transaction, scaled, feature_name_prefix)
            self._create_tail(transaction, scaled, feature_name_prefix, side_name="Right", sign=1)
            self._create_tail(transaction, scaled, feature_name_prefix, side_name="Left", sign=-1)
            transaction.hide_construction_geometry()
            return transaction.component
        except Exception:
            transaction.rollback()
            raise

    def _create_fuselage(
        self,
        transaction: FeatureTransaction,
        scaled: ScaledSR71Geometry,
        prefix: str,
    ) -> None:
        profiles = []
        for index, station in enumerate(scaled.fuselage_stations, start=1):
            sketch = self._create_yz_sketch(
                transaction,
                station.position_cm,
                f"{prefix} Fuselage Station {index:02d}",
            )
            self._add_fuselage_profile(sketch, station, index)
            profiles.append(self._require_profile(sketch, f"Fuselage station {index:02d}"))

        loft = self._create_solid_loft(transaction, profiles, "fuselage/chine")
        self._name_feature_body(
            loft, f"{prefix} Fuselage/Chine Loft", f"{prefix} Fuselage/Chine Body"
        )

    def _create_wing(
        self,
        transaction: FeatureTransaction,
        scaled: ScaledSR71Geometry,
        prefix: str,
    ) -> None:
        import adsk.core
        import adsk.fusion

        sketch = self._create_xy_sketch(
            transaction,
            -scaled.wing_thickness_cm / 2,
            f"{prefix} Planform Sketch",
        )

        right_points = scaled.right_planform_points_cm
        vertices = list(right_points) + [
            (x_cm, -y_cm) for x_cm, y_cm in reversed(right_points[1:-1])
        ]
        self._add_closed_polygon(sketch, vertices, "SR-71 planform")
        profile = self._require_profile(sketch, "SR-71 planform")

        extrudes = transaction.component.features.extrudeFeatures
        extrude_input = extrudes.createInput(
            profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        if extrude_input is None:
            raise RuntimeError("Unable to create SR-71 wing extrusion input.")
        thickness = adsk.core.ValueInput.createByReal(scaled.wing_thickness_cm)
        if thickness is None:
            raise RuntimeError("Unable to create SR-71 wing thickness value.")
        extrude_input.setDistanceExtent(False, thickness)
        wing = extrudes.add(extrude_input)
        if wing is None:
            raise RuntimeError("Unable to create SR-71 wing extrusion.")
        transaction.track_feature(wing)
        self._name_feature_body(wing, f"{prefix} Wing Extrusion", f"{prefix} Wing Body")

    def _create_nacelle(
        self,
        transaction: FeatureTransaction,
        scaled: ScaledSR71Geometry,
        prefix: str,
        *,
        side_name: str,
        sign: int,
    ) -> None:
        import adsk.core

        profiles = []
        for index, station in enumerate(scaled.nacelle_stations, start=1):
            sketch = self._create_yz_sketch(
                transaction,
                station.position_cm,
                f"{prefix} {side_name} Nacelle Station {index:02d}",
            )
            centre = adsk.core.Point3D.create(sign * station.center_y_cm, station.center_z_cm, 0)
            major = adsk.core.Point3D.create(
                sign * station.center_y_cm + station.half_width_cm,
                station.center_z_cm,
                0,
            )
            minor = adsk.core.Point3D.create(
                sign * station.center_y_cm,
                station.center_z_cm + station.half_height_cm,
                0,
            )
            ellipse = sketch.sketchCurves.sketchEllipses.add(centre, major, minor)
            if ellipse is None:
                raise RuntimeError(
                    f"{side_name} nacelle station {index:02d}: unable to create profile."
                )
            profiles.append(
                self._require_profile(sketch, f"{side_name} nacelle station {index:02d}")
            )

        loft = self._create_solid_loft(transaction, profiles, f"{side_name.lower()} nacelle")
        self._name_feature_body(
            loft,
            f"{prefix} {side_name} Nacelle Loft",
            f"{prefix} {side_name} Nacelle Body",
        )

    def _create_canopy(
        self,
        transaction: FeatureTransaction,
        scaled: ScaledSR71Geometry,
        prefix: str,
    ) -> None:
        import adsk.core

        profiles = []
        for index, station in enumerate(scaled.canopy_stations, start=1):
            sketch = self._create_yz_sketch(
                transaction,
                station.position_cm,
                f"{prefix} Canopy Station {index:02d}",
            )
            centre = adsk.core.Point3D.create(0, station.center_z_cm, 0)
            major = adsk.core.Point3D.create(station.half_width_cm, station.center_z_cm, 0)
            minor = adsk.core.Point3D.create(0, station.center_z_cm + station.half_height_cm, 0)
            ellipse = sketch.sketchCurves.sketchEllipses.add(centre, major, minor)
            if ellipse is None:
                raise RuntimeError(f"Canopy station {index:02d}: unable to create profile.")
            profiles.append(self._require_profile(sketch, f"Canopy station {index:02d}"))

        loft = self._create_solid_loft(transaction, profiles, "canopy")
        self._name_feature_body(loft, f"{prefix} Canopy Loft", f"{prefix} Canopy Body")

    def _create_tail(
        self,
        transaction: FeatureTransaction,
        scaled: ScaledSR71Geometry,
        prefix: str,
        *,
        side_name: str,
        sign: int,
    ) -> None:
        tail = scaled.tail
        tail_sections = (
            (tail.root_leading_x_cm, tail.root_height_cm, "Leading"),
            (tail.tip_x_cm, tail.tip_height_cm, "Tip"),
            (tail.root_trailing_x_cm, tail.root_height_cm, "Trailing"),
        )
        profiles = []
        for index, (position_cm, height_cm, section_name) in enumerate(tail_sections, start=1):
            sketch = self._create_yz_sketch(
                transaction,
                position_cm,
                f"{prefix} {side_name} Tail {section_name} Station",
            )
            self._add_tail_profile(
                sketch,
                root_y_cm=tail.root_y_cm,
                height_cm=height_cm,
                tip_height_cm=tail.tip_height_cm,
                outward_tip_offset_cm=tail.outward_tip_offset_cm,
                tail_thickness_cm=tail.tail_thickness_cm,
                wing_thickness_cm=scaled.wing_thickness_cm,
                sign=sign,
                label=f"{side_name} tail station {index:02d}",
            )
            profiles.append(self._require_profile(sketch, f"{side_name} tail station {index:02d}"))
        loft = self._create_solid_loft(transaction, profiles, f"{side_name.lower()} tail")
        self._name_feature_body(
            loft, f"{prefix} {side_name} Tail Loft", f"{prefix} {side_name} Tail Body"
        )

    @staticmethod
    def _create_yz_sketch(
        transaction: FeatureTransaction, offset_cm: float, name: str
    ) -> adsk.fusion.Sketch:
        """Create a named YZ sketch, reusing the origin plane for zero offset."""
        component = transaction.component
        sketch_plane = component.yZConstructionPlane
        if not uses_origin_plane(offset_cm):
            sketch_plane = SR71Builder._create_offset_plane(
                transaction,
                component.yZConstructionPlane,
                offset_cm,
                f"{name} Plane",
            )
        return SR71Builder._create_sketch(transaction, sketch_plane, name)

    @staticmethod
    def _create_xy_sketch(
        transaction: FeatureTransaction, offset_cm: float, name: str
    ) -> adsk.fusion.Sketch:
        """Create a named XY sketch, reusing the origin plane for zero offset."""
        component = transaction.component
        sketch_plane = component.xYConstructionPlane
        if not uses_origin_plane(offset_cm):
            sketch_plane = SR71Builder._create_offset_plane(
                transaction,
                component.xYConstructionPlane,
                offset_cm,
                f"{name} Plane",
            )
        return SR71Builder._create_sketch(transaction, sketch_plane, name)

    @staticmethod
    def _create_offset_plane(
        transaction: FeatureTransaction,
        base_plane: object,
        offset_cm: float,
        name: str,
    ) -> adsk.fusion.ConstructionPlane:
        import adsk.core

        component = transaction.component
        plane_input = component.constructionPlanes.createInput()
        if plane_input is None:
            raise RuntimeError(
                f"Unable to create construction-plane input for {name} at {offset_cm:g} cm."
            )
        offset = adsk.core.ValueInput.createByReal(offset_cm)
        if offset is None or not plane_input.setByOffset(base_plane, offset):
            raise RuntimeError(f"Unable to define construction plane {name} at {offset_cm:g} cm.")
        plane = component.constructionPlanes.add(plane_input)
        if plane is None:
            raise RuntimeError(f"Unable to create construction plane {name} at {offset_cm:g} cm.")
        transaction.track_offset_plane(plane)
        plane.name = name
        return plane

    @staticmethod
    def _create_sketch(
        transaction: FeatureTransaction, plane: object, name: str
    ) -> adsk.fusion.Sketch:
        sketch = transaction.component.sketches.add(plane)
        if sketch is None:
            raise RuntimeError(f"Unable to create sketch {name}.")
        transaction.track_sketch(sketch)
        sketch.name = name
        return sketch

    @staticmethod
    def _add_fuselage_profile(
        sketch: adsk.fusion.Sketch,
        station: ScaledFuselageStation,
        station_index: int,
    ) -> None:
        """Create a faceted chine-like section with a flatter lower contour."""
        width = station.half_width_cm
        upper = station.upper_height_cm
        lower = station.lower_height_cm
        SR71Builder._add_closed_polygon(
            sketch,
            (
                (0, upper),
                (width * 0.48, upper * 0.82),
                (width * 0.98, upper * 0.28),
                (width, -lower * 0.18),
                (width * 0.76, -lower * 0.75),
                (0, -lower),
                (-width * 0.76, -lower * 0.75),
                (-width, -lower * 0.18),
                (-width * 0.98, upper * 0.28),
                (-width * 0.48, upper * 0.82),
            ),
            f"Fuselage station {station_index:02d}",
        )

    @staticmethod
    def _add_tail_profile(
        sketch: adsk.fusion.Sketch,
        *,
        root_y_cm: float,
        height_cm: float,
        tip_height_cm: float,
        outward_tip_offset_cm: float,
        tail_thickness_cm: float,
        wing_thickness_cm: float,
        sign: int,
        label: str,
    ) -> None:
        """Create one thin, laterally canted YZ tail section.

        The profile's upper edge moves outward with height, while its lateral
        width stays at ``tail_thickness_cm``. This keeps cant and physical
        thickness independent in the resulting native loft.
        """
        lower_z = -wing_thickness_cm / 2
        upper_z = lower_z + height_cm
        lower_center_y = sign * root_y_cm
        upper_center_y = sign * (root_y_cm + outward_tip_offset_cm * (height_cm / tip_height_cm))
        half_thickness = tail_thickness_cm / 2
        SR71Builder._add_closed_polygon(
            sketch,
            (
                (lower_center_y - half_thickness, lower_z),
                (lower_center_y + half_thickness, lower_z),
                (upper_center_y + half_thickness, upper_z),
                (upper_center_y - half_thickness, upper_z),
            ),
            label,
        )

    @staticmethod
    def _add_closed_polygon(
        sketch: adsk.fusion.Sketch,
        vertices: Iterable[tuple[float, float]],
        label: str,
    ) -> None:
        import adsk.core

        points = tuple(adsk.core.Point3D.create(x_cm, y_cm, 0) for x_cm, y_cm in vertices)
        if len(points) < 3:
            raise RuntimeError(f"{label}: a closed profile requires at least three points.")
        for start_point, end_point in zip(points, (*points[1:], points[0])):
            line = sketch.sketchCurves.sketchLines.addByTwoPoints(start_point, end_point)
            if line is None:
                raise RuntimeError(f"{label}: unable to create a profile edge.")

    @staticmethod
    def _require_profile(sketch: adsk.fusion.Sketch, label: str) -> adsk.fusion.Profile:
        if sketch.profiles.count != 1:
            raise RuntimeError(
                f"{label}: expected one closed profile, found {sketch.profiles.count}."
            )
        profile = sketch.profiles.item(0)
        if profile is None:
            raise RuntimeError(f"{label}: unable to retrieve profile.")
        return profile

    @staticmethod
    def _create_solid_loft(
        transaction: FeatureTransaction,
        profiles: Iterable[adsk.fusion.Profile],
        label: str,
    ) -> adsk.fusion.LoftFeature:
        import adsk.fusion

        loft_features = transaction.component.features.loftFeatures
        loft_input = loft_features.createInput(
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        if loft_input is None:
            raise RuntimeError(f"Unable to create {label} loft input.")
        loft_input.isSolid = True
        for index, profile in enumerate(profiles, start=1):
            if loft_input.loftSections.add(profile) is None:
                raise RuntimeError(f"Unable to add {label} loft section {index:02d}.")
        loft = loft_features.add(loft_input)
        if loft is None:
            raise RuntimeError(f"Unable to create {label} loft.")
        transaction.track_feature(loft)
        return loft

    @staticmethod
    def _name_feature_body(feature: object, feature_name: str, body_name: str) -> None:
        feature.name = feature_name
        if feature.bodies.count != 1:
            raise RuntimeError(f"{feature_name}: expected one generated body.")
        body = feature.bodies.item(0)
        if body is None:
            raise RuntimeError(f"{feature_name}: unable to retrieve generated body.")
        body.name = body_name
