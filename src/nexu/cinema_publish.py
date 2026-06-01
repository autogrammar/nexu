"""Publish Nexu workspace stages as runnable Markpact services."""

from __future__ import annotations

import json
import os
import re
import shutil
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
_SERVICE_ID_RE = re.compile(r"^[a-zA-Z0-9._-]+$")
_IMPORTED_SOURCE_PREFIX_RE = re.compile(
    r"imported_projects/([a-zA-Z0-9._-]+)/source/",
    re.IGNORECASE,
)
_LOCAL_SERVICE_URL_RE = re.compile(r"^https?://(?:127\.0\.0\.1|localhost):\d+/?", re.I)


def _service_url_mode() -> str:
    return os.environ.get("NEXU_SERVICE_URL_MODE", "path").strip().lower() or "path"


def _public_service_url(service_id: str) -> str:
    """Return the externally openable URL for a published service."""
    domain = os.environ.get("NEXU_SERVICE_DOMAIN", "").strip().strip(".")
    scheme = os.environ.get("NEXU_SERVICE_SCHEME", "https").strip() or "https"
    if _service_url_mode() == "subdomain" and domain:
        return f"{scheme}://{service_id}.{domain}/"
    return f"/services/view/{service_id}/"


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
        url = entry.get("local_url") or f"http://127.0.0.1:{port}/"
        return _http_ok(url)
    return False


