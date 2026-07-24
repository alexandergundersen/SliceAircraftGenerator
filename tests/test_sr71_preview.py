"""Tests for the standard-library SR-71 silhouette preview."""

from xml.etree import ElementTree as element_tree

from tools.render_sr71_preview import render_preview


def test_preview_contains_labeled_top_side_and_front_views() -> None:
    preview = render_preview(300)
    document = element_tree.tostring(preview.getroot(), encoding="unicode")

    assert "Top view" in document
    assert "Side view" in document
    assert "Front view" in document
    assert "SR-71 normalized silhouette preview" in document
