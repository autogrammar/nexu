"""Tests for cinema_publish — packaging stages as runnable services."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nexu.cinema_publish import (
    list_published_services,
    publish_project_service,
    start_published_service,
    stop_published_service,
)


@pytest.fixture
def cinema_setup(tmp_path: Path):
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    (cinema / "stage0.html").write_text("<html><title>Calc</title><body>ok</body></html>", encoding="utf-8")
    root = tmp_path / "workspace"
    root.mkdir()
    capsule = "test_capsule"
    cap_dir = root / ".nexu" / "capsules" / capsule
    cap_dir.mkdir(parents=True)
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
