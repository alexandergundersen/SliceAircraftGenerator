"""Pure, normalized geometry data for a recognizable SR-71 approximation.

Coordinate convention: X runs nose-to-tail, Y runs laterally, and Z is vertical.
All X positions are normalized from 0.0 at the nose to 1.0 at the tail. The
stored planform, nacelle, and tail data describe the right half; left geometry
is derived by mirroring across the XZ center plane.

The 32.741 m length and 16.942 m span are sourced from the Smithsonian National
Air and Space Museum collection record. All contours in this module are artistic
fabrication-oriented approximations, not engineering or restoration data.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

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
    """A normalized asymmetric vertical fuselage/chine cross-section."""

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
    """A right nacelle station; the left nacelle mirrors its lateral offset."""

    position: float
    center_y_ratio: float
    center_z_ratio: float
    half_width_ratio: float
    half_height_ratio: float

    def __post_init__(self) -> None:
        _require_normalized(self.position, "Nacelle station position")
        _require_finite_positive(self.center_y_ratio, "Nacelle center Y ratio")
        if not isfinite(self.center_z_ratio):
            raise ValueError("Nacelle center Z ratio must be finite.")
        _require_finite_positive(self.half_width_ratio, "Nacelle half-width ratio")
        _require_finite_positive(self.half_height_ratio, "Nacelle half-height ratio")


@dataclass(frozen=True)
class CanopyStation:
    """A normalized canopy cross-section centered on the XZ plane."""

    position: float
    center_z_ratio: float
    half_width_ratio: float
    half_height_ratio: float

    def __post_init__(self) -> None:
        _require_normalized(self.position, "Canopy station position")
        _require_finite_positive(self.center_z_ratio, "Canopy center Z ratio")
        _require_finite_positive(self.half_width_ratio, "Canopy half-width ratio")
        _require_finite_positive(self.half_height_ratio, "Canopy half-height ratio")


@dataclass(frozen=True)
class TailGeometry:
    """Normalized proportions for one canted tail, mirrored for the other side."""

    root_leading_x_ratio: float
    root_trailing_x_ratio: float
    tip_x_ratio: float
    root_height_ratio: float
    tip_height_ratio: float
    root_y_ratio: float
    outward_tip_offset_ratio: float
    tail_thickness_ratio: float

    def __post_init__(self) -> None:
        for field_name, value in (
            ("Tail root leading X ratio", self.root_leading_x_ratio),
            ("Tail root trailing X ratio", self.root_trailing_x_ratio),
            ("Tail tip X ratio", self.tip_x_ratio),
        ):
            _require_normalized(value, field_name)
        if self.root_trailing_x_ratio <= self.root_leading_x_ratio:
            raise ValueError("Tail root trailing X ratio must follow the leading X ratio.")
        _require_finite_positive(self.root_height_ratio, "Tail root height ratio")
        _require_finite_positive(self.tip_height_ratio, "Tail tip height ratio")
        _require_finite_positive(self.root_y_ratio, "Tail root Y ratio")
        _require_finite_positive(self.outward_tip_offset_ratio, "Tail outward offset ratio")
        _require_finite_positive(self.tail_thickness_ratio, "Tail thickness ratio")


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


@dataclass(frozen=True)
class ScaledCanopyStation:
    position_cm: float
    center_z_cm: float
    half_width_cm: float
    half_height_cm: float


@dataclass(frozen=True)
class ScaledTailGeometry:
    root_leading_x_cm: float
    root_trailing_x_cm: float
    tip_x_cm: float
    root_height_cm: float
    tip_height_cm: float
    root_y_cm: float
    outward_tip_offset_cm: float
    tail_thickness_cm: float


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
        """Return the sourced half-span, which is set by the outer wing tips."""
        return self.wingspan_cm / 2

    @property
    def maximum_fuselage_half_width_cm(self) -> float:
        """Return the widest central fuselage/chine station."""
        return max(station.half_width_cm for station in self.fuselage_stations)

    @property
    def maximum_nacelle_outer_edge_cm(self) -> float:
        """Return the furthest nacelle edge from the XZ center plane."""
        return max(station.center_y_cm + station.half_width_cm for station in self.nacelle_stations)

    @property
    def nacelle_tip_margin_cm(self) -> float:
        """Return the wing width visibly remaining outside the nacelles."""
        return self.half_span_cm - self.maximum_nacelle_outer_edge_cm

    @property
    def nacelle_centerline_variation_cm(self) -> float:
        """Return the full lateral variation across nacelle station centers."""
        offsets = tuple(station.center_y_cm for station in self.nacelle_stations)
        return max(offsets) - min(offsets)

    @property
    def maximum_canopy_half_width_cm(self) -> float:
        """Return the widest canopy station."""
        return max(station.half_width_cm for station in self.canopy_stations)

    @property
    def maximum_canopy_half_height_cm(self) -> float:
        """Return the tallest canopy half-height."""
        return max(station.half_height_cm for station in self.canopy_stations)

    def mirrored_planform_points_cm(self) -> tuple[tuple[float, float], ...]:
        """Return the left-side mirror of the right half-planform."""
        return tuple((x_cm, -y_cm) for x_cm, y_cm in self.right_planform_points_cm)

    def nacelle_center_offsets_cm(self) -> tuple[float, float]:
        """Return the deterministic left/right nacelle center offsets."""
        maximum_offset = max(station.center_y_cm for station in self.nacelle_stations)
        return (-maximum_offset, maximum_offset)

    def tail_root_offsets_cm(self) -> tuple[float, float]:
        """Return the deterministic left/right tail-root offsets."""
        return (-self.tail.root_y_cm, self.tail.root_y_cm)


@dataclass(frozen=True)
class SR71GeometryData:
    """Normalized SR-71 approximation data, independent from Fusion APIs."""

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
                tip_x_cm=self.tail.tip_x_ratio * length_cm,
                root_height_cm=self.tail.root_height_ratio * length_cm,
                tip_height_cm=self.tail.tip_height_ratio * length_cm,
                root_y_cm=self.tail.root_y_ratio * length_cm,
                outward_tip_offset_cm=self.tail.outward_tip_offset_ratio * length_cm,
                tail_thickness_cm=self.tail.tail_thickness_ratio * length_cm,
            ),
        )


SR71_DATA = SR71GeometryData(
    fuselage_stations=(
        FuselageStation(0.000, 0.002, 0.002, 0.001),
        FuselageStation(0.030, 0.008, 0.006, 0.003),
        FuselageStation(0.120, 0.025, 0.014, 0.007),
        FuselageStation(0.200, 0.034, 0.019, 0.009),
        FuselageStation(0.360, 0.052, 0.026, 0.012),
        FuselageStation(0.560, 0.062, 0.030, 0.014),
        FuselageStation(0.740, 0.057, 0.026, 0.013),
        FuselageStation(0.880, 0.041, 0.019, 0.010),
        FuselageStation(0.970, 0.014, 0.009, 0.005),
        FuselageStation(1.000, 0.003, 0.003, 0.002),
    ),
    right_planform_points=(
        PlanformPoint(0.000, 0.000),
        PlanformPoint(0.080, 0.006),
        PlanformPoint(0.180, 0.024),
        PlanformPoint(0.360, 0.100),
        PlanformPoint(0.580, SOURCE_WINGSPAN_RATIO / 2),
        PlanformPoint(0.730, 0.245),
        PlanformPoint(0.880, 0.120),
        PlanformPoint(0.980, 0.018),
        PlanformPoint(1.000, 0.000),
    ),
    nacelle_stations=(
        NacelleStation(0.300, 0.140, -0.004, 0.026, 0.022),
        NacelleStation(0.420, 0.145, -0.007, 0.038, 0.030),
        NacelleStation(0.690, 0.150, -0.010, 0.043, 0.033),
        NacelleStation(0.880, 0.148, -0.008, 0.035, 0.027),
        NacelleStation(0.970, 0.140, -0.005, 0.016, 0.014),
    ),
    canopy_stations=(
        CanopyStation(0.150, 0.020, 0.008, 0.005),
        CanopyStation(0.200, 0.028, 0.015, 0.011),
        CanopyStation(0.260, 0.035, 0.022, 0.017),
        CanopyStation(0.320, 0.032, 0.016, 0.011),
        CanopyStation(0.380, 0.025, 0.008, 0.005),
    ),
    tail=TailGeometry(
        root_leading_x_ratio=0.700,
        root_trailing_x_ratio=0.890,
        tip_x_ratio=0.790,
        root_height_ratio=0.012,
        tip_height_ratio=0.115,
        root_y_ratio=0.145,
        outward_tip_offset_ratio=0.025,
        tail_thickness_ratio=0.006,
    ),
    wing_thickness_ratio=0.0065,
)
