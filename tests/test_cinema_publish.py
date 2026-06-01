"""Tests for cinema_publish — packaging stages as runnable services."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nexu.cinema_publish import (
    delete_published_service,
    list_published_services,
    publish_project_service,
    start_published_service,
    stop_published_service,
)


@pytest.fixture
def cinema_setup(tmp_path: Path):
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    (cinema / "stage0.html").write_text(
        "<html><title>Calc</title><body>ok</body></html>",
        encoding="utf-8",
    )
    root = tmp_path / "workspace"
    root.mkdir()
    capsule = "test_capsule"
    cap_dir = root / ".nexu" / "capsules" / capsule
    (cap_dir / "src").mkdir(parents=True)
    (cap_dir / "src" / "calculator.py").write_text("# calc\n", encoding="utf-8")
    (cap_dir / "policy.json").write_text('{"keep":[],"delete":[]}', encoding="utf-8")
    return cinema, root, capsule


def test_publish_creates_service_files(cinema_setup):
    cinema, root, capsule = cinema_setup
    result = publish_project_service(
        cinema,
        root,
        capsule,
        stage=0,
        project_id="demo-app",
        project_title="Demo App",
        user_goal="test goal",
        auto_start=False,
    )
    assert result.get("status") == "published"
    svc = result["service"]
    assert svc["id"] == "demo-app-s0"
    assert svc["published"] is True
    assert svc["markpact"] is True
    service_dir = cinema / "services" / "demo-app-s0"
    assert (service_dir / "index.html").exists()
    assert (service_dir / "README.md").exists()
    assert (service_dir / "service-meta.json").exists()
    assert (service_dir / "export-markpact.md").exists()
    service_meta = json.loads((service_dir / "service-meta.json").read_text(encoding="utf-8"))
    capsule_contracts = service_meta["baseline_contracts"]["capsule"]
    assert any(item["id"] == "calc.app.kind" for item in capsule_contracts)
    assert "Intract baseline model" in (service_dir / "export-markpact.md").read_text(
        encoding="utf-8"
    )


def test_list_and_start_stop_service(cinema_setup):
    cinema, root, capsule = cinema_setup
    publish_project_service(
        cinema,
        root,
        capsule,
        stage=0,
        project_id="run-app",
        auto_start=False,
    )
    catalog = list_published_services(cinema)
    assert catalog["count"] == 1
    assert catalog["services"][0]["status"] == "stopped"

    started = start_published_service(cinema, "run-app-s0")
    assert started.get("status") in ("started", "already_running")
    assert started["service"]["status"] == "running"

    catalog2 = list_published_services(cinema)
    assert catalog2["services"][0]["status"] == "running"

    stopped = stop_published_service(cinema, "run-app-s0")
    assert stopped["status"] == "stopped"

    registry = json.loads((cinema / "services" / "registry.json").read_text(encoding="utf-8"))
    entry = next(s for s in registry["services"] if s["id"] == "run-app-s0")
    assert entry["status"] == "stopped"


def test_publish_missing_stage_returns_error(cinema_setup):
    cinema, root, capsule = cinema_setup
    result = publish_project_service(cinema, root, capsule, stage=9, auto_start=False)
    assert "error" in result


def test_publish_http_import_bundles_source_assets(tmp_path: Path):
    """Published services must include imported project CSS/assets, not only index.html."""
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    project_id = "http-sss.net.pl"
    source_dir = cinema / "imported_projects" / project_id / "source"
    assets_dir = source_dir / "assets"
    assets_dir.mkdir(parents=True)
    (source_dir / "nexu-extracted.css").write_text(
        "body { overflow: visible; } .hero { width: 100%; }",
        encoding="utf-8",
    )
    (assets_dir / "stylesheet-0.css").write_text(
        "h1 { white-space: normal; }",
        encoding="utf-8",
    )
    stage0 = f"""<!DOCTYPE html><html><head>
<link rel="stylesheet" href="imported_projects/{project_id}/source/nexu-extracted.css">
<link rel="stylesheet" href="imported_projects/{project_id}/source/assets/stylesheet-0.css">
</head><body><h1 class="hero">Sss.Net.Pl</h1></body></html>"""
    (cinema / "stage0.html").write_text(stage0, encoding="utf-8")

    root = tmp_path / "workspace"
    root.mkdir()
    capsule = "test_capsule"
    cap_dir = root / ".nexu" / "capsules" / capsule
    (cap_dir / "src").mkdir(parents=True)
    (cap_dir / "policy.json").write_text('{"keep":[],"delete":[]}', encoding="utf-8")

    result = publish_project_service(
        cinema,
        root,
        capsule,
        stage=0,
        project_id=project_id,
        project_title="Sss.Net.Pl",
        auto_start=False,
    )
    assert result.get("status") == "published"
    service_dir = cinema / "services" / f"{project_id}-s0"
    index_html = (service_dir / "index.html").read_text(encoding="utf-8")
    assert f'imported_projects/{project_id}/source/' not in index_html
    assert 'href="source/nexu-extracted.css"' in index_html
    assert 'href="source/assets/stylesheet-0.css"' in index_html
    assert (service_dir / "source" / "nexu-extracted.css").is_file()
    assert (service_dir / "source" / "assets" / "stylesheet-0.css").is_file()
    assert "source/nexu-extracted.css" in result.get("copied_assets", [])


def test_delete_published_service_removes_registry_and_files(cinema_setup):
    cinema, root, capsule = cinema_setup
    publish_project_service(
        cinema,
        root,
        capsule,
        stage=0,
        project_id="del-app",
        auto_start=False,
    )
    service_id = "del-app-s0"
    service_dir = cinema / "services" / service_id
    assert service_dir.is_dir()

    started = start_published_service(cinema, service_id)
    assert started.get("status") in ("started", "already_running")

    deleted = delete_published_service(cinema, service_id)
    assert deleted.get("status") == "deleted"
    assert deleted.get("id") == service_id
    assert not service_dir.exists()

    registry = json.loads((cinema / "services" / "registry.json").read_text(encoding="utf-8"))
    assert registry.get("services") == []
    assert list_published_services(cinema)["count"] == 0


def test_delete_unknown_service_returns_error(cinema_setup):
    cinema, root, capsule = cinema_setup
    result = delete_published_service(cinema, "missing-s0")
    assert "error" in result
