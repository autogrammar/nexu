"""Scope contract helpers: per-project hashtag chips and offline option variants."""

from __future__ import annotations

import re
from typing import Any

DASHBOARD_KINDS = frozenset(
    {"dashboard", "monitor", "ecosystem", "api", "mcp", "frontend", "slice"}
)

SCOPE_STYLE_ID = "nexu-scope-variant"

# kind -> ordered scope ids shown in Cinema player
SCOPE_IDS_BY_KIND: dict[str, tuple[str, ...]] = {
    "dashboard": ("functions", "display", "colors", "shapes", "orientation"),
    "monitor": ("functions", "display", "colors", "shapes", "orientation"),
    "ecosystem": ("functions", "display", "colors", "shapes", "orientation"),
    "api": ("functions", "display", "colors", "shapes"),
    "mcp": ("functions", "display", "colors", "shapes"),
    "frontend": ("functions", "display", "colors", "shapes", "orientation"),
    "slice": ("functions", "display", "colors", "shapes"),
    "calculator": (
        "functions",
        "keypad",
        "display",
        "colors",
        "shapes",
        "orientation",
    ),
}

DEFAULT_SCOPE_BY_KIND: dict[str, str] = {
    "dashboard": "functions",
    "monitor": "functions",
    "ecosystem": "functions",
    "api": "functions",
    "calculator": "keypad",
}


def ui_type_for_kind(kind: str, *, html_hint: str = "") -> str:
    k = (kind or "").strip().lower()
    if k in DASHBOARD_KINDS:
        return "dashboard"
    if k == "calculator":
        return "calculator"
    text = (html_hint or "").lower()
    if "calc-body" in text or "btn-eq" in text:
        return "calculator"
    if "app-shell" in text or "kpi-card" in text or "kpi-grid" in text:
        return "dashboard"
    return "web"


def allowed_scope_ids(project_kind: str) -> tuple[str, ...]:
    k = (project_kind or "").strip().lower()
    return SCOPE_IDS_BY_KIND.get(k, SCOPE_IDS_BY_KIND["calculator"])


def default_scope_for_kind(project_kind: str) -> str:
    k = (project_kind or "").strip().lower()
    ids = allowed_scope_ids(k)
    return DEFAULT_SCOPE_BY_KIND.get(k, ids[0] if ids else "functions")


def normalize_focus_scope(scope: str, project_kind: str) -> str:
    allowed = set(allowed_scope_ids(project_kind))
    s = (scope or "").strip().lower()
    if s in allowed:
        return s
    return default_scope_for_kind(project_kind)


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
            "ORIENTATION-ONLY evolution. Preserve functions, labels, data, and colors. "
            "Change layout direction and panel ordering only. "
        )
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


def strip_scope_style(html: str) -> str:
    if not html:
        return html
    return re.sub(
        rf'<style\s+id="{SCOPE_STYLE_ID}"[^>]*>[\s\S]*?</style>\s*',
        "",
        html,
        flags=re.I,
    )


def _scope_css(scope: str, variant: str) -> str:
    """Dashboard/web-safe CSS patches for offline scope previews."""
    v = variant if variant in ("a", "b", "c") else "b"
    if scope == "colors":
        palettes = {
            "a": (
                ".app-shell,.dashboard-shell{background:#0b1224!important;}"
                ".kpi-card strong,.brand{color:#38bdf8!important;}"
                ".status-pill{background:rgba(56,189,248,0.18)!important;}"
            ),
            "b": (
                ".app-shell,.dashboard-shell{background:#020617!important;}"
                ".kpi-card,.chart-card,.table-card{border-color:rgba(248,250,252,0.35)!important;}"
                "h1,h2,.kpi-card strong{color:#f8fafc!important;}"
            ),
            "c": (
                ".app-shell,.dashboard-shell{background:#1e1033!important;}"
                ".kpi-card strong,.bar-chart span{background:linear-gradient(180deg,#a78bfa,#f472b6)!important;}"
                ".brand{color:#e879f9!important;}"
            ),
        }
        return palettes[v]
    if scope == "shapes":
        radii = {
            "a": (
                ".kpi-card,.chart-card,.table-card,.nav-item,button,[role='button']"
                "{border-radius:4px!important;}"
            ),
            "b": (
                ".kpi-card,.chart-card,.table-card,.nav-item,button,[role='button']"
                "{border-radius:10px!important;}"
            ),
            "c": (
                ".kpi-card,.chart-card,.table-card,.nav-item,button,[role='button']"
                "{border-radius:999px!important;}"
            ),
        }
        return radii[v]
    if scope == "display":
        scales = {
            "a": ".kpi-card strong{font-size:1rem!important;}.chart-card h2{font-size:0.8rem!important;}",
            "b": ".kpi-card strong{font-size:1.25rem!important;}.chart-card{min-height:140px!important;}",
            "c": (
                ".kpi-card strong{font-size:1.45rem!important;}"
                ".chart-card h2{font-size:1rem!important;}.bar-chart{height:180px!important;}"
            ),
        }
        return scales[v]
    if scope == "orientation":
        layouts = {
            "a": ".content-grid{grid-template-columns:1fr!important;}",
            "b": ".content-grid{grid-template-columns:minmax(0,1.6fr) minmax(200px,0.7fr)!important;}",
            "c": ".app-shell{grid-template-columns:140px 1fr!important;}.kpi-grid{grid-template-columns:repeat(2,1fr)!important;}",
        }
        return layouts[v]
    return ""


