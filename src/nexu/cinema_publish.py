"""Publish Nexu workspace stages as runnable Markpact services."""

from __future__ import annotations

import json
import re
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from .cinema_markpact import _escape_markdown_fence, build_markpact_readme
from .cinema_policy import load_effective_ui_constraints

SERVICES_DIR_NAME = "services"
REGISTRY_FILE = "registry.json"
PORT_RANGE = range(9200, 9299)


def services_root(cinema_dir: Path) -> Path:
    return cinema_dir / SERVICES_DIR_NAME


def _registry_path(cinema_dir: Path) -> Path:
    return services_root(cinema_dir) / REGISTRY_FILE


def _load_registry(cinema_dir: Path) -> dict[str, Any]:
    path = _registry_path(cinema_dir)
    if not path.exists():
        return {"services": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"services": []}
    data.setdefault("services", [])
    return data


def _save_registry(cinema_dir: Path, data: dict[str, Any]) -> None:
    root = services_root(cinema_dir)
    root.mkdir(parents=True, exist_ok=True)
    _registry_path(cinema_dir).write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _slug_service_id(project_id: str, capsule_name: str, stage: int) -> str:
    base = project_id or capsule_name or "nexu-app"
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", base).strip("-") or "nexu-app"
    return f"{safe}-s{stage}"


def _pick_port(used: set[int]) -> int | None:
    for port in PORT_RANGE:
        if port in used:
            continue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    return None


def _port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.4):
            return True
    except OSError:
        return False


def _http_ok(url: str) -> bool:
    try:
        with urlopen(url, timeout=0.6) as resp:
            return 200 <= resp.status < 500
    except (URLError, OSError, ValueError):
        return False


def _service_alive(entry: dict[str, Any]) -> bool:
    pid = entry.get("pid")
    port = entry.get("port")
    if pid:
        try:
            import os

            os.kill(int(pid), 0)
        except (OSError, ProcessLookupError, ValueError):
            return False
    if port and _port_open(int(port)):
        url = entry.get("url") or f"http://127.0.0.1:{port}/"
        return _http_ok(url)
    return False


def _refresh_service_status(entry: dict[str, Any]) -> dict[str, Any]:
    alive = _service_alive(entry)
    entry["status"] = "running" if alive else "stopped"
    if not alive:
        entry["pid"] = None
    return entry


def list_published_services(cinema_dir: Path) -> dict[str, Any]:
    """Return published services with live status."""
    data = _load_registry(cinema_dir)
    services = [_refresh_service_status(dict(item)) for item in data.get("services") or []]
    _save_registry(cinema_dir, {"services": services})
    return {"services": services, "count": len(services)}


