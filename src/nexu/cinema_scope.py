"""Cinema scope orchestration; patch primitives live in repatch."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from repatch import (
    DASHBOARD_KINDS,
    IMPORTED_KINDS,
    SCOPE_STYLE_ID,
    VISUAL_REDESIGN_SCOPES,
    allowed_scope_ids,
    default_scope_for_kind,
    goal_requests_column_layout,
    inject_scope_style,
    normalize_focus_scope,
    offline_fast_scopes_for_kind,
    scope_supports_offline_fast_path,
    scoped_html_fragment,
    should_block_full_html_iterate,
    strip_scope_style,
    ui_type_for_kind,
)

__all__ = [
    "DASHBOARD_KINDS",
    "IMPORTED_KINDS",
    "SCOPE_STYLE_ID",
    "VISUAL_REDESIGN_SCOPES",
    "allowed_scope_ids",
    "can_use_offline_fast_iterate",
    "cinema_has_offline_baseline",
    "default_scope_for_kind",
    "inject_scope_style",
    "load_cinema_ui_profile",
    "normalize_focus_scope",
    "offline_fast_scopes_for_kind",
    "scope_meta_for_project",
    "scope_option_variants",
    "scope_supports_offline_fast_path",
    "scoped_html_fragment",
    "should_block_full_html_iterate",
    "strip_scope_style",
    "ui_type_for_kind",
]


def cinema_has_offline_baseline(cinema_dir: Path | str) -> bool:
    """True when stage HTML exists for scoped offline A–C patching."""
    stage0 = Path(cinema_dir) / "stage0.html"
    if not stage0.is_file():
        return False
    try:
        text = stage0.read_text(encoding="utf-8")
    except OSError:
        return False
    lowered = text.lower()
    return len(text.strip()) >= 120 and "<body" in lowered


def scope_option_variants(
    scope: str,
    ui_type: str,
    focus_text: str = "",
) -> list[tuple[str, str, str]]:
    """Return (alt_filename, human_label, llm_variant_note) for Options A–C."""
    kind = (
        "dashboard"
        if ui_type == "dashboard"
        else "calculator"
        if ui_type == "calculator"
        else "web"
    )
    scope = normalize_focus_scope(scope, kind)
    focus = focus_text or ""
    if scope == "colors":
        base = (
            "COLOR-ONLY evolution. Preserve information architecture, control set, "
            "labels, DOM ids, workflows, and orientation. Only change palette and emphasis. "
        )
        return [
            ("alt_a.html", "Option A (colors: cool)", base + "Cool restrained palette." + focus),
            (
                "alt_b.html",
                "Option B (colors: high contrast)",
                base + "Higher contrast operational palette." + focus,
            ),
            (
                "alt_c.html",
                "Option C (colors: expressive)",
                base + "More expressive but still readable palette." + focus,
            ),
        ]
    if scope == "shapes":
        base = (
            "SHAPE-ONLY evolution. Preserve functions, labels, data, navigation, "
            "orientation, and colors as much as possible. Change geometry and spacing only. "
        )
        return [
            ("alt_a.html", "Option A (shapes: compact)", base + "Compact rectangular geometry." + focus),
            ("alt_b.html", "Option B (shapes: balanced)", base + "Balanced card/control geometry." + focus),
            ("alt_c.html", "Option C (shapes: rounded)", base + "Softer rounded component geometry." + focus),
        ]
    if scope == "display":
        base = (
            "DISPLAY-ONLY evolution. Preserve workflows, control set, colors, and orientation. "
            "Change readout hierarchy, chart/table emphasis, and labels only. "
        )
        return [
            ("alt_a.html", "Option A (display: compact)", base + "Compact readouts." + focus),
            ("alt_b.html", "Option B (display: balanced)", base + "Balanced hierarchy." + focus),
            (
                "alt_c.html",
                "Option C (display: emphasized)",
                base + "Stronger primary readout emphasis." + focus,
            ),
        ]
    if scope == "orientation":
        base = (
            "ORIENTATION-ONLY evolution. Preserve functions, labels, data, colors, and all "
            "button ids/classes. Change layout direction and panel ordering only via CSS. "
            "Return a complete HTML5 document with head/body structure intact. "
        )
        if goal_requests_column_layout(focus):
            return [
                (
                    "alt_a.html",
                    "Option A (orientation: single column)",
                    base + "Single-column stacked content flow." + focus,
                ),
                (
                    "alt_b.html",
                    "Option B (orientation: two columns)",
                    base + "Explicit two-column content layout." + focus,
                ),
                (
                    "alt_c.html",
                    "Option C (orientation: responsive columns)",
                    base + "Responsive asymmetric column layout." + focus,
                ),
            ]
        return [
            (
                "alt_a.html",
                "Option A (orientation: vertical)",
                base + "More vertical stacked flow." + focus,
            ),
            (
                "alt_b.html",
                "Option B (orientation: horizontal)",
                base + "More horizontal workspace flow." + focus,
            ),
            (
                "alt_c.html",
                "Option C (orientation: adaptive)",
                base + "Adaptive arrangement for broader screens." + focus,
            ),
        ]
    if scope == "keypad" and ui_type == "calculator":
        base = (
            "KEYPAD evolution. Focus on control grouping, input keys, shortcuts, "
            "and keypad ergonomics. Preserve unrelated colors and orientation. "
        )
        return [
            ("alt_a.html", "Option A (keypad: compact)", base + "Compact input surface." + focus),
            ("alt_b.html", "Option B (keypad: grouped)", base + "Grouped controls by task." + focus),
            ("alt_c.html", "Option C (keypad: advanced)", base + "Expanded expert input surface." + focus),
        ]
    if ui_type == "dashboard":
        return [
            (
                "alt_a.html",
                "Option A (functions: overview)",
                "FUNCTION evolution: KPI overview, primary chart, compact activity." + focus,
            ),
            (
                "alt_b.html",
                "Option B (functions: workflow)",
                "FUNCTION evolution: filters, export, alerts, richer chart context." + focus,
            ),
            (
                "alt_c.html",
                "Option C (functions: analytics)",
                "FUNCTION evolution: drilldown timeline, cohort emphasis, more metrics." + focus,
            ),
        ]
    return [
        ("alt_a.html", "Option A (functions: minimal)", "FUNCTION evolution: essential controls only." + focus),
        ("alt_b.html", "Option B (functions: balanced)", "FUNCTION evolution: balanced complexity." + focus),
        ("alt_c.html", "Option C (functions: expanded)", "FUNCTION evolution: richer feature set." + focus),
    ]


def scope_meta_for_project(project_kind: str) -> dict[str, Any]:
    return {
        "default_focus_scope": default_scope_for_kind(project_kind),
        "allowed_focus_scopes": list(allowed_scope_ids(project_kind)),
    }


def load_cinema_ui_profile(
    active: dict[str, Any] | None,
    cinema_dir: Path | str,
) -> dict[str, Any]:
    """Resolve active project kind/title and UI type for Cinema server + offline paths."""
    project = active if isinstance(active, dict) else {}
    kind = str(project.get("kind") or "").lower()
    title = str(project.get("title") or project.get("id") or "").strip()
    html_hint = ""
    stage0 = Path(cinema_dir) / "stage0.html"
    if stage0.is_file():
        try:
            html_hint = stage0.read_text(encoding="utf-8")
        except OSError:
            html_hint = ""
    profile: dict[str, Any] = {
        "kind": kind,
        "title": title,
        "ui_type": ui_type_for_kind(kind, html_hint=html_hint),
        "active": project,
    }
    try:
        from .cinema_http_preprocess import (
            load_cinema_seed_preprocess_artifacts,
            load_http_preprocess_artifacts,
        )

        preprocess_ctx = load_http_preprocess_artifacts(cinema_dir, project)
        if not preprocess_ctx:
            preprocess_ctx = load_cinema_seed_preprocess_artifacts(cinema_dir, project)
        if preprocess_ctx:
            profile.update(preprocess_ctx)
    except Exception:
        pass
    return profile


def can_use_offline_fast_iterate(
    focus_scope: str,
    project_kind: str,
    cinema_dir: Path | str,
    *,
    force_llm: bool = False,
    fast_scope_options: bool = True,
) -> bool:
    """True when /iterate may skip LLM and use offline scope A–C generation."""
    if force_llm or not fast_scope_options:
        return False
    if not scope_supports_offline_fast_path(focus_scope, project_kind):
        return False
    return cinema_has_offline_baseline(cinema_dir)
