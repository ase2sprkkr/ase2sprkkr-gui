"""Invalid stored run metadata must not prevent the GUI history from loading."""

import json

from kkrunner import RunManager, RunStore

from ase2sprkkr_gui.gui.application.persistent_jobs import PersistentJobSource


def test_gui_loads_healthy_runs_and_warns_about_legacy_backend(tmp_path, caplog):
    store = RunStore(tmp_path / "history")
    manager = RunManager(store)
    for run_id in ("good", "obsolete"):
        record = manager.new_record(
            directory=tmp_path / run_id,
            run_id=run_id,
            metadata={"ase2sprkkr": {"task": "SCF"}},
        )
        store.save(record)

    path = store._path(store.get("obsolete"))
    data = json.loads(path.read_text())
    data["execution"]["backend"]["name"] = "process"
    path.write_text(json.dumps(data))
    unchanged = path.read_bytes()

    source = PersistentJobSource(manager)
    assert [job.id for job in source.jobs()] == ["good"]
    assert source.history_warning is not None
    assert "1 stored run record" in source.history_warning
    assert "Unsupported backend: 'process'" in caplog.text
    assert str(path) in caplog.text
    assert path.read_bytes() == unchanged

    assert source.job_changed("obsolete") is None
    assert source.history_warning is not None
    assert [job.id for job in source.reload()] == ["good"]
    assert [job.id for job in source.refresh()] == ["good"]

    # Once the invalid record is repaired, both entries become visible,
    # and the warning disappears without restarting the GUI.
    data["execution"]["backend"]["name"] = "direct"
    path.write_text(json.dumps(data))
    assert sorted(job.id for job in source.reload()) == ["good", "obsolete"]
    assert source.history_warning is None
