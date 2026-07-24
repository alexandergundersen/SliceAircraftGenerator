"""Pure-Python design-invariant tests for normalized SR-71 silhouette data."""

import math
from dataclasses import replace

import pytest

from geometry.sr71_data import (
    DEFAULT_MODEL_LENGTH_CM,
    SOURCE_WINGSPAN_RATIO,
    SR71_DATA,
    FuselageStation,
    PlanformPoint,
    planform_half_width_at,
)


def test_verified_length_to_wingspan_scaling() -> None:
    scaled = SR71_DATA.scale(DEFAULT_MODEL_LENGTH_CM)

    assert math.isclose(scaled.wingspan_cm / scaled.length_cm, SOURCE_WINGSPAN_RATIO)


def test_default_300_mm_model_has_expected_wingspan() -> None:
    scaled = SR71_DATA.scale(30.0)

    assert math.isclose(scaled.wingspan_cm, 30.0 * SOURCE_WINGSPAN_RATIO)


def test_planform_interpolation_is_exact_at_every_control_point() -> None:
    for point in SR71_DATA.right_planform_points:
        assert planform_half_width_at(point.x_ratio) == point.y_ratio


def test_planform_interpolation_is_piecewise_linear_and_deterministic() -> None:
    left_point = SR71_DATA.right_planform_points[3]
    right_point = SR71_DATA.right_planform_points[4]
    midpoint = (left_point.x_ratio + right_point.x_ratio) / 2

    assert planform_half_width_at(midpoint) == pytest.approx(
        (left_point.y_ratio + right_point.y_ratio) / 2
    )
    assert planform_half_width_at(midpoint) == planform_half_width_at(midpoint)


@pytest.mark.parametrize("x_ratio", [math.nan, math.inf, -math.inf, -0.01, 1.01])
def test_planform_interpolation_rejects_invalid_positions(x_ratio: float) -> None:
    with pytest.raises(ValueError):
        planform_half_width_at(x_ratio)


def test_planform_is_continuous_at_each_control_point() -> None:
    points = SR71_DATA.right_planform_points

    for left_point, point, right_point in zip(points, points[1:], points[2:]):
        delta = min(point.x_ratio - left_point.x_ratio, right_point.x_ratio - point.x_ratio) / 1000
        assert planform_half_width_at(point.x_ratio - delta) == pytest.approx(
            point.y_ratio, abs=0.001
        )
        assert planform_half_width_at(point.x_ratio + delta) == pytest.approx(
            point.y_ratio, abs=0.001
        )


def test_planform_widens_sufficiently_before_the_nacelle_inlet() -> None:
    inlet = SR71_DATA.nacelle_stations[0]

    assert SR71_DATA.planform_half_width_at(0.15) < 0.020
    assert SR71_DATA.planform_half_width_at(inlet.position) >= (
        inlet.center_y_ratio + inlet.half_width_ratio + inlet.required_outer_wing_margin_ratio
    )


def test_wing_envelope_contains_every_nacelle_with_required_margin() -> None:
    scaled = SR71_DATA.scale(30.0)
    margins = scaled.nacelle_outer_wing_margins_cm()

    assert all(margin > 0 for margin in margins)
    assert all(
        margin >= station.required_outer_wing_margin_cm
        for margin, station in zip(margins, scaled.nacelle_stations)
    )


def test_every_nacelle_physically_intersects_the_wing_slab() -> None:
    assert SR71_DATA.scale(30.0).nacelles_overlap_wing_vertically()


def test_nacelles_remain_nearly_parallel_and_inside_the_wing_tips() -> None:
    scaled = SR71_DATA.scale(30.0)

    assert scaled.nacelle_centerline_variation_cm <= scaled.length_cm * 0.010
    assert scaled.maximum_nacelle_outer_edge_cm < scaled.half_span_cm


def test_wing_thickness_stays_within_the_fabrication_friendly_range() -> None:
    scaled = SR71_DATA.scale(30.0)

    assert 0.005 <= scaled.wing_thickness_cm / scaled.length_cm <= 0.008


def test_fuselage_is_low_narrow_and_gradually_tapered() -> None:
    scaled = SR71_DATA.scale(30.0)
    forward_station = scaled.fuselage_stations[2]
    middle_station = scaled.fuselage_stations[4]

    assert scaled.maximum_fuselage_half_width_cm / scaled.length_cm <= 0.045
    assert forward_station.half_width_cm / scaled.length_cm <= 0.022
    assert 0.032 <= middle_station.half_width_cm / scaled.length_cm <= 0.038
    assert scaled.maximum_fuselage_upper_height_cm / scaled.length_cm <= 0.024
    assert all(
        station.lower_height_cm <= station.upper_height_cm / 2
        for station in scaled.fuselage_stations
    )
    assert scaled.fuselage_stations[-2].half_width_cm < middle_station.half_width_cm


def test_canopy_has_two_subtle_peaks_with_an_intermediate_dip() -> None:
    profile = SR71_DATA.scale(30.0).canopy_top_profile_cm
    heights = tuple(height_cm for _, height_cm in profile)

    assert heights[1] > heights[0]
    assert heights[1] > heights[2]
    assert heights[3] > heights[2]
    assert heights[3] > heights[4]
    assert heights[2] < heights[1]
    assert heights[2] < heights[3]


