"""Scope contract helpers: per-project hashtag chips and offline option variants."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

DASHBOARD_KINDS = frozenset(
    {"dashboard", "monitor", "ecosystem", "api", "mcp", "frontend", "slice"}
)

SCOPE_STYLE_ID = "nexu-scope-variant"

# kind -> ordered scope ids shown in Cinema player
IMPORTED_KINDS = frozenset({"imported", "web"})

SCOPE_IDS_BY_KIND: dict[str, tuple[str, ...]] = {
    "imported": ("functions", "display", "colors", "shapes", "orientation"),
    "web": ("functions", "display", "colors", "shapes", "orientation"),
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
    "imported": "functions",
    "web": "functions",
    "calculator": "keypad",
}

# Visual scopes handled by cinema_offline_options + inject_scope_style (~10–50ms).
OFFLINE_FAST_SCOPES_CALCULATOR = frozenset(
    {"colors", "shapes", "display", "orientation", "keypad"}
)
OFFLINE_FAST_SCOPES_DASHBOARD = frozenset(
    {"colors", "shapes", "display", "orientation"}
)

# Visual scopes where DELETE marks mean restyle (not DOM removal).
VISUAL_REDESIGN_SCOPES = frozenset(
    {"colors", "shapes", "display", "orientation", "keypad"}
)

# Project kinds that must not receive full-page LLM regeneration when marks exist.
MARKED_PATCH_KINDS = frozenset(
    IMPORTED_KINDS
    | DASHBOARD_KINDS
    | frozenset({"web", "frontend"})
)


def ui_type_for_kind(kind: str, *, html_hint: str = "") -> str:
    k = (kind or "").strip().lower()
    if k in IMPORTED_KINDS:
        return "web"
    if k in DASHBOARD_KINDS:
        return "dashboard"
    if k == "calculator":
        return "calculator"
    text = re.sub(r"<script\b[^>]*>[\s\S]*?</script>", "", html_hint or "", flags=re.I).lower()
    if "calc-body" in text or "btn-eq" in text:
        return "calculator"
    if "app-shell" in text or "kpi-card" in text or "kpi-grid" in text:
        return "dashboard"
    return "web"


def allowed_scope_ids(project_kind: str) -> tuple[str, ...]:
    k = (project_kind or "").strip().lower()
    return SCOPE_IDS_BY_KIND.get(k, SCOPE_IDS_BY_KIND["web"])


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


def offline_fast_scopes_for_kind(project_kind: str) -> frozenset[str]:
    """Scopes that may use the offline A–C path on /iterate (not functions)."""
    k = (project_kind or "").strip().lower()
    if k in DASHBOARD_KINDS or k in IMPORTED_KINDS:
        return OFFLINE_FAST_SCOPES_DASHBOARD
    if k == "calculator":
        return OFFLINE_FAST_SCOPES_CALCULATOR
    return OFFLINE_FAST_SCOPES_DASHBOARD


def scope_supports_offline_fast_path(scope: str, project_kind: str) -> bool:
    """True when focus_scope can be patched locally without a full LLM HTML call."""
    normalized = normalize_focus_scope(scope, project_kind)
    return normalized in offline_fast_scopes_for_kind(project_kind)


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


def _web_scope_css(scope: str, variant: str) -> str:
    """Generic palette / layout patches for imported or arbitrary web HTML."""
    v = variant if variant in ("a", "b", "c") else "b"
    if scope == "colors":
        palettes = {
            "a": (
                "html,body{background:#0b1224!important;color:#e2e8f0!important;}"
                "a,button,[role='button']{color:#38bdf8!important;}"
                "h1,h2,h3,header,.brand{color:#38bdf8!important;}"
            ),
            "b": (
                "html,body{background:#020617!important;color:#f8fafc!important;}"
                "a,button,[role='button']{color:#facc15!important;}"
                "h1,h2,h3,header{border-color:rgba(248,250,252,0.35)!important;}"
            ),
            "c": (
                "html,body{background:linear-gradient(160deg,#1e1033,#312e81)!important;color:#fce7f3!important;}"
                "a,button,[role='button']{color:#e879f9!important;}"
                "h1,h2,h3,header{color:#f9a8d4!important;}"
            ),
        }
        return palettes[v]
    if scope == "shapes":
        radii = {
            "a": "button,[role='button'],input,select,textarea,section,article,nav,header,footer"
            "{border-radius:4px!important;}",
            "b": "button,[role='button'],input,select,textarea,section,article,nav,header,footer"
            "{border-radius:10px!important;}",
            "c": "button,[role='button'],input,select,textarea,section,article,nav,header,footer"
            "{border-radius:999px!important;}",
        }
        return radii[v]
    if scope == "display":
        scales = {
            "a": "h1{font-size:1.35rem!important;}h2{font-size:1rem!important;}p{font-size:0.9rem!important;}",
            "b": "h1{font-size:1.65rem!important;}h2{font-size:1.15rem!important;}p{font-size:1rem!important;}",
            "c": "h1{font-size:1.9rem!important;font-weight:700!important;}h2{font-size:1.25rem!important;}",
        }
        return scales[v]
    if scope == "orientation":
        layouts = {
            "a": "body{display:flex!important;flex-direction:column!important;gap:12px!important;}",
            "b": "body{display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;gap:16px!important;}",
            "c": "main,section{display:grid!important;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))!important;gap:14px!important;}",
        }
        return layouts[v]
    return ""


def _resolve_scope_kind(project_kind: str, html: str) -> str:
    kind = (project_kind or "").strip().lower()
    if kind in IMPORTED_KINDS or kind in DASHBOARD_KINDS or kind == "calculator":
        return kind
    lowered = (html or "").lower()
    if "calc-body" in lowered or "btn-eq" in lowered:
        return "calculator"
    if "kpi-grid" in lowered or "app-shell" in lowered:
        return "dashboard"
    return "web"


def should_block_full_html_iterate(
    project_kind: str,
    keep_els: list[str] | None,
    delete_els: list[str] | None,
    *,
    focus_scope: str = "",
) -> bool:
    """True when marks exist on imported/web/dashboard projects — force patch paths only."""
    from .cinema_marked_context import has_ui_marks

    if not has_ui_marks(keep_els, delete_els):
        return False
    kind = (project_kind or "").strip().lower()
    return kind in MARKED_PATCH_KINDS


def _bind_annotations_to_html(
    html: str,
    keep_ids: list[str] | None,
    delete_ids: list[str] | None,
) -> str:
    from .cinema_marked_context import (
        _TAG_OPEN_RE,
        _parse_attrs,
        _id_candidates,
        _logical_id,
    )

    keep = [str(x).strip() for x in (keep_ids or []) if str(x).strip()]
    delete = [str(x).strip() for x in (delete_ids or []) if str(x).strip()]
    marked_ids = keep + [x for x in delete if x not in keep]
    if not marked_ids:
        return html

    wanted = set(marked_ids)
    text = str(html or "")
    
    matches = list(_TAG_OPEN_RE.finditer(text))
    matched_ranges: list[tuple[int, int, str]] = []
    seen_elements = set()
    
    for match in matches:
        tag = match.group(1).lower()
        if tag in ("html", "head", "body", "style", "script", "link", "meta"):
            continue
        attrs_text = match.group(2)
        attrs = _parse_attrs(attrs_text)
        
        raw_id = str(attrs.get("id") or "").strip()
        candidates = _id_candidates(raw_id) if raw_id else set()
        target = str(attrs.get("data-nexu-target") or "").strip()
        if target:
            candidates |= _id_candidates(target)
        logical = _logical_id(tag, attrs)
        if logical:
            candidates |= _id_candidates(logical)
            
        hit = wanted & candidates
        if not hit and tag not in ("html", "head", "body", "style", "script", "link", "meta"):
            if raw_id or target:
                continue
            inner_start = match.end()
            inner_end = text.lower().find(f"</{tag}>", inner_start)
            if inner_end >= 0:
                inner_content = text[inner_start:inner_end]
                label = re.sub(r"<[^>]+>", "", inner_content)
                label = re.sub(r"\s+", " ", label).strip()
                logical = _logical_id(tag, attrs, text=label)
                if logical:
                    hit = wanted & _id_candidates(logical)
                    
        if not hit:
            continue
            
        matched_id = list(hit)[0]
        if matched_id in seen_elements:
            continue
        seen_elements.add(matched_id)
        
        if "data-nexu-target" in attrs:
            continue
            
        new_tag = f"<{tag} data-nexu-target=\"{matched_id}\" {attrs_text}>"
        matched_ranges.append((match.start(), match.end(), new_tag))
        
    if not matched_ranges:
        return html
        
    parts: list[str] = []
    last_idx = 0
    for start, end, replacement in matched_ranges:
        parts.append(text[last_idx:start])
        parts.append(replacement)
        last_idx = end
    parts.append(text[last_idx:])
    return "".join(parts)


def _get_scope_css(inferred: str, html: str, scope: str, variant: str) -> str:
    if inferred == "calculator" or (
        inferred not in IMPORTED_KINDS.union(DASHBOARD_KINDS) and "calc-body" in html.lower()
    ):
        return _calc_scope_css(scope, variant)
    if inferred in DASHBOARD_KINDS or "kpi-grid" in html.lower():
        return _scope_css(scope, variant)
    return _web_scope_css(scope, variant) or _scope_css(scope, variant)


def _inject_css_block(html: str, css: str) -> str:
    if not css:
        return html
    block = f'<style id="{SCOPE_STYLE_ID}">\n{css}\n</style>'
    lower = html.lower()
    if "</head>" in lower:
        idx = lower.rfind("</head>")
        return html[:idx] + block + html[idx:]
    if "<body" in lower:
        match = re.search(r"<body[^>]*>", html, flags=re.I)
        if match:
            pos = match.start()
            return html[:pos] + block + html[pos:]
    return block + html


def inject_scope_style(
    html: str,
    scope: str,
    variant: str,
    *,
    project_kind: str = "",
    delete_ids: list[str] | None = None,
    keep_ids: list[str] | None = None,
) -> str:
    html = _bind_annotations_to_html(html, keep_ids, delete_ids)
    inferred = _resolve_scope_kind(project_kind, html)
    scope = normalize_focus_scope(scope, inferred)
    delete_list = [str(x).strip() for x in (delete_ids or []) if str(x).strip()]
    keep_list = [str(x).strip() for x in (keep_ids or []) if str(x).strip()]
    if scope in VISUAL_REDESIGN_SCOPES and keep_list and not delete_list:
        return strip_scope_style(html)
    css = _get_scope_css(inferred, html, scope, variant)
    cleaned = strip_scope_style(html)
    if scope in VISUAL_REDESIGN_SCOPES and delete_list:
        from .cinema_marked_context import (
            marked_scope_colors_css,
            resolve_marked_selectors,
            restrict_scope_css_to_marks,
        )

        selectors = resolve_marked_selectors(cleaned, delete_list)
        if scope == "colors" and selectors:
            css = marked_scope_colors_css(selectors, variant)
        else:
            css = restrict_scope_css_to_marks(css, delete_list, html=cleaned)
    return _inject_css_block(cleaned, css)


def scoped_html_fragment(html: str, focus_scope: str, project_kind: str) -> str | None:
    """Smaller HTML slice for scoped LLM prompts when the scope is visual-only."""
    if not scope_supports_offline_fast_path(focus_scope, project_kind):
        return None
    text = str(html or "")
    scope = normalize_focus_scope(focus_scope, project_kind)
    patterns = (
        r'(<div[^>]*class=[\'"][^\'"]*calc-body[^\'"]*[\'"][\s\S]*?</div>\s*</div>)',
        r'(<div[^>]*class=[\'"][^\'"]*app-shell[^\'"]*[\'"][\s\S]*?</div>\s*</div>)',
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match and len(match.group(1)) >= 40:
            return (
                f"<!-- scoped DOM fragment for #{scope}; regenerate full page from baseline -->\n"
                + match.group(1)
            )
    return None


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
