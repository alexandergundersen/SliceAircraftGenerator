"""Pure-Python tests for normalized SR-71 approximation data."""

import math
from dataclasses import replace

import pytest

from geometry.sr71_data import (
    DEFAULT_MODEL_LENGTH_CM,
    SOURCE_WINGSPAN_RATIO,
    SR71_DATA,
    FuselageStation,
    PlanformPoint,
)


def test_verified_length_to_wingspan_scaling() -> None:
    scaled = SR71_DATA.scale(DEFAULT_MODEL_LENGTH_CM)

    assert math.isclose(scaled.wingspan_cm / scaled.length_cm, SOURCE_WINGSPAN_RATIO)


def test_default_300_mm_model_has_expected_wingspan() -> None:
    scaled = SR71_DATA.scale(30.0)

    assert math.isclose(scaled.wingspan_cm, 30.0 * SOURCE_WINGSPAN_RATIO)


def test_150_mm_and_300_mm_models_preserve_normalized_proportions() -> None:
    half_scale = SR71_DATA.scale(15.0)
    full_scale = SR71_DATA.scale(30.0)

    assert full_scale.wingspan_cm / full_scale.length_cm == pytest.approx(
        half_scale.wingspan_cm / half_scale.length_cm
    )
    assert full_scale.maximum_fuselage_half_width_cm / full_scale.length_cm == pytest.approx(
        half_scale.maximum_fuselage_half_width_cm / half_scale.length_cm
    )
    assert full_scale.maximum_nacelle_outer_edge_cm / full_scale.length_cm == pytest.approx(
        half_scale.maximum_nacelle_outer_edge_cm / half_scale.length_cm
    )
    assert full_scale.tail.tail_thickness_cm / full_scale.length_cm == pytest.approx(
        half_scale.tail.tail_thickness_cm / half_scale.length_cm
    )


def test_fuselage_stations_are_narrow_and_tapered() -> None:
    scaled = SR71_DATA.scale(30.0)
    forward_station = scaled.fuselage_stations[2]
    middle_station = scaled.fuselage_stations[4]

    assert scaled.maximum_fuselage_half_width_cm / scaled.length_cm < 0.065
    assert 0.020 <= forward_station.half_width_cm / scaled.length_cm <= 0.030
    assert 0.040 <= middle_station.half_width_cm / scaled.length_cm <= 0.055
    assert scaled.fuselage_stations[-2].half_width_cm < middle_station.half_width_cm


def test_wing_thickness_stays_within_the_fabrication_friendly_range() -> None:
    scaled = SR71_DATA.scale(30.0)

    assert 0.005 <= scaled.wing_thickness_cm / scaled.length_cm <= 0.008


def test_nacelles_remain_inside_the_outer_wing_planform() -> None:
    scaled = SR71_DATA.scale(30.0)

    assert scaled.maximum_nacelle_outer_edge_cm < scaled.half_span_cm * 0.80
    assert scaled.nacelle_tip_margin_cm >= scaled.length_cm * 0.05
    assert scaled.nacelle_centerline_variation_cm <= scaled.length_cm * 0.015


def test_canopy_is_small_relative_to_the_center_body() -> None:
    scaled = SR71_DATA.scale(30.0)

    assert scaled.maximum_canopy_half_width_cm / scaled.length_cm <= 0.025
    assert scaled.maximum_canopy_half_height_cm / scaled.length_cm <= 0.020
    assert scaled.canopy_stations[0].position_cm / scaled.length_cm >= 0.14
    assert scaled.canopy_stations[-1].position_cm / scaled.length_cm <= 0.38


def test_tail_thickness_is_independent_from_cant_and_remains_thin() -> None:
    scaled = SR71_DATA.scale(30.0)
    modified_tail = replace(SR71_DATA.tail, tail_thickness_ratio=0.008)

    assert scaled.tail.tail_thickness_cm / scaled.length_cm <= 0.008
    assert scaled.tail.tail_thickness_cm != scaled.tail.outward_tip_offset_cm
    assert modified_tail.outward_tip_offset_ratio == SR71_DATA.tail.outward_tip_offset_ratio
    assert modified_tail.tail_thickness_ratio != SR71_DATA.tail.tail_thickness_ratio


def test_tail_roots_align_with_the_nacelle_mounting_region() -> None:
    scaled = SR71_DATA.scale(30.0)

    assert any(
        station.center_y_cm == pytest.approx(scaled.tail.root_y_cm)
        for station in scaled.nacelle_stations
    )
    assert any(
        abs(station.position_cm - scaled.tail.root_leading_x_cm) <= scaled.length_cm * 0.02
        for station in scaled.nacelle_stations
    )


def test_planform_has_a_deterministic_pointed_nose_and_narrow_tail() -> None:
    points = SR71_DATA.right_planform_points

    assert points[0] == PlanformPoint(0.0, 0.0)
    assert points[-1] == PlanformPoint(1.0, 0.0)
    assert points[2].y_ratio < 0.03


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


def test_left_and_right_planforms_are_symmetric() -> None:
    scaled = SR71_DATA.scale(30.0)

    assert scaled.mirrored_planform_points_cm() == tuple(
        (x_cm, -y_cm) for x_cm, y_cm in scaled.right_planform_points_cm
    )


def test_nacelle_and_tail_offsets_are_symmetric() -> None:
    scaled = SR71_DATA.scale(30.0)

    left_nacelle, right_nacelle = scaled.nacelle_center_offsets_cm()
    left_tail, right_tail = scaled.tail_root_offsets_cm()
    assert left_nacelle == -right_nacelle
    assert left_tail == -right_tail


def test_geometry_data_is_deterministic() -> None:
    assert SR71_DATA.scale(30.0) == SR71_DATA.scale(30.0)
