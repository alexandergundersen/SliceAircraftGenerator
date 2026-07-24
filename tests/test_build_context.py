"""Tests for pure-Python aircraft build inputs."""

import unittest

from geometry.build_context import AircraftBuildContext


class AircraftBuildContextTests(unittest.TestCase):
    """Verify immutable build inputs without importing Fusion's API."""

    def test_default_component_name_is_used_when_no_override_is_supplied(self) -> None:
        context = AircraftBuildContext(root_component=object(), length_cm=100.0)

        self.assertEqual(context.resolved_component_name("Prototype"), "Prototype")

    def test_custom_component_name_overrides_the_definition_default(self) -> None:
        context = AircraftBuildContext(
            root_component=object(), length_cm=100.0, component_name="Test Instance"
        )

        self.assertEqual(context.resolved_component_name("Prototype"), "Test Instance")

    def test_non_positive_requested_length_is_rejected(self) -> None:
        for length_cm in (0.0, -0.1):
            with self.subTest(length_cm=length_cm):
                with self.assertRaisesRegex(ValueError, "greater than zero"):
                    AircraftBuildContext(root_component=object(), length_cm=length_cm)
