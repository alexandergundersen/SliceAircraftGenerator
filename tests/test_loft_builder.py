"""Tests for pure helpers used by Fusion loft construction."""

from geometry.loft_builder import ZERO_OFFSET_TOLERANCE_CM, uses_origin_plane


def test_zero_offset_uses_the_origin_plane() -> None:
    assert uses_origin_plane(0.0)


def test_offset_within_tolerance_uses_the_origin_plane() -> None:
    assert uses_origin_plane(ZERO_OFFSET_TOLERANCE_CM / 2)


def test_positive_offset_outside_tolerance_uses_an_offset_plane() -> None:
    assert not uses_origin_plane(ZERO_OFFSET_TOLERANCE_CM * 2)


def test_negative_offset_outside_tolerance_uses_an_offset_plane() -> None:
    assert not uses_origin_plane(-ZERO_OFFSET_TOLERANCE_CM * 2)
