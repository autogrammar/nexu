"""Example project catalog and activation for Nexu."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .cinema_policy import (
    ensure_option_previews_from_stages,
    enforce_deletes_on_option_previews,
    load_effective_ui_constraints,
    option_previews_are_distinct,
    stage_files_are_distinct,
)
from .cinema_scripts import write_cinema_inject_files

ACTIVE_PROJECT_FILE = "active_project.json"


@dataclass(frozen=True)
class ExampleProject:
    id: str
    title: str
    subtitle: str
    domain: str
    kind: str
    tags: tuple[str, ...]
    emoji: str
    source_paths: tuple[str, ...]

    def to_public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["tags"] = list(self.tags)
        data["source_paths"] = list(self.source_paths)
        return data


def find_nexu_repo_root(start: Path | None = None) -> Path | None:
    """Walk parents from cinema/workspace until examples/ exists."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "examples").is_dir() and (candidate / "src" / "nexu").is_dir():
            return candidate
    return None


EXAMPLE_PROJECTS: tuple[ExampleProject, ...] = (
    ExampleProject(
        id="web_app_calculator",
        title="Scientific Calculator",
        subtitle="Chemical & scientific keypad evolution",
        domain="web",
        kind="calculator",
        tags=("scientific", "chemistry", "featured"),
        emoji="🧪",
        source_paths=(
            "examples/web_app_calculator/cinema",
            "examples/web_app_calculator/workspace/.nexu/capsules/scientific_calc/cinema",
        ),
    ),
    ExampleProject(
        id="web_app_dashboard",
        title="Operations Dashboard",
        subtitle="KPI cards, charts, and filters",
        domain="web",
        kind="dashboard",
        tags=("metrics", "charts"),
        emoji="📊",
        source_paths=("examples/web_app_dashboard/cinema",),
    ),
    ExampleProject(
        id="web_app_analytics",
        title="Analytics Workspace",
        subtitle="Funnels, cohorts, and experiment flags",
        domain="data",
        kind="dashboard",
        tags=("analytics", "experiments"),
        emoji="📈",
        source_paths=(),
    ),
    ExampleProject(
        id="web_app_event_monitor",
        title="Event Monitor",
        subtitle="Live stream health and alert tiles",
        domain="data",
        kind="monitor",
        tags=("realtime", "alerts"),
        emoji="📡",
        source_paths=(),
    ),
    ExampleProject(
        id="web_app_pactown_ecosystem",
        title="Pactown Ecosystem",
        subtitle="Multi-service Markpact topology map",
        domain="integration",
        kind="ecosystem",
        tags=("markpact", "microservices"),
        emoji="🌐",
        source_paths=(),
    ),
    ExampleProject(
        id="frontend_view",
        title="Frontend Module",
        subtitle="Isolated UI capsule slice",
        domain="web",
        kind="frontend",
        tags=("component", "isolation"),
        emoji="🖼️",
        source_paths=(),
    ),
    ExampleProject(
        id="backend_service",
        title="Backend Service",
        subtitle="API routes and contract surface",
        domain="infra",
        kind="api",
        tags=("rest", "contracts"),
        emoji="⚙️",
        source_paths=(),
    ),
    ExampleProject(
        id="vertical_slice",
        title="Vertical Slice",
        subtitle="UI + API + tests in one capsule",
        domain="integration",
        kind="slice",
        tags=("fullstack", "demo"),
        emoji="🧩",
        source_paths=(),
    ),
    ExampleProject(
        id="mcp_service",
        title="MCP Service",
        subtitle="Tool server and capability grid",
        domain="integration",
        kind="mcp",
        tags=("agents", "tools"),
        emoji="🔌",
        source_paths=(),
    ),
)


def list_project_catalog() -> dict[str, Any]:
    domains = sorted({p.domain for p in EXAMPLE_PROJECTS})
    kinds = sorted({p.kind for p in EXAMPLE_PROJECTS})
    return {
        "projects": [p.to_public_dict() for p in EXAMPLE_PROJECTS],
        "filters": {
            "domains": domains,
            "kinds": kinds,
            "tags": sorted({tag for p in EXAMPLE_PROJECTS for tag in p.tags}),
        },
    }


def _resolve_source_cinema(project: ExampleProject, repo_root: Path | None) -> Path | None:
    if repo_root is None:
        return None
    for rel in project.source_paths:
        candidate = repo_root / rel
        if candidate.is_dir() and (candidate / "stage0.html").exists():
            return candidate
    return None


