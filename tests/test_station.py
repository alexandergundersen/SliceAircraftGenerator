"""Tests for pure station validation and scaling."""

import unittest

from geometry.station import Station, scale_stations, validate_station_sequence


class StationTests(unittest.TestCase):
    """Exercise station data independently from the Fusion API."""

    def test_valid_station_can_be_created(self) -> None:
        station = Station(position=0.25, half_width_cm=10.0, half_height_cm=5.0)

        self.assertEqual(station.position, 0.25)
        self.assertEqual(station.half_width_cm, 10.0)
        self.assertEqual(station.half_height_cm, 5.0)

    def test_station_rejects_positions_outside_normalized_range(self) -> None:
        for position in (-0.01, 1.01):
            with self.subTest(position=position):
                with self.assertRaisesRegex(ValueError, "between 0 and 1"):
                    Station(position=position, half_width_cm=10.0, half_height_cm=5.0)

    def test_station_rejects_non_positive_dimensions(self) -> None:
        for half_width_cm, half_height_cm in ((0.0, 5.0), (-1.0, 5.0), (10.0, 0.0), (10.0, -1.0)):
            with self.subTest(half_width_cm=half_width_cm, half_height_cm=half_height_cm):
                with self.assertRaisesRegex(ValueError, "greater than zero"):
                    Station(
                        position=0.25,
                        half_width_cm=half_width_cm,
                        half_height_cm=half_height_cm,
                    )

    def test_station_sequence_requires_strictly_increasing_positions(self) -> None:
        stations = (
            Station(position=0.0, half_width_cm=10.0, half_height_cm=5.0),
            Station(position=0.0, half_width_cm=8.0, half_height_cm=4.0),
        )

        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            validate_station_sequence(stations)

    def test_station_sequence_requires_at_least_two_stations(self) -> None:
        station = Station(position=0.0, half_width_cm=10.0, half_height_cm=5.0)

        with self.assertRaisesRegex(ValueError, "at least two"):
            validate_station_sequence((station,))

    def test_scale_stations_scales_dimensions_and_preserves_positions(self) -> None:
        stations = (
            Station(position=0.0, half_width_cm=10.0, half_height_cm=5.0),
            Station(position=1.0, half_width_cm=4.0, half_height_cm=2.0),
        )

        scaled = scale_stations(
            stations,
            reference_length_cm=100.0,
            requested_length_cm=250.0,
        )

        self.assertEqual(
            scaled,
            (
                Station(position=0.0, half_width_cm=25.0, half_height_cm=12.5),
                Station(position=1.0, half_width_cm=10.0, half_height_cm=5.0),
            ),
        )

    def test_scaling_rejects_non_positive_requested_length(self) -> None:
        stations = (
            Station(position=0.0, half_width_cm=10.0, half_height_cm=5.0),
            Station(position=1.0, half_width_cm=4.0, half_height_cm=2.0),
        )

        for requested_length_cm in (0.0, -1.0):
            with self.subTest(requested_length_cm=requested_length_cm):
                with self.assertRaisesRegex(ValueError, "Requested aircraft length"):
                    scale_stations(
                        stations,
                        reference_length_cm=100.0,
                        requested_length_cm=requested_length_cm,
                    )
