"""Tests for cinema checkpoint history."""

import json
from pathlib import Path

from nexu.cinema_history import (
    list_history_checkpoints,
    restore_history_checkpoint,
    save_history_checkpoint,
)


def test_save_list_and_restore_files(tmp_path: Path, monkeypatch) -> None:
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    (cinema / "stage0.html").write_text("<html>v1</html>", encoding="utf-8")
    (cinema / "intract_policy_ledger.json").write_text("[]", encoding="utf-8")

    cp1 = save_history_checkpoint(
        cinema, action="iterate", stage=0, status="evolved_by_llm", delete=["Mod"]
    )
    assert cp1["id"] == "cp_0000"

    (cinema / "stage0.html").write_text("<html>v2</html>", encoding="utf-8")
    (cinema / "intract_policy_ledger.json").write_text(
        '[{"timestamp":"t1","proposed_contracts":[]}]', encoding="utf-8"
    )
    save_history_checkpoint(cinema, action="iterate", stage=0, status="evolved_by_spatial_patch")

    listed = list_history_checkpoints(cinema)
    assert len(listed) == 2
    assert listed[0]["id"] == "cp_0001"

    monkeypatch.setattr(
        "nexu.cinema_history.cinema_dir_for", lambda _root, _name: cinema
    )
    monkeypatch.setattr("nexu.cinema_history._refresh_policy_snapshot", lambda *_a: None)
    monkeypatch.setattr(
        "nexu.cinema_history.apply_ledger_from_cinema",
        lambda *_a, **_k: {"added_total": 0, "results": []},
    )

    result = restore_history_checkpoint(
        tmp_path, "scientific_calc", "cp_0000", apply_manifest=True
    )
    assert result["status"] == "restored"
    assert (cinema / "stage0.html").read_text(encoding="utf-8") == "<html>v1</html>"
    ledger = json.loads((cinema / "intract_policy_ledger.json").read_text(encoding="utf-8"))
    assert ledger == []
