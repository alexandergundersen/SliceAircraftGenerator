"""Render a standard-library-only SVG silhouette preview from SR-71 geometry data."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as element_tree


def _load_geometry_data_module() -> object:
    """Load the canonical pure data module when this tool runs as a script.

    A direct ``python3 tools/render_sr71_preview.py`` invocation gives Python
    the tools directory rather than the repository root as its import location.
    Loading this one pure module by file location preserves the same source of
    truth without modifying ``sys.path`` or duplicating normalized data.
    """
    module_path = Path(__file__).resolve().parents[1] / "geometry" / "sr71_data.py"
    module_spec = importlib.util.spec_from_file_location("sr71_preview_data", module_path)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError("Unable to load the SR-71 pure geometry data module.")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


_GEOMETRY_DATA = _load_geometry_data_module()
SOURCE_WINGSPAN_RATIO = _GEOMETRY_DATA.SOURCE_WINGSPAN_RATIO
SR71_DATA = _GEOMETRY_DATA.SR71_DATA

SVG_NS = "http://www.w3.org/2000/svg"
element_tree.register_namespace("", SVG_NS)


@dataclass(frozen=True)
class Viewport:
    """Map one normalized drawing extent into a labeled SVG view box."""

    origin_x: float
    origin_y: float
    width: float
    height: float
    min_x: float
    max_x: float
    min_y: float
    max_y: float

    def point(self, x_value: float, y_value: float) -> tuple[float, float]:
        x_span = self.max_x - self.min_x
        y_span = self.max_y - self.min_y
        return (
            self.origin_x + (x_value - self.min_x) / x_span * self.width,
            self.origin_y + self.height - (y_value - self.min_y) / y_span * self.height,
        )


def _svg_element(tag: str, **attributes: str) -> element_tree.Element:
    return element_tree.Element(f"{{{SVG_NS}}}{tag}", attributes)


def _add_text(parent: element_tree.Element, x_value: float, y_value: float, text: str) -> None:
    label = element_tree.SubElement(parent, f"{{{SVG_NS}}}text", x=f"{x_value:g}", y=f"{y_value:g}")
    label.text = text


def _add_polyline(
    parent: element_tree.Element,
    viewport: Viewport,
    points: tuple[tuple[float, float], ...],
    *,
    css_class: str,
    closed: bool = False,
) -> None:
    if closed:
        points = (*points, points[0])
    encoded_points = " ".join(
        f"{x_value:.2f},{y_value:.2f}"
        for x_value, y_value in (viewport.point(*point) for point in points)
    )
    element_tree.SubElement(
        parent,
        f"{{{SVG_NS}}}polyline",
        points=encoded_points,
        **{"class": css_class},
    )


def _add_bounds(parent: element_tree.Element, viewport: Viewport, label: str) -> None:
    element_tree.SubElement(
        parent,
        f"{{{SVG_NS}}}rect",
        x=f"{viewport.origin_x:g}",
        y=f"{viewport.origin_y:g}",
        width=f"{viewport.width:g}",
        height=f"{viewport.height:g}",
        **{"class": "bounds"},
    )
    _add_text(parent, viewport.origin_x, viewport.origin_y - 10, label)


def _top_view(parent: element_tree.Element, length_mm: float) -> None:
    scaled = SR71_DATA.scale(length_mm / 10)
    half_span_mm = scaled.half_span_cm * 10
    viewport = Viewport(40, 45, 520, 260, 0, length_mm, -half_span_mm, half_span_mm)
    _add_bounds(parent, viewport, "Top view")
    right_planform = tuple((x_cm * 10, y_cm * 10) for x_cm, y_cm in scaled.right_planform_points_cm)
    planform = (
        *right_planform,
        *((x_value, -y_value) for x_value, y_value in reversed(right_planform[1:-1])),
    )
    _add_polyline(parent, viewport, planform, css_class="planform", closed=True)
    fuselage_right = tuple(
        (station.position_cm * 10, station.half_width_cm * 10)
        for station in scaled.fuselage_stations
    )
    fuselage = (
        *fuselage_right,
        *((x_value, -y_value) for x_value, y_value in reversed(fuselage_right)),
    )
    _add_polyline(parent, viewport, fuselage, css_class="fuselage", closed=True)
    canopy_right = tuple(
        (station.position_cm * 10, station.half_width_cm * 10) for station in scaled.canopy_stations
    )
    canopy = (*canopy_right, *((x_value, -y_value) for x_value, y_value in reversed(canopy_right)))
    _add_polyline(parent, viewport, canopy, css_class="canopy", closed=True)
    for sign in (-1, 1):
        nacelle_outer = tuple(
            (
                station.position_cm * 10,
                sign * (station.center_y_cm + station.half_width_cm) * 10,
            )
            for station in scaled.nacelle_stations
        )
        nacelle_inner = tuple(
            (
                station.position_cm * 10,
                sign * (station.center_y_cm - station.half_width_cm) * 10,
            )
            for station in reversed(scaled.nacelle_stations)
        )
        _add_polyline(
            parent, viewport, (*nacelle_outer, *nacelle_inner), css_class="nacelle", closed=True
        )
        tail = scaled.tail
        root_y = sign * tail.root_y_cm * 10
        tip_y = sign * (tail.root_y_cm + tail.outward_tip_offset_cm) * 10
        _add_polyline(
            parent,
            viewport,
            (
                (tail.root_leading_x_cm * 10, root_y),
                (tail.root_trailing_x_cm * 10, root_y),
                (tail.tip_trailing_x_cm * 10, tip_y),
                (tail.tip_leading_x_cm * 10, tip_y),
            ),
            css_class="tail",
            closed=True,
        )
    _add_polyline(parent, viewport, ((0, 0), (length_mm, 0)), css_class="centerline")


def _side_view(parent: element_tree.Element, length_mm: float) -> None:
    scaled = SR71_DATA.scale(length_mm / 10)
    viewport = Viewport(40, 370, 520, 210, 0, length_mm, -length_mm * 0.06, length_mm * 0.12)
    _add_bounds(parent, viewport, "Side view")
    fuselage_upper = tuple(
        (station.position_cm * 10, station.upper_height_cm * 10)
        for station in scaled.fuselage_stations
    )
    fuselage_lower = tuple(
        (station.position_cm * 10, -station.lower_height_cm * 10)
        for station in reversed(scaled.fuselage_stations)
    )
    _add_polyline(
        parent, viewport, (*fuselage_upper, *fuselage_lower), css_class="fuselage", closed=True
    )
    wing_half_thickness = scaled.wing_thickness_cm * 5
    _add_polyline(
        parent,
        viewport,
        (
            (0, -wing_half_thickness),
            (length_mm, -wing_half_thickness),
            (length_mm, wing_half_thickness),
            (0, wing_half_thickness),
        ),
        css_class="wing",
        closed=True,
    )
    nacelle_upper = tuple(
        (station.position_cm * 10, (station.center_z_cm + station.half_height_cm) * 10)
        for station in scaled.nacelle_stations
    )
    nacelle_lower = tuple(
        (station.position_cm * 10, (station.center_z_cm - station.half_height_cm) * 10)
        for station in reversed(scaled.nacelle_stations)
    )
    _add_polyline(
        parent, viewport, (*nacelle_upper, *nacelle_lower), css_class="nacelle", closed=True
    )
    _add_polyline(
        parent,
        viewport,
        tuple((x_cm * 10, z_cm * 10) for x_cm, z_cm in scaled.tail.side_profile_points_cm),
        css_class="tail",
        closed=True,
    )
    _add_polyline(parent, viewport, scaled.canopy_top_profile_cm, css_class="canopy")
    _add_polyline(parent, viewport, ((0, 0), (length_mm, 0)), css_class="centerline")


def _front_view(parent: element_tree.Element, length_mm: float) -> None:
    scaled = SR71_DATA.scale(length_mm / 10)
    half_span_mm = scaled.half_span_cm * 10
    viewport = Viewport(
        620, 45, 330, 260, -half_span_mm, half_span_mm, -length_mm * 0.06, length_mm * 0.12
    )
    _add_bounds(parent, viewport, "Front view")
    wing_half_thickness = scaled.wing_thickness_cm * 5
    _add_polyline(
        parent,
        viewport,
        (
            (-half_span_mm, -wing_half_thickness),
            (half_span_mm, -wing_half_thickness),
            (half_span_mm, wing_half_thickness),
            (-half_span_mm, wing_half_thickness),
        ),
        css_class="wing",
        closed=True,
    )
    widest_fuselage = max(scaled.fuselage_stations, key=lambda station: station.half_width_cm)
    _add_polyline(
        parent,
        viewport,
        (
            (-widest_fuselage.half_width_cm * 10, -widest_fuselage.lower_height_cm * 10),
            (widest_fuselage.half_width_cm * 10, -widest_fuselage.lower_height_cm * 10),
            (widest_fuselage.half_width_cm * 10, widest_fuselage.upper_height_cm * 10),
            (-widest_fuselage.half_width_cm * 10, widest_fuselage.upper_height_cm * 10),
        ),
        css_class="fuselage",
        closed=True,
    )
    main_nacelle = max(scaled.nacelle_stations, key=lambda station: station.half_width_cm)
    nacelle_radius_x = (
        main_nacelle.half_width_cm * 10 / (viewport.max_x - viewport.min_x) * viewport.width
    )
    nacelle_radius_y = (
        main_nacelle.half_height_cm * 10 / (viewport.max_y - viewport.min_y) * viewport.height
    )
    for sign in (-1, 1):
        center_x, center_y = viewport.point(
            sign * main_nacelle.center_y_cm * 10, main_nacelle.center_z_cm * 10
        )
        element_tree.SubElement(
            parent,
            f"{{{SVG_NS}}}ellipse",
            cx=f"{center_x:.2f}",
            cy=f"{center_y:.2f}",
            rx=f"{nacelle_radius_x:.2f}",
            ry=f"{nacelle_radius_y:.2f}",
            **{"class": "nacelle"},
        )
    for sign in (-1, 1):
        _add_polyline(
            parent,
            viewport,
            (
                (sign * scaled.tail.root_y_cm * 10, scaled.tail.base_z_cm * 10),
                (
                    sign * (scaled.tail.root_y_cm + scaled.tail.outward_tip_offset_cm) * 10,
                    scaled.tail.tip_z_cm * 10,
                ),
            ),
            css_class="tail",
        )
    _add_polyline(
        parent, viewport, ((0, -length_mm * 0.06), (0, length_mm * 0.12)), css_class="centerline"
    )


def render_preview(length_mm: float) -> element_tree.ElementTree:
    """Build an SVG document whose views all derive from ``SR71_DATA``."""
    if length_mm <= 0:
        raise ValueError("Preview length must be greater than zero.")
    root = _svg_element("svg", width="1000", height="630", viewBox="0 0 1000 630")
    style = element_tree.SubElement(root, f"{{{SVG_NS}}}style")
    style.text = (
        "text{font:14px sans-serif;fill:#1f2937}.bounds{fill:none;stroke:#94a3b8}"
        ".centerline{fill:none;stroke:#94a3b8;stroke-dasharray:5 4}"
        ".planform{fill:#dbeafe;stroke:#1d4ed8;stroke-width:2}"
        ".wing{fill:#dbeafe;stroke:#1d4ed8;stroke-width:2}"
        ".fuselage{fill:#cbd5e1;stroke:#334155;stroke-width:2}"
        ".nacelle{fill:#94a3b8;stroke:#334155;stroke-width:2}"
        ".canopy{fill:none;stroke:#0f766e;stroke-width:3}"
        ".tail{fill:#fecaca;stroke:#b91c1c;stroke-width:2}"
    )
    _add_text(
        root,
        40,
        22,
        "SR-71 normalized silhouette preview — "
        f"length {length_mm:g} mm, span {length_mm * SOURCE_WINGSPAN_RATIO:g} mm",
    )
    _top_view(root, length_mm)
    _side_view(root, length_mm)
    _front_view(root, length_mm)
    return element_tree.ElementTree(root)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--length-mm", type=float, required=True, help="Requested overall model length"
    )
    parser.add_argument("--output", type=Path, required=True, help="SVG output path")
    arguments = parser.parse_args()
    preview = render_preview(arguments.length_mm)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    preview.write(arguments.output, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    main()