def _calc_scope_css(scope: str, variant: str) -> str:
    """Palette / layout overrides for calculator HTML (.calc-body, .screen, .btn-*)."""
    v = variant if variant in ("a", "b", "c") else "a"
    if scope == "colors":
        palettes = {
            "a": (
                "html,body{background:#0a1628!important;color:#e2e8f0!important;}"
                ".calc-body{background:#1e293b!important;border-color:#38bdf8!important;}"
                ".calc-title,.screen{color:#38bdf8!important;}"
                ".screen{background:#0f172a!important;}"
                ".btn{background:rgba(255,255,255,0.08)!important;color:#fff!important;}"
                ".btn-sci{background:#38bdf8!important;color:#0f172a!important;}"
                ".btn-chem{background:#34d399!important;color:#064e3b!important;}"
                ".btn-chem-heavy{background:#a78bfa!important;color:#1e1b4b!important;}"
                "[style*='e67e22']{background:#0ea5e9!important;}"
                "[style*='2ecc71']{background:#22c55e!important;}"
            ),
            "b": (
                "html,body{background:#000!important;color:#fff!important;}"
                ".calc-body{background:#111!important;border:2px solid #facc15!important;}"
                ".calc-title,.screen{color:#facc15!important;}"
                ".screen{background:#1a1a1a!important;}"
                ".btn{background:#262626!important;color:#fff!important;border:1px solid #525252!important;}"
                ".btn-sci{background:#facc15!important;color:#000!important;}"
                ".btn-chem{background:#fff!important;color:#000!important;}"
                ".btn-chem-heavy{background:#d4d4d4!important;color:#000!important;}"
                "[style*='e67e22']{background:#f97316!important;color:#000!important;}"
                "[style*='2ecc71']{background:#22c55e!important;color:#000!important;}"
            ),
            "c": (
                "html,body{background:linear-gradient(160deg,#1e1b4b,#831843)!important;color:#fce7f3!important;}"
                ".calc-body{background:rgba(30,27,75,0.85)!important;border-color:#f472b6!important;}"
                ".calc-title,.screen{color:#f9a8d4!important;}"
                ".screen{background:rgba(15,23,42,0.6)!important;}"
                ".btn{background:rgba(244,114,182,0.25)!important;color:#fff!important;}"
                ".btn-sci{background:#c084fc!important;color:#1e1b4b!important;}"
                ".btn-chem{background:#fb7185!important;color:#500724!important;}"
                ".btn-chem-heavy{background:#e879f9!important;color:#4a044e!important;}"
                "[style*='e67e22']{background:#f472b6!important;}"
                "[style*='2ecc71']{background:#a3e635!important;color:#14532d!important;}"
            ),
        }
        return palettes[v]
    if scope == "shapes":
        radii = {
            "a": ".calc-body{border-radius:8px!important;}.btn,.btn-sci,.btn-chem{border-radius:4px!important;}",
            "b": ".calc-body{border-radius:12px!important;}.btn,.btn-sci,.btn-chem{border-radius:8px!important;}",
            "c": ".calc-body{border-radius:20px!important;}.btn,.btn-sci,.btn-chem{border-radius:50%!important;}",
        }
        return radii[v]
    if scope == "display":
        sizes = {
            "a": ".screen{font-size:calc(6px + 1.2vh)!important;min-height:1.8em!important;}",
            "b": ".screen{font-size:calc(7px + 1.6vh)!important;min-height:2.2em!important;}",
            "c": ".screen{font-size:calc(9px + 2vh)!important;min-height:2.8em!important;font-weight:700!important;}",
        }
        return sizes[v]
    if scope == "orientation":
        layouts = {
            "a": ".calc-body{aspect-ratio:3/5!important;max-width:70vh!important;}",
            "b": ".calc-body{aspect-ratio:4/5!important;max-width:75vh!important;}",
            "c": ".calc-body{aspect-ratio:5/4!important;max-width:95vw!important;max-height:80vh!important;}",
        }
        return layouts[v]
    if scope == "keypad":
        gaps = {
            "a": ".grid{gap:4px!important;grid-template-columns:repeat(3,1fr)!important;}",
            "b": ".grid{gap:6px!important;grid-template-columns:repeat(4,1fr)!important;}",
            "c": ".grid{gap:8px!important;grid-template-columns:repeat(5,1fr)!important;}",
        }
        return gaps[v]
    return ""


def inject_scope_style(html: str, scope: str, variant: str, *, project_kind: str = "") -> str:
    inferred = project_kind or (
        "calculator"
        if "calc-body" in html.lower()
        else ("dashboard" if "kpi-grid" in html.lower() else "web")
    )
    scope = normalize_focus_scope(scope, inferred)
    css = (
        _calc_scope_css(scope, variant)
        if inferred == "calculator" or "calc-body" in html.lower()
        else _scope_css(scope, variant)
    )
    cleaned = strip_scope_style(html)
    if not css:
        return cleaned
    block = f'<style id="{SCOPE_STYLE_ID}">\n{css}\n</style>'
    lower = cleaned.lower()
    if "</head>" in lower:
        idx = lower.rfind("</head>")
        return cleaned[:idx] + block + cleaned[idx:]
    if "<body" in lower:
        match = re.search(r"<body[^>]*>", cleaned, flags=re.I)
        if match:
            pos = match.start()
            return cleaned[:pos] + block + cleaned[pos:]
    return block + cleaned


def scope_meta_for_project(project_kind: str) -> dict[str, Any]:
    return {
        "default_focus_scope": default_scope_for_kind(project_kind),
        "allowed_focus_scopes": list(allowed_scope_ids(project_kind)),
    }
