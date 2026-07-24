# ADR 0001: Aircraft geometry sources

## Status

Accepted for the next geometry milestone. The current SR-71 work remains an
experimental spike and is not a production aircraft definition.

## Context

Slice Aircraft Generator exists to create reliable source volumes for transverse
rib sculptures. Its priority is a recognizable silhouette, stable section
intersections, predictable scaling, and manageable Fusion regeneration—not an
aerospace-grade watertight skin.

Draft PR #3 proved that native Fusion construction, placement, rollback, and
construction-visibility cleanup can work. The latest Fusion smoke test also
showed the limit of the current approach: repeated procedural station-ratio
tuning did not reliably produce an immediately recognizable SR-71 in front and
three-quarter views. Continuing to alter those ratios would not establish a
scalable route for additional aircraft.

## Decision drivers

- Silhouette fidelity must be verifiable before opening Fusion.
- The command UI must remain independent of geometry-source choice.
- Pure metadata and profile data must import and test without `adsk`.
- Fusion-specific operations must be shared instead of copied per aircraft.
- Future slicing must work on a stable source volume or reliably combine
  sections from multiple source bodies.
- Imported source assets require explicit provenance and licensing review.

## Options considered

### A. Fully procedural Python per aircraft

This creates native editable Fusion features and can express bespoke geometry.
It also has high implementation cost, repeats Fusion API operations, and makes
visual tuning difficult because every silhouette iteration requires Fusion.
The current SR-71 spike is evidence that this approach scales poorly when it is
used as the whole-aircraft default.

Use it only for exceptional additions that shared providers cannot express.

### B. Shared builder with aircraft-specific normalized data

Shared primitives and normalized data improve reuse, pure-Python testing, and
moderate editability. They are appropriate for simple bodies, symmetric pods,
thin fins, and controlled cross-section refinement. They still depend on
manually tuned geometry data, however, and do not by themselves guarantee a
recognizable top or side silhouette.

Use this for reusable primitives and optional local refinements, not as the
sole source of a visually distinctive aircraft.

### C. Top/side profile assets with a shared visual-hull builder

An aircraft supplies clean top SVG/DXF and side SVG/DXF outlines. A shared
Fusion builder imports, scales, and combines intersecting or extruded
silhouettes into a visual hull, optionally refined by cross-sections, symmetric
pods, and thin fins. This gives strong top/side silhouette control and is well
suited to sliced sculptures, where visual recognition and section stability are
more useful than aerodynamic surface detail.

The result remains a native editable Fusion construction, but it deliberately
does not claim engineering-grade surface accuracy.

### D. Imported STEP or mesh source model

An imported STEP or mesh is the fastest route to a recognizable aircraft. It
requires source licensing and provenance review. Mesh-to-B-Rep conversion can
be slow or unreliable, and imported bodies have reduced parametric editability.
The slicing engine may operate directly on a suitable imported B-Rep or mesh,
but that capability must be validated separately.

This is appropriate for a fabrication-first workflow when a permitted source is
available and the section-validation pipeline accepts it.

## Decision

Adopt a **hybrid provider architecture**:

1. An aircraft definition provides metadata and selects a geometry provider.
2. Providers own how source geometry is acquired or constructed.
3. Reusable Fusion primitives own profile import, visual hulls, symmetric pairs,
   lofts, thin fins, and transactions.
4. Pure aircraft metadata and profile data contain no Fusion API calls.
5. An aircraft may supply a small custom builder only for geometry that cannot
   be expressed with the shared providers and primitives.

The command UI continues to choose an `AircraftDefinition`; it does not know
whether that definition uses SVG/DXF profiles, imported geometry, or a
procedural provider.

### Target contracts

```text
AircraftDefinition
  display_name
  default_length_cm
  source_metadata
  geometry_provider

AircraftGeometryProvider
  build(context, definition) -> Component

ProfileAssetProvider | ImportedBodyProvider | ProceduralProvider
  implement AircraftGeometryProvider
```

