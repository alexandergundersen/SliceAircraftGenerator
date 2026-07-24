"""Pure, normalized data for a fabrication-oriented SR-71 silhouette.

Coordinates use X nose-to-tail, Y lateral, and Z vertical. The right-side
planform, nacelle, and tail values are mirrored across the XZ center plane.
Only the sourced overall span-to-length ratio is factual reference data; every
contour in this module is a deterministic artistic approximation for a readable,
editable Fusion display model.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, radians, tan

SOURCE_LENGTH_M = 32.741
SOURCE_WINGSPAN_M = 16.942
SOURCE_WINGSPAN_RATIO = SOURCE_WINGSPAN_M / SOURCE_LENGTH_M
DEFAULT_MODEL_LENGTH_CM = 30.0


def _require_finite_positive(value: float, field_name: str) -> None:
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{field_name} must be a finite value greater than zero.")


def _require_finite_nonnegative(value: float, field_name: str) -> None:
    if not isfinite(value) or value < 0:
        raise ValueError(f"{field_name} must be a finite value greater than or equal to zero.")


def _require_normalized(value: float, field_name: str) -> None:
    if not isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{field_name} must be finite and between 0 and 1 inclusive.")


@dataclass(frozen=True)
class FuselageStation:
    """A normalized low, asymmetric fuselage/chine cross-section."""

    position: float
    half_width_ratio: float
    upper_height_ratio: float
    lower_height_ratio: float

    def __post_init__(self) -> None:
        _require_normalized(self.position, "Fuselage station position")
        _require_finite_positive(self.half_width_ratio, "Fuselage half-width ratio")
        _require_finite_positive(self.upper_height_ratio, "Fuselage upper-height ratio")
        _require_finite_positive(self.lower_height_ratio, "Fuselage lower-height ratio")


@dataclass(frozen=True)
class PlanformPoint:
    """A right-side normalized planform point measured from the centerline."""

    x_ratio: float
    y_ratio: float

    def __post_init__(self) -> None:
        _require_normalized(self.x_ratio, "Planform X ratio")
        _require_finite_nonnegative(self.y_ratio, "Planform Y ratio")


@dataclass(frozen=True)
class NacelleStation:
    """A right nacelle station, including its required outer-wing margin."""

    position: float
    center_y_ratio: float
    center_z_ratio: float
    half_width_ratio: float
    half_height_ratio: float
    required_outer_wing_margin_ratio: float

    def __post_init__(self) -> None:
        _require_normalized(self.position, "Nacelle station position")
        _require_finite_positive(self.center_y_ratio, "Nacelle center Y ratio")
        if not isfinite(self.center_z_ratio):
            raise ValueError("Nacelle center Z ratio must be finite.")
        _require_finite_positive(self.half_width_ratio, "Nacelle half-width ratio")
        _require_finite_positive(self.half_height_ratio, "Nacelle half-height ratio")
        _require_finite_nonnegative(
            self.required_outer_wing_margin_ratio, "Nacelle outer-wing margin ratio"
        )


@dataclass(frozen=True)
class CanopyStation:
    """A normalized, centered canopy cross-section."""

    position: float
    center_z_ratio: float
    half_width_ratio: float
    half_height_ratio: float

    def __post_init__(self) -> None:
        _require_normalized(self.position, "Canopy station position")
        _require_finite_positive(self.center_z_ratio, "Canopy center Z ratio")
        _require_finite_positive(self.half_width_ratio, "Canopy half-width ratio")
        _require_finite_positive(self.half_height_ratio, "Canopy half-height ratio")

    @property
    def top_z_ratio(self) -> float:
        """Return the visual upper contour used for the tandem canopy profile."""
        return self.center_z_ratio + self.half_height_ratio


@dataclass(frozen=True)
class TailGeometry:
    """One thin, angular, canted tail side profile, mirrored for the other side."""

    root_leading_x_ratio: float
    root_trailing_x_ratio: float
    tip_leading_x_ratio: float
    tip_trailing_x_ratio: float
    base_z_ratio: float
    tip_z_ratio: float
    root_y_ratio: float
    tail_thickness_ratio: float
    outward_cant_angle_degrees: float

    def __post_init__(self) -> None:
        for field_name, value in (
            ("Tail root leading X ratio", self.root_leading_x_ratio),
            ("Tail root trailing X ratio", self.root_trailing_x_ratio),
            ("Tail tip leading X ratio", self.tip_leading_x_ratio),
            ("Tail tip trailing X ratio", self.tip_trailing_x_ratio),
        ):
            _require_normalized(value, field_name)
        if not (
            self.root_leading_x_ratio
            < self.tip_leading_x_ratio
            < self.tip_trailing_x_ratio
            < self.root_trailing_x_ratio
        ):
            raise ValueError("Tail side-profile X values must form a swept angular quadrilateral.")
        if not isfinite(self.base_z_ratio) or not isfinite(self.tip_z_ratio):
            raise ValueError("Tail Z ratios must be finite.")
        if self.tip_z_ratio <= self.base_z_ratio:
            raise ValueError("Tail tip Z ratio must be above the base Z ratio.")
        _require_finite_positive(self.root_y_ratio, "Tail root Y ratio")
        _require_finite_positive(self.tail_thickness_ratio, "Tail thickness ratio")
        _require_finite_positive(self.outward_cant_angle_degrees, "Tail outward cant angle")

    @property
    def outward_tip_offset_ratio(self) -> float:
        """Derive outward top displacement from the explicit cant angle."""
        return tan(radians(self.outward_cant_angle_degrees)) * (
            self.tip_z_ratio - self.base_z_ratio
        )

    @property
    def side_profile_points(self) -> tuple[tuple[float, float], ...]:
        """Return the angular XZ quadrilateral in drawing order."""
        return (
            (self.root_leading_x_ratio, self.base_z_ratio),
            (self.root_trailing_x_ratio, self.base_z_ratio),
            (self.tip_trailing_x_ratio, self.tip_z_ratio),
            (self.tip_leading_x_ratio, self.tip_z_ratio),
        )


@dataclass(frozen=True)
class ScaledFuselageStation:
    position_cm: float
    half_width_cm: float
    upper_height_cm: float
    lower_height_cm: float


@dataclass(frozen=True)
class ScaledNacelleStation:
    position_cm: float
    center_y_cm: float
    center_z_cm: float
    half_width_cm: float
    half_height_cm: float
    required_outer_wing_margin_cm: float


@dataclass(frozen=True)
class ScaledCanopyStation:
    position_cm: float
    center_z_cm: float
    half_width_cm: float
    half_height_cm: float

    @property
    def top_z_cm(self) -> float:
        return self.center_z_cm + self.half_height_cm


@dataclass(frozen=True)
class ScaledTailGeometry:
    root_leading_x_cm: float
    root_trailing_x_cm: float
    tip_leading_x_cm: float
    tip_trailing_x_cm: float
    base_z_cm: float
    tip_z_cm: float
    root_y_cm: float
    tail_thickness_cm: float
    outward_cant_angle_degrees: float

    @property
    def outward_tip_offset_cm(self) -> float:
        return tan(radians(self.outward_cant_angle_degrees)) * (self.tip_z_cm - self.base_z_cm)

    @property
    def side_profile_points_cm(self) -> tuple[tuple[float, float], ...]:
        return (
            (self.root_leading_x_cm, self.base_z_cm),
            (self.root_trailing_x_cm, self.base_z_cm),
            (self.tip_trailing_x_cm, self.tip_z_cm),
            (self.tip_leading_x_cm, self.tip_z_cm),
        )


@dataclass(frozen=True)
class ScaledSR71Geometry:
    """Deterministic absolute dimensions for one requested model length."""

    length_cm: float
    wingspan_cm: float
    wing_thickness_cm: float
    fuselage_stations: tuple[ScaledFuselageStation, ...]
    right_planform_points_cm: tuple[tuple[float, float], ...]
    nacelle_stations: tuple[ScaledNacelleStation, ...]
    canopy_stations: tuple[ScaledCanopyStation, ...]
    tail: ScaledTailGeometry

    @property
    def half_span_cm(self) -> float:
        return self.wingspan_cm / 2

    @property
    def maximum_fuselage_half_width_cm(self) -> float:
        return max(station.half_width_cm for station in self.fuselage_stations)

    @property
    def maximum_fuselage_upper_height_cm(self) -> float:
        return max(station.upper_height_cm for station in self.fuselage_stations)

    @property
    def maximum_nacelle_outer_edge_cm(self) -> float:
        return max(station.center_y_cm + station.half_width_cm for station in self.nacelle_stations)

    @property
    def nacelle_tip_margin_cm(self) -> float:
        return self.half_span_cm - self.maximum_nacelle_outer_edge_cm

    @property
    def nacelle_centerline_variation_cm(self) -> float:
        offsets = tuple(station.center_y_cm for station in self.nacelle_stations)
        return max(offsets) - min(offsets)

    @property
    def maximum_canopy_half_width_cm(self) -> float:
        return max(station.half_width_cm for station in self.canopy_stations)

    @property
    def maximum_canopy_half_height_cm(self) -> float:
        return max(station.half_height_cm for station in self.canopy_stations)

    @property
    def canopy_top_profile_cm(self) -> tuple[tuple[float, float], ...]:
        return tuple((station.position_cm, station.top_z_cm) for station in self.canopy_stations)

    def planform_half_width_at_cm(self, x_cm: float) -> float:
        """Interpolate the scaled right-side planform envelope at one X position."""
        if not isfinite(x_cm) or not 0 <= x_cm <= self.length_cm:
            raise ValueError("Planform X position must be finite and within the model length.")
        return _interpolate_planform_points(self.right_planform_points_cm, x_cm)

    def nacelle_outer_wing_margins_cm(self) -> tuple[float, ...]:
        """Return the actual remaining wing width beyond each nacelle station."""
        return tuple(
            self.planform_half_width_at_cm(station.position_cm)
            - station.center_y_cm
            - station.half_width_cm
            for station in self.nacelle_stations
        )

    def nacelles_overlap_wing_vertically(self) -> bool:
        """Return whether every nacelle section intersects the centered wing slab."""
        wing_lower = -self.wing_thickness_cm / 2
        wing_upper = self.wing_thickness_cm / 2
        return all(
            station.center_z_cm - station.half_height_cm <= wing_upper
            and station.center_z_cm + station.half_height_cm >= wing_lower
            for station in self.nacelle_stations
        )

    def mirrored_planform_points_cm(self) -> tuple[tuple[float, float], ...]:
        return tuple((x_cm, -y_cm) for x_cm, y_cm in self.right_planform_points_cm)

    def nacelle_center_offsets_cm(self) -> tuple[float, float]:
        maximum_offset = max(station.center_y_cm for station in self.nacelle_stations)
        return (-maximum_offset, maximum_offset)

    def tail_root_offsets_cm(self) -> tuple[float, float]:
        return (-self.tail.root_y_cm, self.tail.root_y_cm)


@dataclass(frozen=True)
class SR71GeometryData:
    """Normalized SR-71 silhouette data, independent from Fusion APIs."""

    fuselage_stations: tuple[FuselageStation, ...]
    right_planform_points: tuple[PlanformPoint, ...]
    nacelle_stations: tuple[NacelleStation, ...]
    canopy_stations: tuple[CanopyStation, ...]
    tail: TailGeometry
    wing_thickness_ratio: float

    def __post_init__(self) -> None:
        _require_finite_positive(self.wing_thickness_ratio, "Wing thickness ratio")
        self._validate_order(self.fuselage_stations, "Fuselage")
        self._validate_order(self.nacelle_stations, "Nacelle")
        self._validate_order(self.canopy_stations, "Canopy")
        if len(self.right_planform_points) < 3:
            raise ValueError("The half-planform requires at least three control points.")
        planform_x_positions = tuple(point.x_ratio for point in self.right_planform_points)
        if any(
            next_position <= position
            for position, next_position in zip(planform_x_positions, planform_x_positions[1:])
        ):
            raise ValueError("Planform X positions must be strictly increasing.")

    @staticmethod
    def _validate_order(stations: tuple[object, ...], label: str) -> None:
        if len(stations) < 2:
            raise ValueError(f"{label} stations require at least two entries.")
        positions = tuple(station.position for station in stations)
        if any(
            next_position <= position for position, next_position in zip(positions, positions[1:])
        ):
            raise ValueError(f"{label} station positions must be strictly increasing.")

    def planform_half_width_at(self, x_ratio: float) -> float:
        """Piecewise-linearly interpolate the normalized right-side envelope."""
        _require_normalized(x_ratio, "Planform X ratio")
        return _interpolate_planform_points(
            tuple((point.x_ratio, point.y_ratio) for point in self.right_planform_points), x_ratio
        )

    def scale(self, length_cm: float) -> ScaledSR71Geometry:
        """Scale all normalized dimensions linearly to ``length_cm``."""
        _require_finite_positive(length_cm, "Requested aircraft length")
        return ScaledSR71Geometry(
            length_cm=length_cm,
            wingspan_cm=length_cm * SOURCE_WINGSPAN_RATIO,
            wing_thickness_cm=length_cm * self.wing_thickness_ratio,
            fuselage_stations=tuple(
                ScaledFuselageStation(
                    position_cm=station.position * length_cm,
                    half_width_cm=station.half_width_ratio * length_cm,
                    upper_height_cm=station.upper_height_ratio * length_cm,
                    lower_height_cm=station.lower_height_ratio * length_cm,
                )
                for station in self.fuselage_stations
            ),
            right_planform_points_cm=tuple(
                (point.x_ratio * length_cm, point.y_ratio * length_cm)
                for point in self.right_planform_points
            ),
            nacelle_stations=tuple(
                ScaledNacelleStation(
                    position_cm=station.position * length_cm,
                    center_y_cm=station.center_y_ratio * length_cm,
                    center_z_cm=station.center_z_ratio * length_cm,
                    half_width_cm=station.half_width_ratio * length_cm,
                    half_height_cm=station.half_height_ratio * length_cm,
                    required_outer_wing_margin_cm=(
                        station.required_outer_wing_margin_ratio * length_cm
                    ),
                )
                for station in self.nacelle_stations
            ),
            canopy_stations=tuple(
                ScaledCanopyStation(
                    position_cm=station.position * length_cm,
                    center_z_cm=station.center_z_ratio * length_cm,
                    half_width_cm=station.half_width_ratio * length_cm,
                    half_height_cm=station.half_height_ratio * length_cm,
                )
                for station in self.canopy_stations
            ),
            tail=ScaledTailGeometry(
                root_leading_x_cm=self.tail.root_leading_x_ratio * length_cm,
                root_trailing_x_cm=self.tail.root_trailing_x_ratio * length_cm,
                tip_leading_x_cm=self.tail.tip_leading_x_ratio * length_cm,
                tip_trailing_x_cm=self.tail.tip_trailing_x_ratio * length_cm,
                base_z_cm=self.tail.base_z_ratio * length_cm,
                tip_z_cm=self.tail.tip_z_ratio * length_cm,
                root_y_cm=self.tail.root_y_ratio * length_cm,
                tail_thickness_cm=self.tail.tail_thickness_ratio * length_cm,
                outward_cant_angle_degrees=self.tail.outward_cant_angle_degrees,
            ),
        )


def _interpolate_planform_points(points: tuple[tuple[float, float], ...], x_value: float) -> float:
    """Return a deterministic piecewise-linear Y value for validated points."""
    for point_x, point_y in points:
        if x_value == point_x:
            return point_y
    for (left_x, left_y), (right_x, right_y) in zip(points, points[1:]):
        if left_x < x_value < right_x:
            fraction = (x_value - left_x) / (right_x - left_x)
            return left_y + fraction * (right_y - left_y)
    raise ValueError("Planform X position is outside the available control points.")


SR71_DATA = SR71GeometryData(
    fuselage_stations=(
        FuselageStation(0.000, 0.001, 0.001, 0.0005),
        FuselageStation(0.030, 0.006, 0.004, 0.002),
        FuselageStation(0.120, 0.020, 0.012, 0.005),
        FuselageStation(0.220, 0.028, 0.017, 0.007),
        FuselageStation(0.350, 0.037, 0.022, 0.010),
        FuselageStation(0.520, 0.044, 0.023, 0.010),
        FuselageStation(0.700, 0.041, 0.021, 0.009),
        FuselageStation(0.860, 0.030, 0.015, 0.007),
        FuselageStation(0.960, 0.012, 0.006, 0.003),
        FuselageStation(1.000, 0.002, 0.001, 0.0005),
    ),
    right_planform_points=(
        PlanformPoint(0.000, 0.000),
        PlanformPoint(0.080, 0.006),
        PlanformPoint(0.150, 0.018),
        PlanformPoint(0.250, 0.075),
        PlanformPoint(0.360, 0.165),
        PlanformPoint(0.540, SOURCE_WINGSPAN_RATIO / 2),
        PlanformPoint(0.700, 0.235),
        PlanformPoint(0.860, 0.205),
        PlanformPoint(0.920, 0.180),
        PlanformPoint(0.960, 0.150),
        PlanformPoint(0.990, 0.045),
        PlanformPoint(1.000, 0.000),
    ),
    nacelle_stations=(
        NacelleStation(0.360, 0.118, -0.003, 0.028, 0.024, 0.008),
        NacelleStation(0.460, 0.122, -0.004, 0.034, 0.028, 0.020),
        NacelleStation(0.700, 0.125, -0.004, 0.035, 0.029, 0.020),
        NacelleStation(0.860, 0.123, -0.003, 0.031, 0.027, 0.020),
        NacelleStation(0.960, 0.118, -0.003, 0.016, 0.016, 0.008),
    ),
    canopy_stations=(
        CanopyStation(0.150, 0.016, 0.006, 0.004),
        CanopyStation(0.190, 0.018, 0.015, 0.012),
        CanopyStation(0.225, 0.017, 0.012, 0.006),
        CanopyStation(0.260, 0.019, 0.016, 0.013),
        CanopyStation(0.320, 0.016, 0.006, 0.004),
    ),
    tail=TailGeometry(
        root_leading_x_ratio=0.720,
        root_trailing_x_ratio=0.900,
        tip_leading_x_ratio=0.780,
        tip_trailing_x_ratio=0.840,
        base_z_ratio=-0.00325,
        tip_z_ratio=0.095,
        root_y_ratio=0.123,
        tail_thickness_ratio=0.005,
        outward_cant_angle_degrees=15.0,
    ),
    wing_thickness_ratio=0.0065,
)


def planform_half_width_at(x_ratio: float) -> float:
    """Return the default SR-71 normalized half-width at ``x_ratio``."""
    return SR71_DATA.planform_half_width_at(x_ratio)
