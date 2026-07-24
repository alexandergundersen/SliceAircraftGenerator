# Geometry provider architecture

This target architecture follows [ADR 0001](adr/0001-aircraft-geometry-sources.md).
It separates pure aircraft information from reusable Fusion operations and from
the future fabrication pipeline.

```mermaid
flowchart LR
    UI[Slice Aircraft command] --> Definition[AircraftDefinition]
    Definition --> Metadata[Pure metadata and source provenance]
    Definition --> Provider[AircraftGeometryProvider]

    Provider --> Profile[ProfileAssetProvider]
    Provider --> Imported[ImportedBodyProvider]
    Provider --> Procedural[ProceduralProvider]

    Profile --> Assets[Top/side SVG or DXF\noptional sections]
    Profile --> Import[Profile import primitive]
    Import --> Hull[Visual-hull primitive]
    Procedural --> Primitives[Shared Fusion primitives]
    Imported --> Source[Permitted STEP or mesh source]

    Hull --> Refine[Symmetric pod / thin fin / optional loft]
    Primitives --> Refine
    Source --> Bodies[Native or validated source bodies]
    Refine --> Bodies

    Bodies --> Transaction[Placement and transaction ownership]
    Transaction --> Slice[Generic slice engine]
    Slice --> Fabrication[Sections, slotted base, STL export]
```

## Ownership boundaries

| Layer | Owns | Must not own |
| --- | --- | --- |
| Aircraft package | Metadata, dimensions, source provenance, profile assets, optional sections | Fusion API calls or slicing mechanics |
| Geometry provider | Source acquisition and high-level build choice | Command UI decisions |
| Geometry primitive | Reusable native Fusion operation | Aircraft-specific proportions or branding |
| Transaction | Part/Hybrid placement, created-object ownership, rollback, browser cleanup | Aircraft shape decisions |
| Slice engine | Section construction and multi-body section combination | Aircraft-specific modeling |

## Default aircraft contribution

```text
metadata + dimensions + top outline + side outline
  + optional cross-sections / pods / fins
  + custom builder only when shared providers cannot express the shape
```

The first provider proof of concept uses a fictional delta aircraft and ten
transverse-section checks before real SR-71 assets are introduced.
