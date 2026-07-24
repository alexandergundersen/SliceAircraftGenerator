# Slice Aircraft Generator

Slice Aircraft Generator is an Autodesk Fusion 360 Python add-in that provides a
starting point for a fabrication-oriented, sliced-aircraft workflow. It adds
**Slice Aircraft** to **Solid → Create** and opens a parameter dialog containing
placeholder inputs for Aircraft, Length, Rib Count, and Rib Thickness.

The initial **Elliptical Loft Prototype** generates editable demonstration
geometry for validating the end-to-end Fusion workflow. Each station is retained
as a named construction plane and sketch, followed by a native Fusion
`LoftFeature`, so the resulting B-Rep is inspectable and editable in the
parametric timeline. It is infrastructure and demonstration geometry, not an
accurate model of any aircraft. Rib and export workflows remain placeholders for
future releases.

The **SR-71 Blackbird** option is the default 300 mm display model. It produces
a native, editable multi-body approximation containing a chine-shaped fuselage,
delta wing, paired nacelles, raised canopy, and canted twin tails. It is designed
to be recognizable from top and side views, not to reproduce restoration or
engineering geometry.

The first manual visual smoke test successfully generated the model but found
that its initial proportions read as a thick flying wing. The current recipe
therefore refines the narrow center body, swept outer planform, nacelle spacing,
low canopy, thin wing, and independently-thick canted tails. Another manual
Fusion visual smoke test is required before this definition is considered ready.

## Install

1. Download or clone this repository.
2. In Fusion 360, open **Utilities → Add-Ins → Scripts and Add-Ins**.
3. On the **Add-Ins** tab, use the green **+** button and select this directory
   (the directory containing `SliceAircraftGenerator.py` and
   `SliceAircraftGenerator.manifest`).
4. Select **Slice Aircraft Generator** and click **Run**. Enable **Run on Startup**
   in Fusion if desired.
5. Open the **Solid** workspace and choose **Create → Slice Aircraft**.

## Project layout

```
SliceAircraftGenerator.py       Fusion add-in entry point (`run` / `stop`)
commands/                       Toolbar commands and command event handlers
geometry/                       Aircraft definitions and station-based B-Rep generation
export/                         Future DXF, SVG, and other fabrication exports
utils/                          Fusion event lifetime and diagnostics helpers
resources/                      Optional command artwork
```

## Development notes

Fusion's Python API requires command event-handler objects to remain strongly
referenced for as long as their events can fire. `utils.events.EventSubscriptions`
owns those references and unregisters them when the add-in or dialog closes.
This lets the add-in reload without leaving duplicate controls or stale callbacks.

The entry point deletes its toolbar control and command definition in `stop`,
and its handlers are removed before those UI objects are released. This is the
expected clean unload lifecycle for a Fusion add-in.

## Geometry definitions

`geometry.aircraft_definition.AircraftDefinition` is the contract for aircraft
recipes. It receives an immutable `AircraftBuildContext` and returns a generated
component. `Station` and its validation/scaling helpers are pure Python, while
`LoftBuilder` owns the Fusion-specific construction planes, sketches, native
solid loft, and failed-generation cleanup.

`EllipticalLoftPrototypeDefinition` provides generic station data and delegates
to `LoftBuilder`. It is intentionally only a generic demonstration recipe, not
an accurate model of an aircraft; accurate aircraft definitions will be added
separately.

## SR-71 approximation

The model uses X nose-to-tail, Y lateral, and Z vertical coordinates; normalized
X values run from 0 at the nose to 1 at the tail. The Smithsonian National Air
and Space Museum lists the SR-71 at **32.741 m** long with a **16.942 m** span,
which yields the sourced span-to-length ratio used by this model (approximately
0.517). [Smithsonian collection record](https://airandspace.si.edu/collection-objects/lockheed-sr-71-blackbird/nasm_A19920072000)
and [NASA's SR-71 fact sheet](https://www.nasa.gov/wp-content/uploads/2021/09/495839main_FS-030_SR-71.pdf)
independently report essentially the same dimensions.

Only that overall ratio is sourced. Chines, station contours, planform control
points, canopy shape, nacelle contours, and tail geometry are normalized artistic
approximations intended for a stable fabrication-oriented display model. All
dimensions scale linearly from the requested length. The current SR-71 is
deliberately multi-body; it does not perform fragile boolean unions.

The refined approximation uses the following normalized design ranges. These are
artistic fabrication choices, not sourced SR-71 engineering dimensions:

- The central fuselage/chine maximum half-width is 0.062 of overall length; it is
  0.025 near x=0.12 and 0.052 near x=0.36, with a low flattened vertical section.
- The wing is 0.0065 of overall length thick (about 1.95 mm at 300 mm) and is
  centered about the XY datum using an offset sketch plane.
- Nacelle center offsets remain from 0.140 to 0.150 of length, their main
  half-width is 0.038–0.043, and the outer wing provides at least 0.05 of length
  of visible margin beyond the nacelles.
- The five-station canopy runs from x=0.15 to x=0.38 with maximum half-width
  0.022 and half-height 0.017, creating a deliberately low raised feature.
- Each tail has a 0.115 maximum height, a 0.025 outward cant offset, and an
  independent 0.006 physical thickness (about 1.8 mm at 300 mm). The tail loft
  uses thin canted YZ profiles so the outward cant is not used as body thickness.

After a successful SR-71 generation, the add-in hides only the construction
planes and sketches it created. They remain editable in Fusion's browser and
timeline, while the initial viewport shows the resulting bodies. Existing user
objects and origin geometry are never hidden.

### Development

SR-71-specific normalized proportions and validation live in `geometry/sr71_data.py`.
`geometry/sr71_builder.py` converts them into Fusion features while reusing the
generic placement transaction, so Part and Hybrid behavior and failure cleanup
remain consistent with the diagnostic prototype.

The command selects geometry placement from Fusion's design intent. Part Designs
generate directly in the root component, Hybrid Designs generate in a new
internal component, and Assembly Designs are rejected because external assembly
components are not part of this add-in's current scope.

## License

This project is licensed under the [MIT License](LICENSE).