The existing `AircraftDefinition`, `AircraftBuildContext`, `BuildPlacement`,
and `FeatureTransaction` are useful input to this design. Their future API may
be adapted deliberately; this ADR does not implement that migration.

## Recommended layout

```text
aircraft/
  __init__.py
  registry.py
  sr71/
    definition.py
    metadata.py
    profiles/top.svg
    profiles/side.svg
    optional_sections.json
  f117/
    definition.py
    metadata.py
    profiles/top.svg
    profiles/side.svg

geometry/
  providers/
    base.py
    profile_asset_provider.py
    imported_body_provider.py
    procedural_provider.py
  primitives/
    profile_import.py
    visual_hull.py
    symmetric_pair.py
    loft.py
    thin_fin.py
    transaction.py
  slicing/
    slice_engine.py
```

See [the architecture diagram](../architecture.md) for provider flow and
ownership boundaries.

## SR-71 direction

The SR-71 should move away from an all-station procedural body. The next
implementation should:

1. trace or create a clean top outline and side outline;
2. validate those assets outside Fusion;
3. construct a shared visual-hull body from the profiles;
4. add nacelles through a reusable symmetric-pod primitive;
5. add tails through a reusable thin-fin primitive;
6. add only minimal canopy refinement necessary for the sculpture;
7. validate top and side silhouettes before a Fusion smoke test.

The intended result is a recognizable sliced-art source volume, not an
aerodynamically accurate SR-71 model. A multi-body source is acceptable if the
future slice engine reliably combines its section results.

## Proof of concept before SR-71 rebuild

Build a small fictional delta-aircraft proof of concept first:

1. supply matching simple top and side profiles;
2. build one native Fusion visual hull;
3. generate ten transverse sections;
4. confirm every section is closed and deterministic;
5. measure regeneration time;
6. confirm uniform scaling; and
7. only then apply the pipeline to the SR-71.

## PR #3 disposition

Choose **Option 1: close PR #3 as an experimental spike and create a new issue
for the profile-driven geometry provider.**

PR #3 mixes experimental SR-71 geometry, smoke-test discoveries, and useful
infrastructure learnings. Reducing it to infrastructure after the fact would
require selectively removing the central experiment, make its review history
misleading, and still leave no validated profile-driven path. Closing it keeps
the experiment visible without presenting it as production SR-71 geometry.
Future provider work can port individual validated learnings—placement,
transactional cleanup, diagnostics, and browser visibility handling—through
small, independently reviewable changes.

## Proposed follow-up issues

1. **Profile asset data model** — Define metadata, source provenance, normalized
   coordinate conventions, validation, and asset packaging for top/side profiles.
2. **SVG/DXF profile importer** — Import permitted 2D profile assets into native
   Fusion sketches with scaling, closure, and unit validation.
3. **Visual-hull Fusion builder** — Build an editable native visual hull from
   top/side profiles using the shared transaction and placement rules.
4. **Cross-section validation prototype** — Generate ten deterministic transverse
   sections, verify closure, report failures, and measure regeneration time.
5. **SR-71 top and side profile assets** — Create licensed or original assets,
   document their sources/approximations, and validate their silhouettes.
6. **SR-71 nacelle and tail refinement** — Add reusable symmetric-pod and
   thin-fin refinements to the SR-71 visual hull.
7. **Generic slice engine** — Convert validated source bodies into predictable
   transverse slice geometry, including multi-body section combination.
8. **Slotted base generator** — Generate fabrication bases that fit the slice
   set without coupling base logic to an aircraft provider.
9. **STL export** — Export validated model geometry with explicit units and
   user-facing export diagnostics.

## Consequences

New aircraft normally contribute metadata, overall dimensions, top/side
profiles, optional cross-sections, and optional pod/tail definitions. They do
not copy hundreds of Fusion calls. Procedural code remains available for true
exceptions, while imported STEP/mesh sources remain an explicitly licensed,
validated alternative.
