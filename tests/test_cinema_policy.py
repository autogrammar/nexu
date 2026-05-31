import json
from pathlib import Path

from nexu.cinema_policy import (
    apply_ledger_from_cinema,
    normalize_manifest_target,
    normalize_proposals_for_ledger,
    propose_ui_delta_contract_dicts,
    resolve_iteration_mode,
    validate_intract_artifact,
)


def test_resolve_iteration_mode():
    assert resolve_iteration_mode(pending_goal=True, delete_count=2) == "goal_options"
    assert resolve_iteration_mode(has_hints=True, delete_count=0, keep_count=1) == "goal_options"
    assert resolve_iteration_mode(has_hints=True, delete_count=1) == "active_workspace"
    assert resolve_iteration_mode(has_hints=False, delete_count=0, keep_count=2) == "active_workspace"
    assert resolve_iteration_mode(has_hints=False, delete_count=0, keep_count=0) == "none"


def test_normalize_manifest_target_defaults_invalid():
    assert normalize_manifest_target("bogus") == "both"
    assert normalize_manifest_target("project") == "project"


def test_apply_ledger_from_cinema_project_only(tmp_path: Path):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "intract.yaml").write_text(
        "version: intract.v1\ncontracts: []\n",
        encoding="utf-8",
    )
    capsule = workspace / ".nexu" / "capsules" / "demo"
    cinema = capsule / "cinema"
    cinema.mkdir(parents=True)
    line = (
        '@intract.v1 id:cinema.demo.S0.ui.remove.A scope:ui intent:ui:remove:A '
        'priority:3 domain:ui effect:ui_change forbid:destructive_write '
        'validate:no_forbidden_effect meaning:"removed A"'
    )
    (cinema / "intract_policy_ledger.json").write_text(
        json.dumps([{"status": "evolved_by_llm", "proposed_contracts": [{"line": line}]}]),
        encoding="utf-8",
    )
    (cinema / "intract_policy.json").write_text(
        json.dumps(
            {
                "project": {"intract_path": str(workspace / "intract.yaml")},
                "capsule": {"intract_path": str(capsule / "intract.yaml")},
            }
        ),
        encoding="utf-8",
    )

    result = apply_ledger_from_cinema(workspace, "demo", target="project", dry_run=True)
    assert result["added_total"] == 1
    assert "cinema.demo.S0.ui.remove.A" not in (workspace / "intract.yaml").read_text(encoding="utf-8")


def test_propose_ui_delta_and_validate(tmp_path: Path):
    proposals = propose_ui_delta_contract_dicts(
        stage=0, keep=["Btn"], delete=["Mod"], capsule_name="demo"
    )
    normalized = normalize_proposals_for_ledger(0, "demo", proposals)
    assert len(normalized) == 2
    assert all(item.get("delta_text") for item in normalized)
    html = "<!DOCTYPE html><html><body><button id='Btn'></button></body></html>"
    report = validate_intract_artifact(html, normalized, filename="stage0.html", root=tmp_path)
    assert report is not None
    assert report.get("status") in {"pass", "partial", "warn", "unavailable", "error"}
