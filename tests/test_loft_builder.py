"""Tests for pure helpers used by Fusion loft construction."""

import pytest

from geometry.loft_builder import (
    ZERO_OFFSET_TOLERANCE_CM,
    set_browser_visibility,
    uses_origin_plane,
)


def test_zero_offset_uses_the_origin_plane() -> None:
    assert uses_origin_plane(0.0)


def test_offset_within_tolerance_uses_the_origin_plane() -> None:
    assert uses_origin_plane(ZERO_OFFSET_TOLERANCE_CM / 2)


def test_positive_offset_outside_tolerance_uses_an_offset_plane() -> None:
    assert not uses_origin_plane(ZERO_OFFSET_TOLERANCE_CM * 2)


def test_negative_offset_outside_tolerance_uses_an_offset_plane() -> None:
    assert not uses_origin_plane(-ZERO_OFFSET_TOLERANCE_CM * 2)


class _BrowserObject:
    """Minimal browser-object stand-in for the pure helper contract."""

    def __init__(self, *, is_valid: bool = True) -> None:
        self.isValid = is_valid
        self.isLightBulbOn = True


class _UnsupportedBrowserObject:
    __slots__ = ("isValid", "name")

    def __init__(self) -> None:
        self.isValid = True
        self.name = "Unsupported"


def test_browser_visibility_uses_the_writable_light_bulb() -> None:
    browser_object = _BrowserObject()

    assert set_browser_visibility(browser_object, False)
    assert not browser_object.isLightBulbOn


def test_browser_visibility_skips_invalid_objects() -> None:
    browser_object = _BrowserObject(is_valid=False)

    assert not set_browser_visibility(browser_object, False)
    assert browser_object.isLightBulbOn


def test_browser_visibility_reports_objects_without_a_writable_light_bulb() -> None:
    with pytest.raises(RuntimeError, match="writable browser visibility"):
        set_browser_visibility(_UnsupportedBrowserObject(), False)
