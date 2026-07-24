"""Pure-Python tests for profile-driven aircraft asset contracts."""

from __future__ import annotations

import json
import math
from dataclasses import FrozenInstanceError

import pytest

from aircraft.profile_assets import (
    AircraftProfileDefinition,
    NormalizedPoint,
    ProfileAsset,
    ProfileNormalization,
    ProfileSource,
    ProfileView,
)


def _source() -> ProfileSource:
    return ProfileSource(
        attribution="Original project silhouette",
        license_notes="Project-owned demonstration asset.",
        reference_url="https://example.com/profile-source",
    )


def _outline() -> tuple[NormalizedPoint, ...]:
    return (
        NormalizedPoint(0.0, 0.0),
        NormalizedPoint(0.5, 0.25),
        NormalizedPoint(1.0, 0.0),
        NormalizedPoint(0.5, -0.25),
        NormalizedPoint(0.0, 0.0),
    )


def _asset(view: ProfileView = ProfileView.TOP) -> ProfileAsset:
    return ProfileAsset(
        source_path=f"profiles/{view.value}.svg",
        view=view,
        outline=_outline(),
        source=_source(),
        expected_symmetric=True,
    )


def test_normalized_point_requires_finite_coordinates() -> None:
    for coordinate in (math.inf, -math.inf, math.nan):
        with pytest.raises(ValueError, match="finite"):
            NormalizedPoint(coordinate, 0.0)


@pytest.mark.parametrize("point", [(-0.01, 0.0), (1.01, 0.0), (0.5, -1.01), (0.5, 1.01)])
def test_normalized_point_requires_documented_coordinate_bounds(point: tuple[float, float]) -> None:
    with pytest.raises(ValueError, match="between"):
        NormalizedPoint(*point)


def test_profile_asset_requires_a_closed_outline_with_minimum_point_count() -> None:
    with pytest.raises(ValueError, match="at least four"):
        ProfileAsset(
            source_path="profiles/top.svg",
            view=ProfileView.TOP,
            outline=(NormalizedPoint(0.0, 0.0), NormalizedPoint(1.0, 0.0)),
            source=_source(),
            expected_symmetric=True,
        )
    with pytest.raises(ValueError, match="end at its first point"):
        ProfileAsset(
            source_path="profiles/top.svg",
            view=ProfileView.TOP,
            outline=(
                NormalizedPoint(0.0, 0.0),
                NormalizedPoint(0.5, 0.25),
                NormalizedPoint(1.0, 0.0),
                NormalizedPoint(0.5, -0.25),
            ),
            source=_source(),
            expected_symmetric=True,
        )


def test_profile_asset_preserves_deterministic_outline_order_and_bounds() -> None:
    asset = _asset()

    assert asset.outline == _outline()
    assert asset.bounds.min_x == 0.0
    assert asset.bounds.max_x == 1.0
    assert asset.bounds.min_y == -0.25
    assert asset.bounds.max_y == 0.25


def test_profile_asset_scales_every_coordinate_uniformly() -> None:
    asset = _asset()

    assert asset.scaled_outline(25.0) == (
        (0.0, 0.0),
        (12.5, 6.25),
        (25.0, 0.0),
        (12.5, -6.25),
        (0.0, 0.0),
    )
    assert asset.bounds.scaled(25.0).max_y == 6.25


@pytest.mark.parametrize("scale", [0.0, -1.0, math.inf, math.nan])
def test_profile_asset_rejects_invalid_uniform_scale(scale: float) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        _asset().scaled_outline(scale)


@pytest.mark.parametrize("path", ["", "/profiles/top.svg", "../top.svg", "profiles/top.txt"])
def test_profile_asset_rejects_invalid_paths_and_extensions(path: str) -> None:
    with pytest.raises(ValueError, match="path"):
        ProfileAsset(
            source_path=path,
            view=ProfileView.TOP,
            outline=_outline(),
            source=_source(),
            expected_symmetric=True,
        )


def test_profile_asset_records_symmetry_and_normalization_metadata() -> None:
    asset = _asset()

    assert asset.expected_symmetric
    assert asset.normalization is ProfileNormalization.OVERALL_LENGTH


def test_source_requires_attribution_and_license_notes() -> None:
    with pytest.raises(ValueError, match="attribution"):
        ProfileSource(attribution="", license_notes="Valid note")
    with pytest.raises(ValueError, match="license"):
        ProfileSource(attribution="Valid attribution", license_notes="")


def test_aircraft_definition_requires_top_and_side_profiles() -> None:
    top_profile = _asset(ProfileView.TOP)
    side_profile = _asset(ProfileView.SIDE)
    definition = AircraftProfileDefinition(
        identifier="delta_demo",
        display_name="Delta Demonstrator",
        top_profile=top_profile,
        side_profile=side_profile,
    )

    assert definition.top_profile is top_profile
    assert definition.side_profile is side_profile
    with pytest.raises(ValueError, match="top profile"):
        AircraftProfileDefinition(
            identifier="invalid",
            display_name="Invalid",
            top_profile=side_profile,
            side_profile=side_profile,
        )


def test_aircraft_definition_accepts_optional_section_profiles() -> None:
    section_profile = _asset(ProfileView.SECTION)

    definition = AircraftProfileDefinition(
        identifier="delta_demo",
        display_name="Delta Demonstrator",
        top_profile=_asset(ProfileView.TOP),
        side_profile=_asset(ProfileView.SIDE),
        section_profiles=(section_profile,),
    )

    assert definition.section_profiles == (section_profile,)


def test_profile_metadata_is_json_serializable_and_deterministic() -> None:
    definition = AircraftProfileDefinition(
        identifier="delta_demo",
        display_name="Delta Demonstrator",
        top_profile=_asset(ProfileView.TOP),
        side_profile=_asset(ProfileView.SIDE),
    )

    metadata = definition.as_metadata()
    assert json.loads(json.dumps(metadata)) == metadata
    assert definition.as_metadata() == metadata


def test_profile_contracts_are_immutable() -> None:
    asset = _asset()

    with pytest.raises(FrozenInstanceError):
        asset.source_path = "profiles/changed.svg"
