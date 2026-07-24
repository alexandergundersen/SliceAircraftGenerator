"""Pure-Python tests for normalized SR-71 approximation data."""

import math

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


def test_doubling_requested_length_doubles_all_major_dimensions() -> None:
    base = SR71_DATA.scale(30.0)
    doubled = SR71_DATA.scale(60.0)

    assert doubled.wingspan_cm == pytest.approx(base.wingspan_cm * 2)
    assert doubled.wing_thickness_cm == pytest.approx(base.wing_thickness_cm * 2)
    assert doubled.fuselage_stations[4].half_width_cm == pytest.approx(
        base.fuselage_stations[4].half_width_cm * 2
    )
    assert doubled.nacelle_stations[2].center_y_cm == pytest.approx(
        base.nacelle_stations[2].center_y_cm * 2
    )
    assert doubled.tail.tip_height_cm == pytest.approx(base.tail.tip_height_cm * 2)


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


def test_planform_requires_points_on_one_side_of_the_centerline() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        PlanformPoint(0.5, -0.1)


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
