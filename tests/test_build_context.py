"""Tests for pure-Python aircraft build inputs."""

import unittest
from dataclasses import FrozenInstanceError

from geometry.build_context import AircraftBuildContext, BuildPlacement


class AircraftBuildContextTests(unittest.TestCase):
    """Verify immutable build inputs without importing Fusion's API."""

    def test_root_component_placement_uses_the_default_feature_prefix(self) -> None:
        context = AircraftBuildContext(
            root_component=object(),
            length_cm=100.0,
            placement=BuildPlacement.ROOT_COMPONENT,
        )

        self.assertEqual(context.feature_name_prefix("Prototype"), "Prototype")
        self.assertFalse(context.placement.owns_target_component)
        self.assertFalse(context.placement.renames_target_component)

    def test_internal_component_placement_is_owned_and_renamed(self) -> None:
        context = AircraftBuildContext(
            root_component=object(),
            length_cm=100.0,
            placement=BuildPlacement.NEW_INTERNAL_COMPONENT,
        )

        self.assertTrue(context.placement.owns_target_component)
        self.assertTrue(context.placement.renames_target_component)

    def test_custom_component_name_overrides_the_default_feature_prefix(self) -> None:
        context = AircraftBuildContext(
            root_component=object(),
            length_cm=100.0,
            placement=BuildPlacement.ROOT_COMPONENT,
            component_name="Test Instance",
        )

        self.assertEqual(context.feature_name_prefix("Prototype"), "Test Instance")

    def test_placement_is_immutable(self) -> None:
        context = AircraftBuildContext(
            root_component=object(),
            length_cm=100.0,
            placement=BuildPlacement.ROOT_COMPONENT,
        )

        with self.assertRaises(FrozenInstanceError):
            context.placement = BuildPlacement.NEW_INTERNAL_COMPONENT

    def test_invalid_placement_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "BuildPlacement"):
            AircraftBuildContext(
                root_component=object(),
                length_cm=100.0,
                placement="root_component",  # type: ignore[arg-type]
            )

    def test_missing_placement_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            AircraftBuildContext(root_component=object(), length_cm=100.0)  # type: ignore[call-arg]

    def test_non_positive_requested_length_is_rejected(self) -> None:
        for length_cm in (0.0, -0.1):
            with self.subTest(length_cm=length_cm):
                with self.assertRaisesRegex(ValueError, "greater than zero"):
                    AircraftBuildContext(
                        root_component=object(),
                        length_cm=length_cm,
                        placement=BuildPlacement.ROOT_COMPONENT,
                    )
