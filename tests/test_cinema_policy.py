import json
from pathlib import Path

from nexu.cinema_policy import (
    apply_ledger_from_cinema,
    append_iteration_ledger_entry,
    ensure_option_previews_from_stages,
    option_previews_are_distinct,
    effective_ui_constraints_from_ledger,
    enforce_deletes_on_option_previews,
    merge_ui_constraint_lists,
    normalize_manifest_target,
    normalize_proposals_for_ledger,
    propose_ui_delta_contract_dicts,
    resolve_iteration_mode,
    sync_option_previews_from_workspace,
    validate_intract_artifact,
)


def test_resolve_iteration_mode():
    assert resolve_iteration_mode(pending_goal=True, delete_count=2) == "active_workspace"
    assert resolve_iteration_mode(has_hints=True, delete_count=0, keep_count=1) == "active_workspace"
    assert resolve_iteration_mode(has_hints=True, delete_count=1) == "active_workspace"
    assert resolve_iteration_mode(has_hints=False, delete_count=0, keep_count=2) == "active_workspace"
    assert resolve_iteration_mode(has_hints=False, delete_count=0, keep_count=0) == "none"
    assert resolve_iteration_mode(pending_goal=True, has_hints=True) == "goal_options"


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


def test_effective_ui_constraints_from_ledger_last_wins():
    ledger = [
        {"stage": 0, "keep": ["sin", "cos"], "delete": []},
        {"stage": 0, "keep": [], "delete": ["cos"]},
        {"stage": 1, "keep": ["H"], "delete": []},
    ]
    effective = effective_ui_constraints_from_ledger(ledger, stage=0)
    assert effective["keep"] == ["sin"]
    assert effective["delete"] == ["cos"]


def test_effective_ui_constraints_filters_project_and_scope():
    ledger = [
        {
            "stage": 0,
            "keep": ["sin"],
            "delete": [],
            "project_id": "web_app_calculator",
            "focus_scope": "functions",
        },
        {
            "stage": 0,
            "keep": ["hero"],
            "delete": [],
            "project_id": "http-malortgdynia.pl",
            "focus_scope": "colors",
        },
        {
            "stage": 0,
            "keep": ["7"],
            "delete": [],
            "project_id": "http-malortgdynia.pl",
            "focus_scope": "functions",
        },
    ]
    http_colors = effective_ui_constraints_from_ledger(
        ledger,
        stage=0,
        project_id="http-malortgdynia.pl",
        project_kind="imported",
        focus_scope="colors",
    )
    assert http_colors["keep"] == ["hero"]
    assert "sin" not in http_colors["keep"]
    assert "7" not in http_colors["keep"]

    calc = effective_ui_constraints_from_ledger(
        ledger,
        stage=0,
        project_id="web_app_calculator",
        project_kind="calculator",
        focus_scope="functions",
    )
    assert calc["keep"] == ["sin"]


def test_promote_applies_spatial_deletes_only_for_functions_scope():
    from nexu.cinema_policy import promote_applies_spatial_deletes

    assert promote_applies_spatial_deletes("functions")
    assert promote_applies_spatial_deletes("")
    assert not promote_applies_spatial_deletes("colors")
    assert not promote_applies_spatial_deletes("display")
    assert not promote_applies_spatial_deletes("orientation")


def test_refresh_imported_policy_snapshot_keeps_markpact_separate_from_intract(
    tmp_path: Path,
) -> None:
    from nexu.cinema_policy import refresh_imported_policy_snapshot

    cinema = tmp_path / "cinema"
    cinema.mkdir()
    markpact = cinema / "imported_projects" / "http-example.net" / "README.markpact.md"
    markpact.parent.mkdir(parents=True)
    markpact.write_text("# Markpact\n", encoding="utf-8")
    meta = {
        "id": "http-example.net",
        "import_kind": "http",
        "markpact_path": str(markpact),
    }
    active = {"id": "http-example.net", "kind": "imported"}

    refresh_imported_policy_snapshot(cinema, meta, active)

    policy = json.loads((cinema / "intract_policy.json").read_text(encoding="utf-8"))
    project = policy["project"]
    assert project["has_intract_yaml"] is False
    assert project["intract_path"] is None
    assert project["markpact_path"] == str(markpact)


def test_intract_manifest_path_rejects_markpact_readme(tmp_path: Path) -> None:
    from nexu.cinema_policy import _intract_manifest_path

    markpact = tmp_path / "README.markpact.md"
    markpact.write_text("# Markpact\n", encoding="utf-8")
    intract = tmp_path / "intract.yaml"
    intract.write_text("version: intract.v1\n", encoding="utf-8")

    assert _intract_manifest_path(str(markpact)) is None
    assert _intract_manifest_path(str(intract)) == intract


