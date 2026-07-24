"""Immutable, Fusion-independent contracts for aircraft silhouette assets."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from pathlib import PurePosixPath

SUPPORTED_PROFILE_EXTENSIONS = frozenset({".dxf", ".svg"})


class ProfileView(Enum):
    """The orthographic view represented by one normalized profile asset."""

    TOP = "top"
    SIDE = "side"
    SECTION = "section"


class ProfileNormalization(Enum):
    """The coordinate convention used by profile points in this first contract."""

    OVERALL_LENGTH = "overall_length"


@dataclass(frozen=True)
class NormalizedPoint:
    """One finite point in an outline normalized by aircraft overall length.

    X runs from nose (0) to tail (1). Y is a centered secondary coordinate and
    remains within one overall length of that datum. Providers decide how the
    orthographic Y coordinate maps to native Fusion axes.
    """

    x: float
    y: float

    def __post_init__(self) -> None:
        if not isfinite(self.x) or not isfinite(self.y):
            raise ValueError("Normalized point coordinates must be finite.")
        if not 0 <= self.x <= 1:
            raise ValueError("Normalized point X coordinate must be between 0 and 1.")
        if not -1 <= self.y <= 1:
            raise ValueError("Normalized point Y coordinate must be between -1 and 1.")

    def scaled(self, scale: float) -> tuple[float, float]:
        """Return a uniformly scaled coordinate pair for a provider to consume."""
        if not isfinite(scale) or scale <= 0:
            raise ValueError("Profile scale must be a finite value greater than zero.")
        return (self.x * scale, self.y * scale)


@dataclass(frozen=True)
class ProfileBounds:
    """Deterministic bounds calculated from one normalized closed outline."""

    min_x: float
    max_x: float
    min_y: float
    max_y: float

    @classmethod
    def from_outline(cls, outline: tuple[NormalizedPoint, ...]) -> ProfileBounds:
        """Create bounds without changing the supplied deterministic point order."""
        return cls(
            min_x=min(point.x for point in outline),
            max_x=max(point.x for point in outline),
            min_y=min(point.y for point in outline),
            max_y=max(point.y for point in outline),
        )

    def scaled(self, scale: float) -> ProfileBounds:
        """Return bounds at the same uniform scale as an outline."""
        if not isfinite(scale) or scale <= 0:
            raise ValueError("Profile scale must be a finite value greater than zero.")
        return ProfileBounds(
            min_x=self.min_x * scale,
            max_x=self.max_x * scale,
            min_y=self.min_y * scale,
            max_y=self.max_y * scale,
        )


@dataclass(frozen=True)
class ProfileSource:
    """Human-readable provenance required for a source-controlled profile asset."""

    attribution: str
    license_notes: str
    reference_url: str | None = None

    def __post_init__(self) -> None:
        if not self.attribution.strip():
            raise ValueError("Profile source attribution must not be empty.")
        if not self.license_notes.strip():
            raise ValueError("Profile source license notes must not be empty.")
        if self.reference_url is not None and not self.reference_url.strip():
            raise ValueError("Profile source reference URL must not be blank when supplied.")

    def as_metadata(self) -> dict[str, str | None]:
        """Return JSON-serializable provenance metadata."""
        return {
            "attribution": self.attribution,
            "license_notes": self.license_notes,
            "reference_url": self.reference_url,
        }


@dataclass(frozen=True)
class ProfileAsset:
    """A validated, closed normalized asset consumed later by a geometry provider."""

    source_path: str
    view: ProfileView
    outline: tuple[NormalizedPoint, ...]
    source: ProfileSource
    expected_symmetric: bool
    normalization: ProfileNormalization = ProfileNormalization.OVERALL_LENGTH
    bounds: ProfileBounds = field(init=False)

    def __post_init__(self) -> None:
        path = PurePosixPath(self.source_path)
        if not self.source_path or path.is_absolute() or ".." in path.parts:
            raise ValueError("Profile asset path must be a non-empty relative path.")
        if path.suffix.lower() not in SUPPORTED_PROFILE_EXTENSIONS:
            extensions = ", ".join(sorted(SUPPORTED_PROFILE_EXTENSIONS))
            raise ValueError(f"Profile asset path must use one of: {extensions}.")
        if not isinstance(self.view, ProfileView):
            raise ValueError("Profile asset view must be a ProfileView value.")
        if not isinstance(self.normalization, ProfileNormalization):
            raise ValueError("Profile normalization must be a ProfileNormalization value.")
        if not isinstance(self.expected_symmetric, bool):
            raise ValueError("Profile symmetry metadata must be a boolean value.")
        if len(self.outline) < 4:
            raise ValueError("A closed profile outline requires at least four points.")
        if self.outline[0] != self.outline[-1]:
            raise ValueError("A profile outline must end at its first point.")
        if any(start == end for start, end in zip(self.outline, self.outline[1:])):
            raise ValueError("A profile outline must not contain repeated adjacent points.")
        object.__setattr__(self, "bounds", ProfileBounds.from_outline(self.outline))

    def scaled_outline(self, scale: float) -> tuple[tuple[float, float], ...]:
        """Return a uniformly scaled outline while preserving point ordering."""
        return tuple(point.scaled(scale) for point in self.outline)

    def as_metadata(self) -> dict[str, object]:
        """Return deterministic JSON-serializable metadata without reading the asset file."""
        return {
            "source_path": self.source_path,
            "view": self.view.value,
            "normalization": self.normalization.value,
            "expected_symmetric": self.expected_symmetric,
            "source": self.source.as_metadata(),
            "outline": [{"x": point.x, "y": point.y} for point in self.outline],
            "bounds": {
                "min_x": self.bounds.min_x,
                "max_x": self.bounds.max_x,
                "min_y": self.bounds.min_y,
                "max_y": self.bounds.max_y,
            },
        }


@dataclass(frozen=True)
class AircraftProfileDefinition:
    """The pure top/side asset bundle selected by a future aircraft provider."""

    identifier: str
    display_name: str
    top_profile: ProfileAsset
    side_profile: ProfileAsset
    section_profiles: tuple[ProfileAsset, ...] = ()

    def __post_init__(self) -> None:
        if not self.identifier.strip():
            raise ValueError("Aircraft profile definition identifier must not be empty.")
        if not self.display_name.strip():
            raise ValueError("Aircraft profile definition display name must not be empty.")
        if self.top_profile.view is not ProfileView.TOP:
            raise ValueError("Aircraft profile definition requires a top profile.")
        if self.side_profile.view is not ProfileView.SIDE:
            raise ValueError("Aircraft profile definition requires a side profile.")
        if any(profile.view is not ProfileView.SECTION for profile in self.section_profiles):
            raise ValueError("Optional section profiles must use the section view.")

    def as_metadata(self) -> dict[str, object]:
        """Return a deterministic JSON-serializable provider input description."""
        return {
            "identifier": self.identifier,
            "display_name": self.display_name,
            "top_profile": self.top_profile.as_metadata(),
            "side_profile": self.side_profile.as_metadata(),
            "section_profiles": [profile.as_metadata() for profile in self.section_profiles],
        }
