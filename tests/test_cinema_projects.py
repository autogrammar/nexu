import json
from pathlib import Path

from nexu.cinema_policy import _normalize_html_body
from nexu.cinema_projects import (
    EXAMPLE_PROJECTS,
    activate_example_project,
    delete_example_project,
    list_project_catalog,
)


def test_list_project_catalog_has_nine_examples():
    catalog = list_project_catalog()
    assert len(catalog["projects"]) == 9
    assert "web" in catalog["filters"]["domains"]


def test_workspace_catalog_can_hide_demo_project(tmp_path: Path):
    cinema = tmp_path / "cinema"
    cinema.mkdir()

    result = delete_example_project(cinema, "web_app_dashboard", workspace_root=tmp_path)
    catalog = list_project_catalog(cinema)

    assert result["status"] == "deleted"
    assert result["delete_mode"] == "workspace_tombstone"
    assert "web_app_dashboard" not in {p["id"] for p in catalog["projects"]}
    assert (cinema / "projects.deleted.json").exists()
    assert all(p.get("deletable") is True for p in catalog["projects"])


def test_activate_example_project_seeds_when_no_source(tmp_path: Path):
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    result = activate_example_project(cinema, "mcp_service", workspace_root=tmp_path)
    assert result["status"] == "project_activated"
    assert (cinema / "stage0.html").exists()
    assert (cinema / "alt_a.html").exists()
    html = (cinema / "stage0.html").read_text(encoding="utf-8").lower()
    assert "mcp" in html
    assert "app-shell" in html
    assert "calc-body" not in html
    assert "data-nexu-target" in html


def test_activate_frontend_view_seeds_selectable_web_gui(tmp_path: Path):
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    result = activate_example_project(cinema, "frontend_view", workspace_root=tmp_path)
    assert result["status"] == "project_activated"
    html = (cinema / "stage0.html").read_text(encoding="utf-8").lower()
    assert "frontend module" in html
    assert "app-shell" in html
    assert "calc-body" not in html
    assert html.count("data-nexu-target") >= 6
    assert "nexu-selectable" in html


def test_activate_analytics_copies_cinema_when_repo_available():
    repo = Path(__file__).resolve().parents[1]
    cinema = repo / "examples" / "_tmp_cinema_analytics_activate"
    if cinema.exists():
        import shutil

        shutil.rmtree(cinema)
    cinema.mkdir(parents=True)
    result = activate_example_project(
        cinema,
        "web_app_analytics",
        repo_root=repo,
        workspace_root=repo / "examples" / "web_app_calculator" / "workspace",
    )
    assert result["status"] == "project_activated"
    assert "stage0.html" in result["files_copied"]
    html = (cinema / "stage0.html").read_text(encoding="utf-8").lower()
    assert "analytics workspace" in html
    assert "funnel" in html
    assert "calc-body" not in html
    import shutil

    shutil.rmtree(cinema)


def test_activate_copies_dashboard_cinema_when_repo_available():
    repo = Path(__file__).resolve().parents[1]
    project = next(p for p in EXAMPLE_PROJECTS if p.id == "web_app_dashboard")
    cinema = repo / "examples" / "_tmp_cinema_activate"
    if cinema.exists():
        import shutil

        shutil.rmtree(cinema)
    cinema.mkdir(parents=True)
    result = activate_example_project(
        cinema,
        project.id,
        repo_root=repo,
        workspace_root=repo / "examples" / "web_app_calculator" / "workspace",
    )
    assert result["status"] == "project_activated"
    assert "stage0.html" in result["files_copied"]
    import shutil

    shutil.rmtree(cinema)


def test_activate_backend_service_resets_ledger_and_distinct_options(tmp_path: Path):
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    (cinema / "intract_policy_ledger.json").write_text(
        json.dumps(
            [
                {
                    "status": "goal_defined",
                    "user_goal": "chemical calculator",
                    "proposed_contracts": [{"line": "evolve:chemical_calculator"}],
                }
            ]
        ),
        encoding="utf-8",
    )
    for name in ("alt_a.html", "alt_b.html", "alt_c.html"):
        (cinema / name).write_text(
            '<!DOCTYPE html><html><body><div class="calc-body">same</div></body></html>',
            encoding="utf-8",
        )

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    result = activate_example_project(
        cinema,
        "backend_service",
        workspace_root=workspace,
        capsule_name="backend_capsule",
    )

    assert result["status"] == "project_activated"
    assert result.get("ledger_reset") is True
    assert result["goal_bootstrap"]["status"] == "requires_llm"
    ledger = json.loads((cinema / "intract_policy_ledger.json").read_text(encoding="utf-8"))
    assert len(ledger) == 1
    assert ledger[0]["status"] == "goal_defined"
    bodies = {
        name: _normalize_html_body((cinema / name).read_text(encoding="utf-8"))
        for name in ("alt_a.html", "alt_b.html", "alt_c.html")
    }
    assert len(set(bodies.values())) >= 2
    assert "calc-body" not in bodies["alt_a.html"].lower()
    assert "backend service" in bodies["alt_a.html"].lower()


def test_activate_dashboard_replaces_stale_calculator_options(tmp_path: Path):
    repo = Path(__file__).resolve().parents[1]
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    for name in ("alt_a.html", "alt_b.html", "alt_c.html"):
        (cinema / name).write_text(
            f'<!DOCTYPE html><html><body><div class="calc-body">{name}</div></body></html>',
            encoding="utf-8",
        )

    result = activate_example_project(
        cinema,
        "web_app_dashboard",
        repo_root=repo,
        workspace_root=tmp_path,
    )

    assert result["status"] == "project_activated"
    assert result["options_sync"]["status"] == "options_built_from_stages"
    alt_a = (cinema / "alt_a.html").read_text(encoding="utf-8").lower()
    alt_b = (cinema / "alt_b.html").read_text(encoding="utf-8").lower()
    assert "operations dashboard" in alt_a
    assert "calc-body" not in alt_a
    assert "scientific" not in alt_b


def test_activate_calculator_preserves_distinct_option_previews():
    repo = Path(__file__).resolve().parents[1]
    cinema = repo / "examples" / "_tmp_cinema_calc_activate"
    if cinema.exists():
        import shutil

        shutil.rmtree(cinema)
    cinema.mkdir(parents=True)
    result = activate_example_project(
        cinema,
        "web_app_calculator",
        repo_root=repo,
        workspace_root=repo / "examples" / "web_app_calculator" / "workspace",
        capsule_name="scientific_calc",
    )
    assert result["status"] == "project_activated"
    bodies = {
        name: _normalize_html_body((cinema / name).read_text(encoding="utf-8"))
        for name in ("alt_a.html", "alt_b.html", "alt_c.html")
    }
    assert len(set(bodies.values())) >= 2, "options A–C must differ on first load"
    import shutil

    shutil.rmtree(cinema)