def test_effective_ui_constraints_ignores_unscoped_when_focus_scope_set():
    ledger = [
        {"stage": 0, "keep": ["legacy_btn"], "delete": []},
        {"stage": 0, "keep": ["hero"], "delete": [], "focus_scope": "colors"},
    ]
    effective = effective_ui_constraints_from_ledger(ledger, stage=0, focus_scope="colors")
    assert effective["keep"] == ["hero"]
    assert "legacy_btn" not in effective["keep"]


def test_merge_ui_constraint_lists_session_overrides_ledger():
    keep, delete = merge_ui_constraint_lists(
        ledger_keep=["sin"],
        ledger_delete=["Mod"],
        session_keep=["cos"],
        session_delete=["sin"],
    )
    assert keep == ["cos"]
    assert delete == ["Mod", "sin"]


def test_sync_option_previews_empty_delete_ids_mirrors_workspace(tmp_path: Path):
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    html = """<!DOCTYPE html><html><body>
    <div class="btn btn-sci" id="btn-sin">sin</div>
    <div class="btn btn-sci" id="btn-cos">cos</div>
    <div class="btn btn-sci-excess" id="btn-Mod">Mod</div>
    </body></html>"""
    (cinema / "stage0.html").write_text(html, encoding="utf-8")
    ledger = [{"stage": 0, "keep": [], "delete": ["cos", "Mod"]}]
    (cinema / "intract_policy_ledger.json").write_text(
        json.dumps(ledger), encoding="utf-8"
    )

    result = sync_option_previews_from_workspace(
        cinema,
        stage=0,
        delete_ids=[],
        root=tmp_path,
        capsule_name="demo",
    )
    assert result["status"] == "options_synced_from_workspace"
    assert result["spatial_removed"] == []

    alt_a = (cinema / "alt_a.html").read_text(encoding="utf-8")
    assert "btn-cos" in alt_a and "btn-Mod" in alt_a


def test_sync_option_previews_from_workspace(tmp_path: Path):
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    html = """<!DOCTYPE html><html><head><title>Base</title></head><body>
    <div class="btn btn-sci" id="btn-sin">sin</div>
    <div class="btn btn-sci" id="btn-cos">cos</div>
    <div class="btn" id="btn-7">7</div>
    </body></html>"""
    (cinema / "stage0.html").write_text(html, encoding="utf-8")

    result = sync_option_previews_from_workspace(
        cinema, stage=0, delete_ids=["cos"]
    )
    assert result["status"] == "options_synced_from_workspace"
    assert "cos" in result["spatial_removed"]

    alt_a = (cinema / "alt_a.html").read_text(encoding="utf-8")
    assert "btn-sin" in alt_a and "btn-cos" not in alt_a
    assert "Option A (minimal)" in alt_a
    assert (cinema / "alt_b.html").exists() and (cinema / "alt_c.html").exists()


def test_enforce_deletes_on_option_previews(tmp_path: Path):
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    html = """<!DOCTYPE html><html><body>
    <div class="btn btn-sci" id="btn-sin">sin</div>
    <div class="btn btn-sci" id="btn-tan">tan</div>
    </body></html>"""
    for name in ("alt_a.html", "alt_b.html", "alt_c.html"):
        (cinema / name).write_text(html, encoding="utf-8")

    result = enforce_deletes_on_option_previews(cinema, ["tan"])
    assert result["status"] == "options_patched"
    assert "tan" in result["spatial_removed"]
    assert "btn-tan" not in (cinema / "alt_b.html").read_text(encoding="utf-8")


def test_ensure_option_previews_from_stages(tmp_path: Path):
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    (cinema / "stage0.html").write_text(
        "<html><head><title>S0</title></head><body><button>7</button></body></html>",
        encoding="utf-8",
    )
    (cinema / "stage1.html").write_text(
        "<html><head><title>S1</title></head><body><button>sin</button></body></html>",
        encoding="utf-8",
    )
    (cinema / "stage2.html").write_text(
        "<html><head><title>S2</title></head><body><button>sin</button><button>cos</button></body></html>",
        encoding="utf-8",
    )
    result = ensure_option_previews_from_stages(cinema)
    assert result["status"] == "options_built_from_stages"
    assert option_previews_are_distinct(cinema)


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


def test_iteration_ledger_contracts_use_active_project_and_scope(tmp_path: Path):
    entry = append_iteration_ledger_entry(
        tmp_path,
        "scientific_calc",
        stage=0,
        keep=["hero-title"],
        delete=["cta-primary"],
        status="evolved_by_llm",
        model="test-model",
        domain="web",
        project_id="http-sss.net.pl",
        focus_scope="colors",
        cinema_dir=tmp_path,
    )

    lines = [p["line"] for p in entry["proposed_contracts"]]
    assert any("id:cinema.http-sss.net.pl.S0.colors.remove.cta-primary" in line for line in lines)
    assert any("id:cinema.http-sss.net.pl.S0.colors.keep.hero-title" in line for line in lines)
    assert all("scope:colors" in line for line in lines)
    assert all("project:http-sss.net.pl" in line for line in lines)
    assert all("cinema.scientific_calc.S0.ui" not in line for line in lines)