def _refresh_service_status(entry: dict[str, Any]) -> dict[str, Any]:
    service_id = str(entry.get("id") or "").strip()
    if service_id:
        public_url = _public_service_url(service_id)
        if not entry.get("public_url"):
            entry["public_url"] = public_url
        if not entry.get("url") or _LOCAL_SERVICE_URL_RE.match(str(entry.get("url"))):
            entry["url"] = public_url
    if entry.get("port") and not entry.get("local_url"):
        entry["local_url"] = f"http://127.0.0.1:{int(entry['port'])}/"
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
    public_url: str,
    baseline_contracts: dict[str, Any] | None = None,
) -> str:
    html = (service_dir / "index.html").read_text(encoding="utf-8")
    title_match = re.search(r"<title[^>]*>([^<]*)</title>", html, flags=re.I)
    app_title = (
        title_match.group(1).strip() if title_match else None
    ) or f"{capsule_name} S{stage}"
    goal_line = user_goal.strip() or "(none recorded)"
    baselines = baseline_contracts or {}
    meta = {
        "published_at": datetime.now(timezone.utc).isoformat(),
        "capsule": capsule_name,
        "stage": stage,
        "port": port,
        "public_url": public_url,
        "local_url": f"http://127.0.0.1:{port}/",
        "user_goal": goal_line,
        "policy_keep": list(effective_ui.get("keep") or []),
        "policy_delete": list(effective_ui.get("delete") or []),
        "baseline_contracts": {
            "project": list(baselines.get("project") or []),
            "capsule": list(baselines.get("capsule") or []),
        },
    }
    baseline_lines = [
        str(item.get("line") or item.get("id") or item)
        for item in meta["baseline_contracts"]["project"]
        + meta["baseline_contracts"]["capsule"]
    ]
    baseline_block = "\n".join(f"- `{line}`" for line in baseline_lines) or "- (none)"
    html_body = _escape_markdown_fence(html)
    readme = f"""# {app_title} — published Nexu service

Runnable **Markpact** service published from Nexu (stage {stage}).

## Run

```bash markpact:run
python -m http.server {port}
```

Open **{public_url}** from the Nexu Services tab. Local process URL: **http://127.0.0.1:{port}/**.

## Intract baseline model

Keep these contracts attached to future edits. They describe the intended app model and prevent
goal-driven changes from regressing the baseline UI/functionality:

{baseline_block}

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


def _imported_project_ids_in_html(html: str) -> set[str]:
    return set(_IMPORTED_SOURCE_PREFIX_RE.findall(html))


def _bundle_imported_source_assets(
    cinema_dir: Path,
    service_dir: Path,
    html: str,
) -> tuple[str, list[str]]:
    """Copy imported project source trees and rewrite cinema-local asset URLs."""
    copied: list[str] = []
    rewritten = html
    for project_id in sorted(_imported_project_ids_in_html(html)):
        source_root = cinema_dir / "imported_projects" / project_id / "source"
        if not source_root.is_dir():
            continue
        prefix = f"imported_projects/{project_id}/source/"
        for src_file in sorted(source_root.rglob("*")):
            if not src_file.is_file():
                continue
            rel = src_file.relative_to(source_root)
            dest_rel = f"source/{rel.as_posix()}"
            dest = service_dir / dest_rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest)
            copied.append(dest_rel)
        rewritten = rewritten.replace(prefix, "source/")
    return rewritten, copied


def _prepare_service_directory(
    cinema_dir: Path,
    stage_file: Path,
    service_id: str,
) -> tuple[Path, list[str]]:
    """Create service directory with stage HTML and any linked local assets."""
    service_dir = services_root(cinema_dir) / service_id
    service_dir.mkdir(parents=True, exist_ok=True)

    html = stage_file.read_text(encoding="utf-8")
    html, copied_assets = _bundle_imported_source_assets(cinema_dir, service_dir, html)
    (service_dir / "index.html").write_text(html, encoding="utf-8")

    return service_dir, copied_assets


def _generate_markpact_export(
    service_dir: Path,
    cinema_dir: Path,
    root: Path,
    capsule_name: str,
    stage: int,
    user_goal: str,
) -> None:
    """Generate and write the Markpact export file."""
    from .cinema import build_intract_policy_snapshot

    snapshot = build_intract_policy_snapshot(root, capsule_name)
    markpact_body = build_markpact_readme(
        cinema_dir,
        stage=stage,
        capsule_name=capsule_name,
        user_goal=user_goal,
        effective_ui=load_effective_ui_constraints(root, capsule_name, stage=stage),
        baseline_contracts=snapshot.get("baseline_contracts", {}),
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
    public_url = _public_service_url(service_id)
    return {
        "id": service_id,
        "title": project_title or capsule_name,
        "project_id": project_id or capsule_name,
        "capsule": capsule_name,
        "stage": stage,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "port": port,
        "url": public_url,
        "public_url": public_url,
        "local_url": f"http://127.0.0.1:{port}/",
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
    service_dir, copied_assets = _prepare_service_directory(cinema_dir, stage_file, service_id)
    
    from .cinema import build_intract_policy_snapshot

    snapshot = build_intract_policy_snapshot(root, capsule_name)
    baseline_contracts = snapshot.get("baseline_contracts", {})
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
        public_url=_public_service_url(service_id),
        baseline_contracts=baseline_contracts,
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
        "copied_assets": copied_assets,
    }
    if auto_start:
        started = start_published_service(cinema_dir, service_id)
        result["start"] = started
        if started.get("service"):
            result["service"] = started["service"]
    return result


def _spawn_http_server(service_dir: Path, port: int) -> subprocess.Popen:
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
    return proc


def _wait_for_service_running(entry: dict[str, Any], deadline: float) -> dict[str, Any]:
    refreshed = dict(entry)
    while time.time() < deadline:
        refreshed = _refresh_service_status(dict(entry))
        if refreshed.get("status") == "running":
            break
        time.sleep(0.1)
    return refreshed


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

    proc = _spawn_http_server(service_dir, port)

    entry["port"] = port
    entry["pid"] = proc.pid
    entry["local_url"] = f"http://127.0.0.1:{port}/"
    entry["public_url"] = _public_service_url(service_id)
    entry["url"] = entry["public_url"]
    entry["status"] = "running"

    for idx, item in enumerate(services):
        if item.get("id") == service_id:
            services[idx] = entry
            break
    _save_registry(cinema_dir, {"services": services})

    deadline = time.time() + 2.0
    refreshed = _wait_for_service_running(entry, deadline)
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


def _validate_service_id(service_id: str) -> str | None:
    sid = (service_id or "").strip()
    if not sid or not _SERVICE_ID_RE.fullmatch(sid):
        return "invalid service_id"
    return None


def delete_published_service(cinema_dir: Path, service_id: str) -> dict[str, Any]:
    """Stop, unregister, and remove files for a published service."""
    sid_err = _validate_service_id(service_id)
    if sid_err:
        return {"error": sid_err}

    data = _load_registry(cinema_dir)
    services: list[dict[str, Any]] = list(data.get("services") or [])
    entry = next((s for s in services if s.get("id") == service_id), None)
    if entry is None:
        return {"error": f"unknown service: {service_id}"}

    if entry.get("status") == "running" or entry.get("pid"):
        stop_published_service(cinema_dir, service_id)

    services = [s for s in services if s.get("id") != service_id]
    _save_registry(cinema_dir, {"services": services})

    service_dir = services_root(cinema_dir) / service_id
    if service_dir.exists():
        shutil.rmtree(service_dir)

    return {"status": "deleted", "id": service_id}


def delete_published_services_for_project(
    cinema_dir: Path,
    project_id: str,
) -> dict[str, Any]:
    """Remove all published services linked to a project id."""
    normalized = (project_id or "").strip()
    if not normalized:
        return {"deleted": [], "count": 0}

    data = _load_registry(cinema_dir)
    matching = [
        s
        for s in data.get("services") or []
        if str(s.get("project_id") or "") == normalized
    ]
    deleted: list[str] = []
    errors: list[dict[str, str]] = []
    for entry in matching:
        sid = str(entry.get("id") or "")
        if not sid:
            continue
        result = delete_published_service(cinema_dir, sid)
        if result.get("error"):
            errors.append({"id": sid, "error": str(result["error"])})
        else:
            deleted.append(sid)
    out: dict[str, Any] = {"deleted": deleted, "count": len(deleted)}
    if errors:
        out["errors"] = errors
    return out
