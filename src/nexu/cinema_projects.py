"""Example project catalog and activation for Nexu."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .cinema_policy import (
    append_goal_ledger_entry,
    ensure_option_previews_from_stages,
    option_previews_are_distinct,
    refresh_cinema_policy_snapshot,
    reset_cinema_policy_ledger,
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
        source_paths=("examples/web_app_analytics/cinema",),
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


def _project_widgets(project: ExampleProject) -> dict[str, tuple[str, ...]]:
    widgets = {
        "calculator": (
            "sin",
            "cos",
            "tan",
            "log",
            "screen",
            "digits",
            "operators",
            "equals",
        ),
        "dashboard": (
            "kpi",
            "chart",
            "filter",
            "export",
            "users",
            "revenue",
            "growth",
            "alerts",
        ),
        "monitor": ("cpu", "memory", "latency", "logs", "trace", "alert", "ack", "retry"),
        "ecosystem": ("api", "auth", "db", "queue", "cache", "worker", "edge", "sync"),
        "api": ("GET", "POST", "PUT", "PATCH", "health", "metrics", "docs", "auth"),
        "mcp": ("tools", "schema", "call", "run", "ctx", "sync", "logs", "stop"),
        "frontend": ("view", "form", "nav", "modal", "toast", "list", "card", "button"),
        "slice": ("ui", "api", "test", "db", "job", "auth", "cache", "log"),
    }
    return {"items": widgets.get(project.kind, ("overview", "detail", "action", "status"))}


def _seed_html_for_project(project: ExampleProject, variant: str = "stage0") -> str:
    """Feature-complete starter UI for examples without dedicated cinema assets."""
    palette = {
        "web": ("#38bdf8", "#22c55e"),
        "data": ("#a78bfa", "#38bdf8"),
        "infra": ("#f97316", "#facc15"),
        "integration": ("#34d399", "#818cf8"),
    }
    accent, secondary = palette.get(project.domain, ("#38bdf8", "#22c55e"))
    widgets = _project_widgets(project)["items"]
    density = {"stage0": "overview", "stage1": "workflow", "stage2": "expanded"}.get(
        variant,
        "overview",
    )
    title_suffix = {"stage0": "S0", "stage1": "S1", "stage2": "S2"}.get(variant, "S0")
    metric_values = {
        "dashboard": ("$128.4k", "24.8%", "9.2k", "14"),
        "monitor": ("99.94%", "182 ms", "42", "3"),
        "ecosystem": ("12 svc", "4 queues", "98.2%", "7"),
        "api": ("2.1k rpm", "38 ms", "0.3%", "18"),
        "mcp": ("16 tools", "312 calls", "99.1%", "5"),
        "frontend": ("8 views", "24 comps", "3 alerts", "91%"),
        "slice": ("3 layers", "18 tests", "2 jobs", "0 drift"),
    }.get(project.kind, ("42", "18", "7", "OK"))
    kpi_cards = "".join(
        f"""
        <section
            class="kpi-card nexu-selectable"
            id="btn-{widgets[i % len(widgets)]}"
            data-nexu-target="{widgets[i % len(widgets)]}"
        >
            <span>{widgets[i % len(widgets)].title()}</span>
            <strong>{value}</strong>
            <small>{'+12%' if i % 2 == 0 else 'stable'}</small>
        </section>"""
        for i, value in enumerate(metric_values)
    )
    chart_bars = "".join(
        f'<span style="height:{h}%"></span>' for h in (45, 72, 58, 86, 64, 91, 76)
    )
    rows = "".join(
        f"""
        <tr>
            <td>{widgets[i % len(widgets)].title()}</td>
            <td>{'Healthy' if i != 2 else 'Review'}</td>
            <td>{'2m ago' if i == 0 else str(i + 4) + 'm ago'}</td>
        </tr>"""
        for i in range(4)
    )
    workflow_panel = (
        f"""
        <aside class="workflow-panel nexu-selectable" data-nexu-target="workflow-panel">
            <h2>{density.title()} flow</h2>
            <button id="btn-filter">Filter</button>
            <button id="btn-export">Export</button>
            <button id="btn-alerts">Alerts</button>
        </aside>"""
        if variant != "stage0"
        else ""
    )
    detail_panel = (
        f"""
        <section class="detail-panel nexu-selectable" data-nexu-target="detail-panel">
            <h2>Drilldown</h2>
            <div class="timeline"><span></span><span></span><span></span><span></span></div>
            <p>{project.subtitle}</p>
        </section>"""
        if variant == "stage2"
        else ""
    )
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>{project.title} ({title_suffix})</title>
    <link
        href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap"
        rel="stylesheet"
    >
    <style>
        * {{ box-sizing: border-box; }}
        html, body {{
            height: 100%; width: 100%; margin: 0; overflow: hidden;
            background: #0b1020; color: #f8fafc; font-family: 'Outfit', sans-serif;
        }}
        .app-shell {{
            height: 100%; width: 100%; padding: 18px;
            display: grid; grid-template-columns: 180px 1fr; gap: 14px;
            background:
                linear-gradient(135deg, rgba(56,189,248,0.10), transparent 45%),
                #0b1020;
        }}
        .sidebar {{
            border: 1px solid rgba(255,255,255,0.08); border-radius: 10px;
            background: rgba(15,23,42,0.86); padding: 14px;
            display: flex; flex-direction: column; gap: 10px;
        }}
        .brand {{ color: {accent}; font-size: 1rem; font-weight: 700; }}
        .nav-item {{
            background: rgba(255,255,255,0.04); border-radius: 8px; padding: 9px 10px;
            color: #cbd5e1; font-size: 0.78rem;
        }}
        .main {{
            min-width: 0; display: grid; grid-template-rows: auto auto 1fr; gap: 12px;
        }}
        .topbar {{
            display: flex; justify-content: space-between; gap: 12px; align-items: center;
        }}
        h1 {{ margin: 0; color: #f8fafc; font-size: clamp(18px, 2.5vh, 28px); }}
        .subtitle {{ margin: 3px 0 0; color: #94a3b8; font-size: 0.78rem; }}
        .status-pill {{
            background: rgba(34,197,94,0.14); color: #86efac;
            border: 1px solid rgba(34,197,94,0.3);
            padding: 7px 10px; border-radius: 999px; font-size: 0.74rem; font-weight: 700;
        }}
        .kpi-grid {{
            display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px;
        }}
        .kpi-card, .chart-card, .table-card, .workflow-panel, .detail-panel {{
            background: rgba(15,23,42,0.82); border: 1px solid rgba(255,255,255,0.08);
            border-radius: 10px; box-shadow: 0 12px 30px rgba(0,0,0,0.24);
        }}
        .kpi-card {{ padding: 12px; min-width: 0; }}
        .kpi-card span {{ display: block; color: #94a3b8; font-size: 0.7rem; }}
        .kpi-card strong {{ display: block; margin-top: 6px; font-size: 1.25rem; color: {accent}; }}
        .kpi-card small {{ color: {secondary}; font-size: 0.7rem; }}
        .content-grid {{
            min-height: 0;
            display: grid;
            grid-template-columns: minmax(0, 1.4fr) minmax(220px, 0.8fr);
            gap: 12px;
        }}
        .chart-card, .table-card, .detail-panel {{ padding: 14px; min-height: 0; }}
        .chart-card h2, .table-card h2, .workflow-panel h2, .detail-panel h2 {{
            margin: 0 0 10px; font-size: 0.9rem; color: #e2e8f0;
        }}
        .bar-chart {{
            height: 150px; display: flex; align-items: flex-end; gap: 9px;
            border-bottom: 1px solid rgba(255,255,255,0.12); padding-top: 18px;
        }}
        .bar-chart span {{
            flex: 1; border-radius: 8px 8px 0 0;
            background: linear-gradient(180deg, {accent}, {secondary});
            min-width: 8px;
        }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.75rem; }}
        td {{ padding: 8px 4px; border-bottom: 1px solid rgba(255,255,255,0.07); }}
        td:nth-child(2) {{ color: {secondary}; }}
        .workflow-panel {{ padding: 14px; display: flex; flex-direction: column; gap: 8px; }}
        .workflow-panel button {{
            border: 0; border-radius: 8px; padding: 8px 10px; color: #07111f;
            background: {accent}; font-weight: 700;
        }}
        .detail-panel {{ grid-column: 1 / -1; }}
        .timeline {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }}
        .timeline span {{ height: 8px; border-radius: 999px; background: {secondary}; }}
        @media (max-width: 720px) {{
            .app-shell {{ grid-template-columns: 1fr; padding: 12px; }}
            .sidebar {{ display: none; }}
            .kpi-grid, .content-grid {{ grid-template-columns: 1fr 1fr; }}
            .workflow-panel, .detail-panel {{ grid-column: 1 / -1; }}
        }}
    </style>
</head>
<body>
    <div class="app-shell" data-project="{project.id}" data-kind="{project.kind}">
        <nav class="sidebar">
            <div class="brand">{project.emoji} {project.title}</div>
            <div class="nav-item nexu-selectable" data-nexu-target="nav-overview">Overview</div>
            <div class="nav-item nexu-selectable" data-nexu-target="nav-workflows">Workflows</div>
            <div class="nav-item nexu-selectable" data-nexu-target="nav-reports">Reports</div>
            <div class="nav-item nexu-selectable" data-nexu-target="nav-settings">Settings</div>
        </nav>
        <main class="main">
            <header class="topbar">
                <div>
                    <h1>{project.title} ({title_suffix})</h1>
                    <p class="subtitle">{project.subtitle}</p>
                </div>
                <div class="status-pill">{density}</div>
            </header>
            <section class="kpi-grid">{kpi_cards}</section>
            <section class="content-grid">
                <section class="chart-card nexu-selectable" id="btn-chart" data-nexu-target="chart">
                    <h2>{widgets[1 % len(widgets)].title()} trend</h2>
                    <div class="bar-chart">{chart_bars}</div>
                </section>
                <section class="table-card nexu-selectable" id="btn-table" data-nexu-target="table">
                    <h2>{widgets[0].title()} activity</h2>
                    <table>{rows}</table>
                </section>
                {workflow_panel}
                {detail_panel}
            </section>
        </main>
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


def _write_seed_variants(cinema_dir: Path, project: ExampleProject) -> None:
    stages = {
        "stage0.html": _seed_html_for_project(project, "stage0"),
        "stage1.html": _seed_html_for_project(project, "stage1"),
        "stage2.html": _seed_html_for_project(project, "stage2"),
    }
    for filename, html in stages.items():
        (cinema_dir / filename).write_text(html, encoding="utf-8")
    (cinema_dir / "alt_a.html").write_text(stages["stage0.html"], encoding="utf-8")
    (cinema_dir / "alt_b.html").write_text(stages["stage1.html"], encoding="utf-8")
    (cinema_dir / "alt_c.html").write_text(stages["stage2.html"], encoding="utf-8")
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

    meta = {
        "id": project.id,
        "title": project.title,
        "domain": project.domain,
        "kind": project.kind,
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "source": "pending",
    }
    (cinema_dir / ACTIVE_PROJECT_FILE).write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    reset_cinema_policy_ledger(cinema_dir)
    if workspace_root is not None and capsule_name:
        refresh_cinema_policy_snapshot(cinema_dir, workspace_root, capsule_name)

    root = repo_root or find_nexu_repo_root(cinema_dir) or find_nexu_repo_root(workspace_root)
    source = _resolve_source_cinema(project, root)
    copied: list[str] = []

    if source is not None:
        copied = _copy_cinema_files(source, cinema_dir)
    if "stage0.html" not in copied:
        _write_seed_variants(cinema_dir, project)
        copied = [
            "stage0.html",
            "alt_a.html",
            "alt_b.html",
            "alt_c.html",
            "stage1.html",
            "stage2.html",
        ]

    write_cinema_inject_files(cinema_dir)

    from .cinema_scripts import repair_cinema_html_files

    repair_cinema_html_files(cinema_dir)

    if project.kind != "calculator":
        options_sync = ensure_option_previews_from_stages(cinema_dir)
    elif stage_files_are_distinct(cinema_dir) and not option_previews_are_distinct(
        cinema_dir
    ):
        options_sync = ensure_option_previews_from_stages(cinema_dir)
    else:
        options_sync = {
            "status": "options_preserved"
            if option_previews_are_distinct(cinema_dir)
            else "options_unchanged",
        }

    meta["source"] = str(source) if source else "seed"
    meta["activated_at"] = datetime.now(timezone.utc).isoformat()
    (cinema_dir / ACTIVE_PROJECT_FILE).write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    from .cinema_scope import scope_meta_for_project

    goal_bootstrap: dict[str, Any] = {"status": "skipped"}
    if workspace_root is not None and capsule_name and project.subtitle.strip():
        append_goal_ledger_entry(
            workspace_root,
            capsule_name,
            stage=0,
            goal=project.subtitle.strip(),
            project_context=f"{project.title} ({project.kind})",
            project_kind=project.kind,
            cinema_dir=cinema_dir,
        )
        refresh_cinema_policy_snapshot(cinema_dir, workspace_root, capsule_name)
        goal_bootstrap = {
            "status": "requires_llm",
            "options_written": [],
            "user_goal": project.subtitle.strip(),
            **scope_meta_for_project(project.kind),
        }

    return {
        "status": "project_activated",
        "project": project.to_public_dict(),
        "files_copied": copied,
        "options_sync": options_sync,
        "ledger_reset": True,
        "goal_bootstrap": goal_bootstrap,
        "scope": scope_meta_for_project(project.kind),
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