def test_canopy_stays_small_and_centered() -> None:
    scaled = SR71_DATA.scale(30.0)

    assert scaled.maximum_canopy_half_width_cm / scaled.length_cm <= 0.018
    assert scaled.maximum_canopy_half_height_cm / scaled.length_cm <= 0.014
    assert scaled.canopy_stations[0].position_cm / scaled.length_cm == pytest.approx(0.15)
    assert scaled.canopy_stations[-1].position_cm / scaled.length_cm == pytest.approx(0.32)


def test_tail_has_an_angular_swept_quadrilateral_profile() -> None:
    tail = SR71_DATA.tail

    assert tail.root_leading_x_ratio < tail.tip_leading_x_ratio
    assert tail.tip_leading_x_ratio < tail.tip_trailing_x_ratio
    assert tail.tip_trailing_x_ratio < tail.root_trailing_x_ratio
    assert tail.tip_z_ratio > tail.base_z_ratio
    assert len(tail.side_profile_points) == 4


def test_tail_thickness_is_independent_from_cant_and_remains_thin() -> None:
    scaled = SR71_DATA.scale(30.0)
    modified_tail = replace(SR71_DATA.tail, tail_thickness_ratio=0.006)

    assert scaled.tail.tail_thickness_cm / scaled.length_cm <= 0.006
    assert 12 <= scaled.tail.outward_cant_angle_degrees <= 18
    assert scaled.tail.tail_thickness_cm != scaled.tail.outward_tip_offset_cm
    assert modified_tail.outward_cant_angle_degrees == SR71_DATA.tail.outward_cant_angle_degrees
    assert modified_tail.tail_thickness_ratio != SR71_DATA.tail.tail_thickness_ratio


def test_tail_roots_align_with_the_nacelle_mounting_region() -> None:
    scaled = SR71_DATA.scale(30.0)

    assert any(
        station.center_y_cm == pytest.approx(scaled.tail.root_y_cm)
        for station in scaled.nacelle_stations
    )
    assert any(
        abs(station.position_cm - scaled.tail.root_leading_x_cm) <= scaled.length_cm * 0.03
        for station in scaled.nacelle_stations
    )


def test_planform_has_a_deterministic_pointed_nose_and_tapered_tail() -> None:
    points = SR71_DATA.right_planform_points

    assert points[0] == PlanformPoint(0.0, 0.0)
    assert points[-1] == PlanformPoint(1.0, 0.0)
    assert points[2].y_ratio < 0.020
    assert points[-2].y_ratio > 0


def test_150_mm_and_300_mm_builds_preserve_normalized_silhouettes() -> None:
    half_scale = SR71_DATA.scale(15.0)
    full_scale = SR71_DATA.scale(30.0)

    assert full_scale.wingspan_cm / full_scale.length_cm == pytest.approx(
        half_scale.wingspan_cm / half_scale.length_cm
    )
    assert full_scale.maximum_fuselage_half_width_cm / full_scale.length_cm == pytest.approx(
        half_scale.maximum_fuselage_half_width_cm / half_scale.length_cm
    )
    assert full_scale.nacelle_outer_wing_margins_cm()[2] / full_scale.length_cm == pytest.approx(
        half_scale.nacelle_outer_wing_margins_cm()[2] / half_scale.length_cm
    )
    assert full_scale.tail.side_profile_points_cm == tuple(
        (x_cm * 2, z_cm * 2) for x_cm, z_cm in half_scale.tail.side_profile_points_cm
    )


def test_left_and_right_derived_geometry_is_exactly_symmetric() -> None:
    scaled = SR71_DATA.scale(30.0)

    assert scaled.mirrored_planform_points_cm() == tuple(
        (x_cm, -y_cm) for x_cm, y_cm in scaled.right_planform_points_cm
    )
    left_nacelle, right_nacelle = scaled.nacelle_center_offsets_cm()
    left_tail, right_tail = scaled.tail_root_offsets_cm()
    assert left_nacelle == -right_nacelle
    assert left_tail == -right_tail


def test_fuselage_and_nacelle_stations_are_strictly_ordered() -> None:
    scaled = SR71_DATA.scale(30.0)

    assert [station.position_cm for station in scaled.fuselage_stations] == sorted(
        station.position_cm for station in scaled.fuselage_stations
    )
    assert [station.position_cm for station in scaled.nacelle_stations] == sorted(
        station.position_cm for station in scaled.nacelle_stations
    )


def test_model_dimensions_are_positive() -> None:
    scaled = SR71_DATA.scale(30.0)

    assert scaled.wingspan_cm > 0
    assert scaled.wing_thickness_cm > 0
    assert all(station.half_width_cm > 0 for station in scaled.fuselage_stations)
    assert all(station.half_height_cm > 0 for station in scaled.nacelle_stations)


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_finite_value_validation(value: float) -> None:
    with pytest.raises(ValueError):
        FuselageStation(value, 0.1, 0.1, 0.1)


def test_planform_rejects_negative_lateral_offsets_but_allows_centerline_tip() -> None:
    with pytest.raises(ValueError, match="greater than or equal to zero"):
        PlanformPoint(0.5, -0.1)

    assert PlanformPoint(0.0, 0.0) == PlanformPoint(0.0, 0.0)


def test_geometry_data_is_deterministic() -> None:
    assert SR71_DATA.scale(30.0) == SR71_DATA.scale(30.0)
