# Profile-driven aircraft geometry

Aircraft definitions should be asset-driven because recognizable aircraft are
primarily silhouette problems before they are Fusion feature problems. A new
aircraft normally supplies immutable metadata plus validated top and side
outlines; it does not duplicate a monolithic Python sequence of Fusion calls.

## Separation of responsibilities

`aircraft.profile_assets` is pure Python. It validates normalized closed
outlines, source paths, provenance, licensing notes, view type, symmetry
expectations, deterministic point ordering, and uniform scaling. It imports no
Fusion modules and does not read SVG or DXF files yet.

Future providers consume the validated `AircraftProfileDefinition`:

1. the SVG/DXF parser produces `ProfileAsset` outlines;
2. the visual-hull provider converts those outlines into native Fusion sketches
   and bodies;
3. reusable symmetric-pod and thin-fin primitives add optional refinements; and
4. the slice engine operates on the resulting source bodies.

Keeping aircraft-specific assets separate from Fusion code makes silhouette
review possible before regeneration, makes provenance explicit, and lets one
provider implementation serve multiple aircraft. It avoids the repeated Fusion
API code and fragile visual tuning associated with one Python script per
aircraft.