def _seed_html_for_project(project: ExampleProject) -> str:
    """Minimal starter UI when no example cinema folder exists."""
    accent = {
        "web": "#38bdf8",
        "data": "#a78bfa",
        "infra": "#f97316",
        "integration": "#34d399",
    }.get(project.domain, "#38bdf8")
    buttons = {
        "calculator": ("sin", "cos", "7", "8", "9", "div", "4", "5", "6", "mul"),
        "dashboard": ("kpi", "chart", "filter", "export", "users", "revenue", "growth", "alerts"),
        "monitor": ("cpu", "mem", "logs", "trace", "alert", "mute", "ack", "retry"),
        "ecosystem": ("api", "auth", "db", "queue", "cache", "worker", "edge", "sync"),
        "api": ("GET", "POST", "PUT", "PATCH", "health", "metrics", "docs", "auth"),
        "mcp": ("tool", "list", "call", "schema", "run", "stop", "ctx", "sync"),
        "frontend": ("view", "form", "nav", "modal", "toast", "list", "card", "btn"),
        "slice": ("ui", "api", "test", "db", "job", "auth", "cache", "log"),
    }.get(project.kind, ("a", "b", "c", "d", "e", "f", "g", "h"))
    btn_html = "".join(
        f'<div class="btn" id="btn-{label}">{label}</div>' for label in buttons[:12]
    )
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>{project.title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600&display=swap" rel="stylesheet">
    <style>
        html, body {{
            height: 100%; width: 100%; margin: 0; overflow: hidden;
            background: #0f172a; color: #fff; font-family: 'Outfit', sans-serif;
            display: flex; justify-content: center; align-items: center;
        }}
        .calc-body {{
            background: #1e293b; border-radius: 12px; padding: 14px;
            width: 90%; height: 90%; max-width: 70vh; aspect-ratio: 4/5;
            display: flex; flex-direction: column; box-sizing: border-box;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .screen {{
            background: #0f172a; color: {accent}; font-size: calc(10px + 1.5vh);
            text-align: right; padding: 10px; border-radius: 8px; margin-bottom: 10px;
        }}
        .grid {{
            display: grid; grid-template-columns: repeat(4, 1fr);
            grid-auto-rows: 1fr; gap: 8px; flex: 1;
        }}
        .btn {{
            background: rgba(255,255,255,0.06); border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: calc(8px + 0.9vh); cursor: pointer; user-select: none;
        }}
    </style>
</head>
<body>
    <div class="calc-body">
        <div class="screen" id="screen">{project.title}</div>
        <div class="grid">{btn_html}</div>
    </div>
</body>
</html>"""


def _copy_cinema_files(source: Path, cinema_dir: Path) -> list[str]:
    copied: list[str] = []
    for name in (
        "stage0.html",
        "stage1.html",
        "stage2.html",
        "alt_a.html",
        "alt_b.html",
        "alt_c.html",
    ):
        src = source / name
        dst = cinema_dir / name
        if src.exists():
            if src.resolve() == dst.resolve():
                copied.append(name)
                continue
            shutil.copy2(src, dst)
            copied.append(name)
    return copied


def _write_seed_variants(cinema_dir: Path, stage_html: str) -> None:
    (cinema_dir / "stage0.html").write_text(stage_html, encoding="utf-8")
    titles = {
        "alt_a.html": "Option A (minimal)",
        "alt_b.html": "Option B (balanced)",
        "alt_c.html": "Option C (expanded)",
    }
    for filename, title in titles.items():
        html = stage_html
        if "<title>" in html:
            import re

            html = re.sub(
                r"<title>.*?</title>",
                f"<title>{title}</title>",
                html,
                count=1,
                flags=re.I | re.S,
            )
        (cinema_dir / filename).write_text(html, encoding="utf-8")
    (cinema_dir / "stage1.html").write_text(
        (cinema_dir / "alt_b.html").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (cinema_dir / "stage2.html").write_text(
        (cinema_dir / "alt_c.html").read_text(encoding="utf-8"), encoding="utf-8"
    )


def activate_example_project(
    cinema_dir: Path,
    project_id: str,
    *,
    repo_root: Path | None = None,
    capsule_name: str | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    """Load example UI into the live cinema directory (no browser reload)."""
    project = next((p for p in EXAMPLE_PROJECTS if p.id == project_id), None)
    if project is None:
        return {"error": f"unknown project: {project_id}"}

    root = repo_root or find_nexu_repo_root(cinema_dir) or find_nexu_repo_root(workspace_root)
    source = _resolve_source_cinema(project, root)
    copied: list[str] = []

    if source is not None:
        copied = _copy_cinema_files(source, cinema_dir)
    if "stage0.html" not in copied:
        _write_seed_variants(cinema_dir, _seed_html_for_project(project))
        copied = ["stage0.html", "alt_a.html", "alt_b.html", "alt_c.html", "stage1.html", "stage2.html"]

    write_cinema_inject_files(cinema_dir)

    if not option_previews_are_distinct(cinema_dir) and stage_files_are_distinct(
        cinema_dir
    ):
        options_sync = ensure_option_previews_from_stages(cinema_dir)
    else:
        options_sync = {
            "status": "options_preserved"
            if option_previews_are_distinct(cinema_dir)
            else "options_unchanged",
        }

    if workspace_root is not None and capsule_name:
        effective = load_effective_ui_constraints(
            workspace_root, capsule_name, stage=0
        )
        to_delete = list(effective.get("delete") or [])
        if to_delete:
            options_sync = {
                **options_sync,
                "policy_patch": enforce_deletes_on_option_previews(
                    cinema_dir, to_delete
                ),
            }

    meta = {
        "id": project.id,
        "title": project.title,
        "domain": project.domain,
        "kind": project.kind,
        "activated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "source": str(source) if source else "seed",
    }
    (cinema_dir / ACTIVE_PROJECT_FILE).write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return {
        "status": "project_activated",
        "project": project.to_public_dict(),
        "files_copied": copied,
        "options_sync": options_sync,
    }


def load_active_project(cinema_dir: Path) -> dict[str, Any] | None:
    path = cinema_dir / ACTIVE_PROJECT_FILE
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None
