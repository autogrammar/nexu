from pathlib import Path

from nexu.cinema_policy import _normalize_html_body
from nexu.cinema_projects import (
    EXAMPLE_PROJECTS,
    activate_example_project,
    list_project_catalog,
)


def test_list_project_catalog_has_nine_examples():
    catalog = list_project_catalog()
    assert len(catalog["projects"]) == 9
    assert "web" in catalog["filters"]["domains"]


def test_activate_example_project_seeds_when_no_source(tmp_path: Path):
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    result = activate_example_project(cinema, "mcp_service", workspace_root=tmp_path)
    assert result["status"] == "project_activated"
    assert (cinema / "stage0.html").exists()
    assert (cinema / "alt_a.html").exists()
    assert "mcp" in (cinema / "stage0.html").read_text(encoding="utf-8").lower()


def test_activate_copies_dashboard_cinema_when_repo_available():
    repo = Path(__file__).resolve().parents[1]
    project = next(p for p in EXAMPLE_PROJECTS if p.id == "web_app_dashboard")
    cinema = repo / "examples" / "_tmp_cinema_activate"
    if cinema.exists():
        import shutil

        shutil.rmtree(cinema)
    cinema.mkdir(parents=True)
    result = activate_example_project(
        cinema, project.id, repo_root=repo, workspace_root=repo / "examples" / "web_app_calculator" / "workspace"
    )
    assert result["status"] == "project_activated"
    assert "stage0.html" in result["files_copied"]
    import shutil

    shutil.rmtree(cinema)


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
