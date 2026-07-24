"""Pure-Python station data, validation, and deterministic scaling helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Station:
    """An elliptical cross-section at a normalized longitudinal position.

    ``half_width_cm`` and ``half_height_cm`` are dimensions at the definition's
    reference length. Use :func:`scale_stations` to derive dimensions for a
    requested length without changing station positions.
    """

    position: float
    half_width_cm: float
    half_height_cm: float

    def __post_init__(self) -> None:
        if not 0 <= self.position <= 1:
            raise ValueError("Station position must be between 0 and 1 inclusive.")
        if self.half_width_cm <= 0 or self.half_height_cm <= 0:
            raise ValueError("Station half-width and half-height must be greater than zero.")

    def scaled(self, factor: float) -> Station:
        """Return a station with dimensions multiplied by a positive ``factor``."""
        if factor <= 0:
            raise ValueError("Station scale factor must be greater than zero.")
        return Station(
            position=self.position,
            half_width_cm=self.half_width_cm * factor,
            half_height_cm=self.half_height_cm * factor,
        )


def validate_station_sequence(stations: Iterable[Station]) -> tuple[Station, ...]:
    """Validate and return an ordered station tuple suitable for a loft."""
    ordered_stations = tuple(stations)
    if len(ordered_stations) < 2:
        raise ValueError("A loft requires at least two stations.")

    previous_position = ordered_stations[0].position
    for station in ordered_stations[1:]:
        if station.position <= previous_position:
            raise ValueError("Station positions must be strictly increasing.")
        previous_position = station.position
    return ordered_stations


def scale_stations(
    stations: Iterable[Station], *, reference_length_cm: float, requested_length_cm: float
) -> tuple[Station, ...]:
    """Validate a station sequence and scale its dimensions to a requested length.

    Position remains normalized, so every station is placed at
    ``position * requested_length_cm``. Dimensions scale linearly by
    ``requested_length_cm / reference_length_cm``.
    """
    if reference_length_cm <= 0:
        raise ValueError("Reference aircraft length must be greater than zero.")
    if requested_length_cm <= 0:
        raise ValueError("Requested aircraft length must be greater than zero.")

    factor = requested_length_cm / reference_length_cm
    return tuple(station.scaled(factor) for station in validate_station_sequence(stations))
