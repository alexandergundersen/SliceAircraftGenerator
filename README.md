# Slice Aircraft Generator

Slice Aircraft Generator is an Autodesk Fusion 360 Python add-in that provides a
starting point for a fabrication-oriented, sliced-aircraft workflow. It adds
**Slice Aircraft** to **Solid → Create** and opens a parameter dialog containing
placeholder inputs for Aircraft, Length, Rib Count, and Rib Thickness.

The initial SR-71 Blackbird definition generates an editable, station-based
fuselage loft. Each station is retained as a named construction plane and
sketch, followed by a native Fusion `LoftFeature`, so the resulting B-Rep is
inspectable and editable in the parametric timeline. Rib and export workflows
remain placeholders for future releases.

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
recipes. A definition receives Fusion's root component and a requested length
(in Fusion internal centimetres), creates a child component, and returns it.
`SR71Definition` is the first implementation. It creates ordered elliptical
station profiles on YZ offset planes and passes them to one solid loft feature.
This keeps the source geometry and the B-Rep timeline-friendly rather than
producing an opaque imported body.

## License

This project is licensed under the [MIT License](LICENSE).
