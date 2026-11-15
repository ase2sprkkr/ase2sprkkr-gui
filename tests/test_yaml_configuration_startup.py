"""Startup displays YAML parse errors instead of silently using defaults."""
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QMessageBox

import ase2sprkkr.configuration as configuration
from ase2sprkkr_gui import main as gui_main


@pytest.mark.parametrize("yaml_text", ("profiles: [\n", "- not a mapping\n"))
def test_startup_reports_malformed_yaml_without_changing_it(
    tmp_path, monkeypatch, yaml_text,
):
    path = tmp_path / "config.yaml"
    path.write_text(yaml_text, encoding="utf8")
    monkeypatch.setattr(configuration, "user_preferences_file", lambda: str(path))

    warnings = []
    monkeypatch.setattr(
        QMessageBox, "warning",
        lambda parent, title, body: warnings.append((title, body)),
    )
    gui_main._warn_unreadable_user_yaml()

    assert len(warnings) == 1
    title, body = warnings[0]
    assert "Invalid ASE2SPRKKR Configuration" == title
    assert str(path) in body
    assert "was not changed" in body
    assert path.read_text(encoding="utf8") == yaml_text

    # The warning disappears after correcting the file.
    path.write_text("running:\n  empty_spheres: true\n", encoding="utf8")
    gui_main._warn_unreadable_user_yaml()
    assert len(warnings) == 1