def _write_service_readme(
    service_dir: Path,
    *,
    cinema_dir: Path,
    stage: int,
    capsule_name: str,
    user_goal: str,
    effective_ui: dict[str, Any],
    port: int,
) -> str:
    html = (service_dir / "index.html").read_text(encoding="utf-8")
    title_match = re.search(r"<title[^>]*>([^<]*)</title>", html, flags=re.I)
    app_title = (
        title_match.group(1).strip() if title_match else None
    ) or f"{capsule_name} S{stage}"
    goal_line = user_goal.strip() or "(none recorded)"
    meta = {
        "published_at": datetime.now(timezone.utc).isoformat(),
        "capsule": capsule_name,
        "stage": stage,
        "port": port,
        "user_goal": goal_line,
        "policy_keep": list(effective_ui.get("keep") or []),
        "policy_delete": list(effective_ui.get("delete") or []),
    }
    html_body = _escape_markdown_fence(html)
    readme = f"""# {app_title} — published Nexu service

Runnable **Markpact** service published from Nexu (stage {stage}).

## Run

```bash markpact:run
python -m http.server {port}
```

Open **http://127.0.0.1:{port}/** after start.

```json markpact:file path=service-meta.json
{json.dumps(meta, indent=2, ensure_ascii=False)}
```

```html markpact:file path=index.html
{html_body}
```

> **Linux one-liner:** `cd "$(dirname "$0")" && python3 -m http.server {port}`
"""
    readme_path = service_dir / "README.md"
    readme_path.write_text(readme, encoding="utf-8")
    (service_dir / "service-meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return readme


def _prepare_service_directory(
    cinema_dir: Path,
    stage_file: Path,
    service_id: str,
) -> tuple[Path, dict[str, Any]]:
    """Create service directory and copy HTML file."""
    service_dir = services_root(cinema_dir) / service_id
    service_dir.mkdir(parents=True, exist_ok=True)
    
    html = stage_file.read_text(encoding="utf-8")
    (service_dir / "index.html").write_text(html, encoding="utf-8")
    
    return service_dir, {}


def _generate_markpact_export(
    service_dir: Path,
    cinema_dir: Path,
    root: Path,
    capsule_name: str,
    stage: int,
    user_goal: str,
) -> None:
    """Generate and write the Markpact export file."""
    markpact_body = build_markpact_readme(
        cinema_dir,
        stage=stage,
        capsule_name=capsule_name,
        user_goal=user_goal,
        effective_ui=load_effective_ui_constraints(root, capsule_name, stage=stage),
    )
    (service_dir / "export-markpact.md").write_text(markpact_body, encoding="utf-8")


def _allocate_service_port(
    cinema_dir: Path,
    service_id: str,
) -> tuple[int, dict[str, Any]]:
    """Allocate a port for the service, reusing existing if available."""
    data = _load_registry(cinema_dir)
    services: list[dict[str, Any]] = list(data.get("services") or [])
    existing = next((s for s in services if s.get("id") == service_id), None)
    used_ports = {
        int(s["port"])
        for s in services
        if s.get("port") and s.get("id") != service_id
    }
    port = (
        int(existing["port"])
        if existing and existing.get("port")
        else (_pick_port(used_ports) or 0)
    )

    if not port:
        return 0, {"error": "no free port in range 9200–9298 for published services"}

    return port, {}


def _create_service_entry(
    service_id: str,
    capsule_name: str,
    project_id: str,
    project_title: str,
    stage: int,
    port: int,
) -> dict[str, Any]:
    """Create a new service registry entry."""
    return {
        "id": service_id,
        "title": project_title or capsule_name,
        "project_id": project_id or capsule_name,
        "capsule": capsule_name,
        "stage": stage,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "port": port,
        "url": f"http://127.0.0.1:{port}/",
        "status": "stopped",
        "pid": None,
        "readme_path": f"{SERVICES_DIR_NAME}/{service_id}/README.md",
        "markpact": True,
        "published": True,
    }


def _register_service(
    cinema_dir: Path,
    service_entry: dict[str, Any],
) -> None:
    """Register the service in the registry."""
    data = _load_registry(cinema_dir)
    services: list[dict[str, Any]] = list(data.get("services") or [])
    service_id = service_entry["id"]
    
    services = [s for s in services if s.get("id") != service_id]
    services.insert(0, service_entry)
    _save_registry(cinema_dir, {"services": services})


def _handle_existing_service(
    cinema_dir: Path,
    service_id: str,
) -> None:
    """Stop existing service if it's running."""
    data = _load_registry(cinema_dir)
    services: list[dict[str, Any]] = list(data.get("services") or [])
    existing = next((s for s in services if s.get("id") == service_id), None)
    
    if existing and existing.get("pid") and _service_alive(existing):
        stop_published_service(cinema_dir, service_id)


def publish_project_service(
    cinema_dir: Path,
    root: Path,
    capsule_name: str,
    *,
    stage: int = 0,
    project_id: str = "",
    project_title: str = "",
    user_goal: str = "",
    auto_start: bool = True,
) -> dict[str, Any]:
    """Package active stage HTML as a published service under cinema/services/."""
    stage_file = cinema_dir / f"stage{stage}.html"
    if not stage_file.exists():
        return {"error": f"missing {stage_file.name}"}

    service_id = _slug_service_id(project_id, capsule_name, stage)
    
    # Prepare service directory and files
    service_dir, prep_error = _prepare_service_directory(cinema_dir, stage_file, service_id)
    if prep_error:
        return prep_error
    
    _generate_markpact_export(service_dir, cinema_dir, root, capsule_name, stage, user_goal)
    
    # Allocate port
    port, port_error = _allocate_service_port(cinema_dir, service_id)
    if port_error:
        return port_error
    
    # Write service README
    effective = load_effective_ui_constraints(root, capsule_name, stage=stage)
    _write_service_readme(
        service_dir,
        cinema_dir=cinema_dir,
        stage=stage,
        capsule_name=capsule_name,
        user_goal=user_goal,
        effective_ui=effective,
        port=port,
    )

    # Handle existing service
    _handle_existing_service(cinema_dir, service_id)

    # Create and register service entry
    entry = _create_service_entry(
        service_id, capsule_name, project_id, project_title, stage, port
    )
    _register_service(cinema_dir, entry)

    result: dict[str, Any] = {
        "status": "published",
        "service": entry,
        "service_dir": str(service_dir.relative_to(cinema_dir)),
    }
    if auto_start:
        started = start_published_service(cinema_dir, service_id)
        result["start"] = started
        if started.get("service"):
            result["service"] = started["service"]
    return result


def start_published_service(cinema_dir: Path, service_id: str) -> dict[str, Any]:
    data = _load_registry(cinema_dir)
    services: list[dict[str, Any]] = list(data.get("services") or [])
    entry = next((s for s in services if s.get("id") == service_id), None)
    if entry is None:
        return {"error": f"unknown service: {service_id}"}

    entry = _refresh_service_status(entry)
    if entry.get("status") == "running":
        return {"status": "already_running", "service": entry}

    service_dir = services_root(cinema_dir) / service_id
    if not (service_dir / "index.html").exists():
        return {"error": f"missing service files for {service_id}"}

    port = int(entry.get("port") or 0)
    if not port:
        used = {int(s["port"]) for s in services if s.get("port")}
        port = _pick_port(used) or 0
    if not port:
        return {"error": "no free port for service"}

    log_path = service_dir / "service.log"
    log_file = open(log_path, "a", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port)],
        cwd=str(service_dir),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    log_file.close()

    entry["port"] = port
    entry["pid"] = proc.pid
    entry["url"] = f"http://127.0.0.1:{port}/"
    entry["status"] = "running"

    for idx, item in enumerate(services):
        if item.get("id") == service_id:
            services[idx] = entry
            break
    _save_registry(cinema_dir, {"services": services})

    refreshed = dict(entry)
    deadline = time.time() + 2.0
    while time.time() < deadline:
        refreshed = _refresh_service_status(dict(entry))
        if refreshed.get("status") == "running":
            break
        time.sleep(0.1)
    return {"status": "started", "service": refreshed}


def stop_published_service(cinema_dir: Path, service_id: str) -> dict[str, Any]:
    data = _load_registry(cinema_dir)
    services: list[dict[str, Any]] = list(data.get("services") or [])
    entry = next((s for s in services if s.get("id") == service_id), None)
    if entry is None:
        return {"error": f"unknown service: {service_id}"}

    pid = entry.get("pid")
    if pid:
        try:
            import os
            import signal

            os.kill(int(pid), signal.SIGTERM)
        except (ProcessLookupError, OSError, ValueError):
            pass

    entry["pid"] = None
    entry["status"] = "stopped"
    for idx, item in enumerate(services):
        if item.get("id") == service_id:
            services[idx] = entry
            break
    _save_registry(cinema_dir, {"services": services})
    return {"status": "stopped", "service": entry}
