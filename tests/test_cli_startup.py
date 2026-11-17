"""Command-line startup reuses the existing workspace file workflows."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication, QWidget

from ase2sprkkr_gui.gui.flows import files as file_flows
from ase2sprkkr_gui.main import GuiApplication


@pytest.mark.parametrize(
    ("filename", "explicit_kind", "expected"),
    [
        ("Fe.cif", "auto", "structure"),
        ("Fe.pot", "auto", "structure"),
        ("result.out", "auto", "output"),
        ("settings.inp", "auto", "input"),
        ("ambiguous.txt", "output", "output"),
        ("ambiguous.txt", "structure", "structure"),
        ("outputs", "auto", "directory"),
    ],
)
def test_startup_target_uses_existing_file_flows(
    tmp_path, monkeypatch, filename, explicit_kind, expected
):
    application = QApplication.instance() or QApplication([])
    path = tmp_path / filename
    if filename == "outputs":
        path.mkdir()
    else:
        path.touch()
    gui = GuiApplication(recent_files_path=tmp_path / "recent.json")
    parent = QWidget()
    monkeypatch.setattr(gui, "create_workflow_window", lambda: parent)
    called = []

    def loader(kind):
        def load(_controller, _recent, target, _parent):
            called.append((kind, target))
            return (target,) if kind == "directory" else True
        return load

    for kind, method in (
        ("structure", "load_structure"),
        ("input", "load_input_parameters"),
        ("output", "load_output"),
        ("directory", "load_output_directory"),
    ):
        monkeypatch.setattr(file_flows, method, loader(kind))

    assert gui.open_startup_selection(explicit_kind, str(path))
    assert called == [(expected, path.resolve())]
    parent.close()


def test_open_last_selects_latest_existing_structure_not_latest_output(
    tmp_path, monkeypatch
):
    application = QApplication.instance() or QApplication([])
    gui = GuiApplication(recent_files_path=tmp_path / "recent.json")
    parent = QWidget()
    monkeypatch.setattr(gui, "create_workflow_window", lambda: parent)
    present = tmp_path / "Fe.cif"
    present.touch()
    missing = tmp_path / "deleted.cif"
    output = tmp_path / "result.out"
    output.touch()
    gui.recent_files.remember("structure", present)
    gui.recent_files.remember("structure", missing)
    gui.recent_files.remember("output", output)
    called = []
    monkeypatch.setattr(
        file_flows, "load_structure",
        lambda _controller, _recent, target, _parent: called.append(target) or True,
    )

    assert gui.open_startup_selection("last", None)
    assert called == [present.resolve()]
    assert gui.recent_files.paths("structure") == (str(present.resolve()),)
    assert gui.recent_files.paths("output") == (str(output.resolve()),)
    parent.close()


def test_open_last_with_no_existing_structure_warns(tmp_path, monkeypatch):
    application = QApplication.instance() or QApplication([])
    gui = GuiApplication(recent_files_path=tmp_path / "recent.json")
    parent = QWidget()
    monkeypatch.setattr(gui, "create_workflow_window", lambda: parent)
    warned = []
    monkeypatch.setattr(
        "ase2sprkkr_gui.main.QMessageBox.warning",
        lambda _parent, title, message: warned.append((title, message)),
    )
    gui.recent_files.remember("structure", tmp_path / "gone.cif")

    assert not gui.open_startup_selection("last", None)
    assert warned[0][0] == "No Recent Structure"
    parent.close()


def test_missing_explicit_startup_file_warns(tmp_path, monkeypatch):
    application = QApplication.instance() or QApplication([])
    gui = GuiApplication(recent_files_path=tmp_path / "recent.json")
    parent = QWidget()
    monkeypatch.setattr(gui, "create_workflow_window", lambda: parent)
    warned = []
    monkeypatch.setattr(
        "ase2sprkkr_gui.main.QMessageBox.warning",
        lambda _parent, title, message: warned.append((title, message)),
    )

    assert not gui.open_startup_selection("auto", str(tmp_path / "gone.cif"))
    assert warned[0][0] == "Cannot Open File"
    parent.close()
