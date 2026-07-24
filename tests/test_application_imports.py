"""Regression tests for package-relative application imports."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INTERNAL_PACKAGES = frozenset({"aircraft", "commands", "geometry", "utils", "export"})
APPLICATION_PACKAGES = ("aircraft", "commands", "geometry", "utils", "export")
APPLICATION_SOURCES = (
    PROJECT_ROOT / "SliceAircraftGenerator.py",
    *(path for package in APPLICATION_PACKAGES for path in (PROJECT_ROOT / package).rglob("*.py")),
)


class ApplicationImportTests(unittest.TestCase):
    """Ensure application code never bypasses the add-in package namespace."""

    def test_internal_packages_are_only_imported_relatively(self) -> None:
        violations: list[str] = []

        for source_path in APPLICATION_SOURCES:
            source_tree = ast.parse(
                source_path.read_text(encoding="utf-8"), filename=str(source_path)
            )
            for node in ast.walk(source_tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in INTERNAL_PACKAGES:
                            violations.append(
                                f"{source_path.relative_to(PROJECT_ROOT)}:{node.lineno}: "
                                f"absolute import {alias.name}"
                            )
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    if node.module.split(".")[0] in INTERNAL_PACKAGES:
                        violations.append(
                            f"{source_path.relative_to(PROJECT_ROOT)}:{node.lineno}: "
                            f"absolute import from {node.module}"
                        )

        self.assertEqual(violations, [])
