from pathlib import Path

from nexu.cinema_goal_contracts import (
    goal_traits_from_contract_lines,
    propose_goal_extension_contracts,
)
from nexu.cinema_offline_options import write_goal_options_offline
from nexu.cinema_policy import append_goal_ledger_entry, load_goal_contract_lines


def test_propose_goal_extension_has_baseline_require():
    proposals = propose_goal_extension_contracts(
        "kalkulator chemiczny z masą molową",
        capsule_name="scientific_calc",
        stage=0,
    )
    assert len(proposals) >= 2
    primary = proposals[0]
    assert primary["kind"] == "goal_extension"
    assert "freeze.baseline" in primary["require"]
    assert "calc.app.kind" in primary["require"]
    assert "define:target_solution" in primary["intent"]
    ids = {p["id"] for p in proposals}
    assert any("trait.chemical" in i for i in ids)


def test_goal_ledger_roundtrip(tmp_path: Path):
    base = tmp_path / ".nexu" / "capsules" / "scientific_calc"
    (base / "src").mkdir(parents=True)
    (base / "src" / "calculator.py").write_text("# calc\n")
    cinema = base / "cinema"
    cinema.mkdir(parents=True)
    entry = append_goal_ledger_entry(
        tmp_path,
        "scientific_calc",
        stage=0,
        goal="scientific calculator with periodic table",
    )
    assert entry["status"] == "goal_defined"
    assert len(entry["proposed_contracts"]) >= 1
    lines = load_goal_contract_lines(tmp_path, "scientific_calc")
    assert lines
    assert any("define:target_solution" in line for line in lines)


def test_goal_ledger_stores_scope_contract_context(tmp_path: Path):
    base = tmp_path / ".nexu" / "capsules" / "frontend_view"
    (base / "src").mkdir(parents=True)
    (base / "src" / "view.py").write_text("# view\n")
    (base / "cinema").mkdir(parents=True)

    entry = append_goal_ledger_entry(
        tmp_path,
        "frontend_view",
        stage=0,
        goal="#components focus for Frontend Module\nExpected version/actions: add states",
        focus_scope="components",
        focus_scope_label="#components",
        current_state="isolated menu component",
        expected_version="show active, hover and disabled states",
        project_context="Frontend Module (frontend/web)",
    )

    assert entry["focus_scope"] == "components"
    assert entry["current_state"] == "isolated menu component"
    assert entry["expected_version"] == "show active, hover and disabled states"
    assert any(p["intent"] == "focus:components" for p in entry["proposed_contracts"])
    assert any("scope.components" in p["id"] for p in entry["proposed_contracts"])


def test_goal_traits_from_contract_lines():
    proposals = propose_goal_extension_contracts(
        "analytics dashboard for space agency engineers",
        capsule_name="web_app_analytics",
        stage=0,
    )
    contract_lines = [p["line"] for p in proposals if p.get("line")]
    traits = goal_traits_from_contract_lines(contract_lines)
    assert traits["dashboard"]
    assert traits["engineering"]


def test_funnels_cohorts_goal_gets_dashboard_trait():
    proposals = propose_goal_extension_contracts(
        "Funnels, cohorts, and experiment flags",
        capsule_name="scientific_calc",
        stage=0,
    )
    ids = {p["id"] for p in proposals}
    assert any("trait.dashboard" in i for i in ids)


def test_api_routes_goal_gets_api_trait_and_template_anchor():
    proposals = propose_goal_extension_contracts(
        "API routes and contract surface",
        capsule_name="scientific_calc",
        stage=0,
        project_kind="api",
    )
    ids = {p["id"] for p in proposals}
    assert any("trait.api" in i for i in ids)
    target = next(p for p in proposals if p["id"].startswith("goal.") and "target" in p["id"])
    assert "ui.template" in target["based_on"]


def test_offline_project_options_show_goal_banner(tmp_path: Path):
    (tmp_path / "active_project.json").write_text(
        '{"id": "web_app_analytics", "kind": "dashboard"}',
        encoding="utf-8",
    )
    for stage in (0, 1, 2):
        (tmp_path / f"stage{stage}.html").write_text(
            f"<!DOCTYPE html><html><body><h1>Stage {stage}</h1></body></html>",
            encoding="utf-8",
        )
    labels = write_goal_options_offline(
        tmp_path,
        hints=[],
        user_goal="KPI charts for space agency",
        goal_contract_lines=[
            "# @intract.v1 intent:evolve:analytics_dashboard",
        ],
    )
    assert len(labels) == 3
    alt_a = (tmp_path / "alt_a.html").read_text(encoding="utf-8")
    assert "nexu-goal-banner" in alt_a
    assert "space agency" in alt_a
