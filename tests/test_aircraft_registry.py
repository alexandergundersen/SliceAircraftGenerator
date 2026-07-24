"""Tests for the command-visible aircraft definition registry."""

from geometry.registry import AIRCRAFT_DEFINITIONS
from geometry.sr71_data import DEFAULT_MODEL_LENGTH_CM


def test_sr71_and_prototype_are_both_registered() -> None:
    names = tuple(definition.display_name for definition in AIRCRAFT_DEFINITIONS)

    assert names == ("SR-71 Blackbird", "Elliptical Loft Prototype")


def test_sr71_is_the_default_display_definition() -> None:
    definition = AIRCRAFT_DEFINITIONS[0]

    assert definition.default_length_cm == DEFAULT_MODEL_LENGTH_CM
