"""Deterministic Cinema option previews for scope-fast `/iterate` and tests.

When `/iterate` runs in goal_options mode with a visual focus_scope, the live
server calls write_goal_options_offline (plus cinema_scope.inject_scope_style)
instead of batch LLM HTML generation.
"""

from __future__ import annotations

from html import escape
from importlib.resources import files
from pathlib import Path
from string import Template

from .cinema_goal_contracts import goal_traits_from_contract_lines, is_chemical_goal
from .cinema_projects import load_active_project
from .cinema_scope import DASHBOARD_KINDS, ui_type_for_kind
from .cinema_scripts import apply_spatial_deletes_to_html, finalize_cinema_html

_TRIGGERS = frozenset({"sin", "cos", "tan", "log", "ln"})

_TOKEN_TO_ID: dict[str, str] = {
    "7": "7",
    "8": "8",
    "9": "9",
    "/": "div",
    "4": "4",
    "5": "5",
    "6": "6",
    "*": "mul",
    "1": "1",
    "2": "2",
    "3": "3",
    "-": "sub",
    "0": "0",
    ".": "dot",
    "=": "eq",
    "+": "add",
}

_NUMPAD_LAYOUT: tuple[tuple[str, ...], ...] = (
    ("7", "8", "9", "/"),
    ("4", "5", "6", "*"),
    ("1", "2", "3", "-"),
    ("0", ".", "=", "+"),
)


def _btn(label: str, el_id: str, *, extra_class: str = "", style: str = "") -> str:
    classes = "btn"
    if extra_class:
        classes += f" {extra_class}"
    style_attr = f' style="{style}"' if style else ""
    safe_id = el_id.replace(" ", "-")
    return f'<div class="{classes}" id="btn-{safe_id}"{style_attr}>{label}</div>'


def _keep_ids_lower(keep_els: list[str]) -> set[str]:
    return {_normal_id(k) for k in keep_els if _normal_id(k)}


def _normal_id(value: object) -> str:
    raw = str(value).strip()
    if not raw:
        return ""
    lower = raw.lower()
    if lower.startswith("btn-"):
        lower = lower[4:]
    if raw in _TOKEN_TO_ID:
        return _TOKEN_TO_ID[raw].lower()
    if lower in _TOKEN_TO_ID:
        return _TOKEN_TO_ID[lower].lower()
    return lower


def _delete_without_keeps(
    delete_els: list[str],
    keep_els: list[str],
) -> list[str]:
    """Current KEEP is stronger than old DELETE entries from the ledger."""
    kept = _keep_ids_lower(keep_els)
    return [d for d in delete_els if _normal_id(d) not in kept]


def _mandatory_trig(keep_els: list[str]) -> list[str]:
    """Policy KEEP for trig keys — must appear in every generated option."""
    kept = _keep_ids_lower(keep_els)
    return [t for t in ("sin", "cos", "tan", "log", "ln") if t in kept]


def _trig_row(keep_els: list[str]) -> str:
    mandatory = _mandatory_trig(keep_els)
    if mandatory:
        return "".join(_btn(t, t, extra_class="btn-sci") for t in mandatory)
    kept = [t for t in _TRIGGERS if t in _keep_ids_lower(keep_els)]
    if not kept:
        kept = ["sin", "cos", "tan", "log"]
    return "".join(_btn(t, t, extra_class="btn-sci") for t in kept)


def _policy_constrained(keep_els: list[str], delete_els: list[str]) -> bool:
    return bool(keep_els or delete_els)


def _numpad_token_btn(token: str) -> str:
    op_style = "background:#e67e22;"
    cls = "btn-op" if token in "+-*/" else "btn"
    st = op_style if token in "+-*/" else ("background:#2ecc71;" if token == "=" else "")
    el_id = _TOKEN_TO_ID.get(token, token.replace(".", "dot").replace("=", "eq"))
    return _btn(token, el_id, extra_class=cls, style=st)


def _numpad_rows(cols: int = 4, *, max_rows: int | None = None) -> str:
    del cols  # grid column count is chosen by shell, not here
    parts: list[str] = []
    for i, row in enumerate(_NUMPAD_LAYOUT):
        if max_rows is not None and i >= max_rows:
            break
        for token in row:
            parts.append(_numpad_token_btn(token))
    return "".join(parts)


def _numpad_from_policy(keep_els: list[str], *, max_rows: int | None = None) -> str:
    """Render only KEEP-marked numpad keys when the user marked enough of them."""
    keep_lower = _keep_ids_lower(keep_els)
    numpad_ids = {
        k
        for k in keep_lower
        if k.isdigit() or k in _TOKEN_TO_ID.values()
    }
    if len(numpad_ids) < 4:
        return _numpad_rows(max_rows=max_rows)
    parts: list[str] = []
    emitted: set[str] = set()

    def append_token(token: str) -> None:
        el_id = _TOKEN_TO_ID.get(token, token)
        if el_id not in keep_lower or el_id in emitted:
            return
        parts.append(_numpad_token_btn(token))
        emitted.add(el_id)

    for i, row in enumerate(_NUMPAD_LAYOUT):
        if max_rows is not None and i >= max_rows:
            continue
        for token in row:
            append_token(token)

    # Compact variants may limit visual rows, but KEEP-marked keys are mandatory.
    for row in _NUMPAD_LAYOUT:
        for token in row:
            append_token(token)
    return "".join(parts) if parts else _numpad_rows(max_rows=max_rows)


def _short_goal_label(goal: str, *, max_len: int = 42) -> str:
    compact = " ".join((goal or "").split())
    if len(compact) <= max_len:
        return compact
    return compact[: max_len - 1] + "…"


def _policy_screen_text(
    variant: str,
    keep_els: list[str],
    *,
    user_goal: str = "",
) -> str:
    trig = _mandatory_trig(keep_els)
    prefix = {"a": "A", "b": "B", "c": "C"}.get(variant, variant.upper())
    goal_note = _short_goal_label(user_goal) if user_goal else ""
    if goal_note and trig:
        return f"🎯 {goal_note} · {prefix} · {','.join(trig)}"
    if goal_note:
        return f"🎯 {goal_note} · {prefix}"
    if trig:
        return f"12.5 · {prefix} · {','.join(trig)}"
    return f"12.5 · {prefix}"


def _expanded_excess_row(keep_els: list[str]) -> str:
    keep_lower = _keep_ids_lower(keep_els)
    defaults = ("EXP", "Mod", "deg", "rad", "pi")
    if keep_lower:
        keys = [k for k in defaults if k.lower() in keep_lower or k in keep_lower]
        if not keys:
            keys = ["pi"]
    else:
        keys = list(defaults)
    parts: list[str] = []
    for key in keys:
        label = "π" if key == "pi" else key
        parts.append(_btn(label, key, extra_class="btn-sci-excess"))
    return "".join(parts)


def _chemical_shell(
    *,
    title: str,
    accent: str,
    screen_text: str,
    grid_cols: int,
    body_buttons: str,
    caption: str = "",
) -> str:
    caption_html = (
        f'<div class="calc-title" id="calc-title">{escape(caption)}</div>'
        if caption.strip()
        else ""
    )
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <link
        href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600&display=swap"
        rel="stylesheet"
    >
    <style>
        html, body {{
            height: 100%; width: 100%; margin: 0; overflow: hidden;
            background: #0a1628; color: #fff; font-family: 'Outfit', sans-serif;
            display: flex; justify-content: center; align-items: center; user-select: none;
        }}
        .calc-body {{
            background: #1e293b; border-radius: 12px; padding: 12px;
            border: 1px solid rgba(56, 189, 248, 0.25);
            width: 90%; height: 90%; max-width: 75vh; max-height: 115vw;
            aspect-ratio: 4/5; display: flex; flex-direction: column; box-sizing: border-box;
        }}
        .screen {{
            background: #0f172a; color: {accent}; font-size: calc(7px + 1.6vh);
            text-align: right; padding: 8px; border-radius: 6px; margin-bottom: 8px;
            min-height: 2.2em;
        }}
        .calc-title {{
            color: {accent}; font-size: calc(6px + 1vh); font-weight: 600;
            text-align: center; margin: 0 0 6px; line-height: 1.25;
        }}
        .grid {{
            display: grid; grid-template-columns: repeat({grid_cols}, 1fr);
            grid-auto-rows: 1fr; gap: 6px; flex: 1;
        }}
        .btn {{
            background: rgba(255,255,255,0.06); color: #fff;
            font-size: calc(6px + 0.85vh); border-radius: 6px;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; user-select: none;
        }}
        .btn-sci {{ background: #38bdf8; color: #0f172a; font-weight: bold; }}
        .btn-chem {{ background: #34d399; color: #064e3b; font-weight: bold; }}
        .btn-chem-heavy {{ background: #a78bfa; color: #1e1b4b; font-weight: bold; }}
        .btn-sci-excess {{ background: #818cf8; color: #fff; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="calc-body">
        {caption_html}
        <div class="screen" id="screen">{screen_text}</div>
        <div class="grid">
            {body_buttons}
        </div>
    </div>
</body>
</html>"""


def _active_project_meta(cinema_dir: Path) -> dict[str, str]:
    data = load_active_project(cinema_dir) or {}
    return {str(k): str(v) for k, v in data.items() if isinstance(v, str)}


def _active_is_imported(cinema_dir: Path) -> bool:
    active = load_active_project(cinema_dir) or {}
    kind = str(active.get("kind") or "").lower()
    if kind == "imported":
        return True
    project_id = str(active.get("id") or "")
    return project_id.startswith(("http-", "git-", "zip-"))


def _cinema_is_calculator(cinema_dir: Path) -> bool:
    active = load_active_project(cinema_dir) or {}
    kind = str(active.get("kind") or "").lower()
    if kind in DASHBOARD_KINDS or kind == "imported":
        return False
    project_id = str(active.get("id") or "")
    if project_id.startswith(("http-", "git-", "zip-")):
        return False
    if kind == "calculator":
        return True
    stage0 = cinema_dir / "stage0.html"
    html_hint = ""
    if stage0.is_file():
        try:
            html_hint = stage0.read_text(encoding="utf-8")
        except OSError:
            html_hint = ""
    if ui_type_for_kind(kind, html_hint=html_hint) == "calculator":
        return True
    lowered = html_hint.lower()
    return any(
        marker in lowered
        for marker in ("simple calc", "scientific calculator", "chemical calculator")
    )


def _project_option_label(meta: dict[str, str], variant: str) -> str:
    kind = meta.get("kind", "project").replace("_", " ")
    title = {
        "a": "Option A (project baseline)",
        "b": f"Option B ({kind} balanced)",
        "c": f"Option C ({kind} expanded)",
    }
    return title[variant]


def _inject_goal_banner(html: str, goal: str, variant: str) -> str:
    """Stamp visible goal context so offline iterations reflect the active project goal."""
    if not goal.strip():
        return html
    label = _short_goal_label(goal, max_len=120)
    import re

    banner = (
        f'<div class="nexu-goal-banner" data-variant="{variant}" '
        f'style="font-size:0.75rem;opacity:0.9;margin:0 0 8px;padding:6px 10px;'
        f'border-radius:6px;background:rgba(56,189,248,0.15);color:#7dd3fc;">'
        f"🎯 Goal · {label}</div>"
    )
    if "nexu-goal-banner" in html:
        return re.sub(
            r'<div class="nexu-goal-banner"[^>]*>.*?</div>',
            banner,
            html,
            count=1,
            flags=re.I | re.S,
        )
    body_match = re.search(r"<body[^>]*>", html, flags=re.I)
    if body_match:
        pos = body_match.end()
        return html[:pos] + banner + html[pos:]
    return banner + html


def _write_project_options_from_stages(
    cinema_dir: Path,
    *,
    delete_els: list[str],
    keep_els: list[str],
    user_goal: str = "",
    focus_scope: str = "",
) -> list[str]:
    """Use active project's stage0/stage1/stage2 as default A-C proposals."""
    from .cinema_scope import (
        inject_scope_style,
        normalize_focus_scope,
        scope_option_variants,
        ui_type_for_kind,
    )

    meta = _active_project_meta(cinema_dir)
    kind = str(meta.get("kind") or "").lower()
    scope = normalize_focus_scope(focus_scope, kind)
    stage0 = cinema_dir / "stage0.html"
    html_hint = ""
    if stage0.is_file():
        try:
            html_hint = stage0.read_text(encoding="utf-8")
        except OSError:
            html_hint = ""
    ui_type = ui_type_for_kind(kind, html_hint=html_hint)
    variant_specs = scope_option_variants(scope, ui_type)
    project_id = str(meta.get("id") or "")
    is_http = project_id.startswith("http-") or str(meta.get("import_kind") or "") == "http"
    if is_http:
        stage_map = [
            ("stage0.html", "a"),
            ("stage0.html", "b"),
            ("stage0.html", "c"),
        ]
    else:
        stage_map = [
            ("stage0.html", "a"),
            ("stage1.html", "b"),
            ("stage2.html", "c"),
        ]
    labels: list[str] = []
    for (alt_name, label, _note), (stage_name, variant) in zip(
        variant_specs, stage_map, strict=True
    ):
        source = cinema_dir / stage_name
        if not source.exists():
            source = cinema_dir / "stage0.html"
        if not source.exists():
            return []
        out = finalize_cinema_html(source.read_text(encoding="utf-8"))
        out = _inject_goal_banner(out, user_goal, variant)
        out = inject_scope_style(out, scope, variant, project_kind=kind)
        effective_delete = _delete_without_keeps(delete_els, keep_els)
        if effective_delete:
            out, _ = apply_spatial_deletes_to_html(out, effective_delete)
            out = finalize_cinema_html(out)
        (cinema_dir / alt_name).write_text(out, encoding="utf-8")
        labels.append(label)
    return labels


def _write_scoped_calculator_options(
    cinema_dir: Path,
    *,
    scope: str,
    delete_els: list[str],
    keep_els: list[str],
    user_goal: str = "",
    use_chemical: bool = False,
    use_scientific: bool = False,
) -> list[str]:
    """Scope-first offline A–C for calculator/chemical projects (colors, shapes, …)."""
    from .cinema_scope import inject_scope_style, scope_option_variants, ui_type_for_kind

    meta = _active_project_meta(cinema_dir)
    kind = str(meta.get("kind") or "calculator").lower()
    ui_type = ui_type_for_kind(kind)
    variant_specs = scope_option_variants(scope, ui_type)
    variant_keys = ("a", "b", "c")
    labels: list[str] = []
    for (alt_name, label, _note), variant in zip(variant_specs, variant_keys, strict=True):
        if use_chemical:
            html = build_chemical_option_html(variant, keep_els, user_goal=user_goal)
        elif use_scientific:
            html = build_policy_scientific_option_html(
                variant, keep_els, user_goal=user_goal
            )
        else:
            html = build_policy_scientific_option_html(
                variant, keep_els, user_goal=user_goal
            )
        out = finalize_cinema_html(html)
        out = inject_scope_style(out, scope, variant, project_kind="calculator")
        out = _inject_goal_banner(out, user_goal, variant)
        effective_delete = _delete_without_keeps(delete_els, keep_els)
        if effective_delete:
            out, _ = apply_spatial_deletes_to_html(out, effective_delete)
            out = finalize_cinema_html(out)
        (cinema_dir / alt_name).write_text(out, encoding="utf-8")
        labels.append(label)
    alt_b = cinema_dir / "alt_b.html"
    alt_c = cinema_dir / "alt_c.html"
    if labels and alt_b.is_file():
        (cinema_dir / "stage1.html").write_text(
            alt_b.read_text(encoding="utf-8"), encoding="utf-8"
        )
    if labels and alt_c.is_file():
        (cinema_dir / "stage2.html").write_text(
            alt_c.read_text(encoding="utf-8"), encoding="utf-8"
        )
    return labels


def _option_shell(
    *,
    title: str,
    accent: str,
    screen_text: str,
    grid_cols: int,
    body_buttons: str,
    skin: str = "standard",
    bg: str = "#0f172a",
) -> str:
    """skin: minimal | standard | expanded — strongly different layouts."""
    if skin == "minimal":
        body_css = (
            "max-width: 58vh; max-height: 100vw; aspect-ratio: 3/4; padding: 8px;"
            " border: 1px solid rgba(46, 204, 113, 0.35);"
        )
        screen_css = "font-size: calc(7px + 1.4vh); min-height: 2em;"
        grid_gap = "4px"
        btn_css = (
            "font-size: calc(5px + 0.75vh); border-radius: 4px;"
            " border: 1px solid rgba(255,255,255,0.08);"
        )
        sci_css = "background: #2ecc71; color: #0f172a;"
    elif skin == "expanded":
        body_css = (
            "max-width: 78vh; max-height: 118vw; aspect-ratio: 4/5; padding: 14px;"
            " border: 1px solid rgba(167, 139, 250, 0.45);"
        )
        screen_css = "font-size: calc(9px + 2vh); min-height: 2.4em;"
        grid_gap = "10px"
        btn_css = (
            "font-size: calc(5px + 0.8vh); border-radius: 50%;"
            " aspect-ratio: 1; min-height: 0;"
        )
        sci_css = "background: #38bdf8; color: #0f172a;"
    else:
        body_css = (
            "max-width: 72vh; max-height: 112vw; aspect-ratio: 4/5; padding: 14px;"
            " border: 1px solid rgba(56, 189, 248, 0.3);"
        )
        screen_css = "font-size: calc(10px + 2vh); min-height: 2.2em;"
        grid_gap = "8px"
        btn_css = (
            "font-size: calc(8px + 1.1vh); border-radius: 8px;"
            " border: 1px solid rgba(255,255,255,0.1); font-weight: 600;"
        )
        sci_css = "background: #38bdf8; color: #0f172a;"
    variant_label = skin.upper()[:1]
    badge = f'<span class="variant-badge">Variant {variant_label}</span>'
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <link
        href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600&display=swap"
        rel="stylesheet"
    >
    <style>
        html, body {{
            height: 100%; width: 100%; margin: 0; overflow: hidden;
            background: {bg}; color: #fff; font-family: 'Outfit', sans-serif;
            display: flex; justify-content: center; align-items: center; user-select: none;
        }}
        .calc-body {{
            background: #1e293b; border-radius: 12px; width: 90%; height: 90%;
            display: flex; flex-direction: column; box-sizing: border-box;
            {body_css}
        }}
        .screen {{
            background: #0f172a; color: {accent}; text-align: right;
            padding: 8px; border-radius: 6px; margin-bottom: 8px;
            {screen_css}
        }}
        .variant-badge {{
            display: block; font-size: 0.65em; opacity: 0.75; text-align: left;
            margin-bottom: 4px; letter-spacing: 0.05em;
        }}
        .grid {{
            display: grid; grid-template-columns: repeat({grid_cols}, 1fr);
            grid-auto-rows: 1fr; gap: {grid_gap}; flex: 1;
        }}
        .btn {{
            background: rgba(255,255,255,0.05); color: #fff;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; user-select: none;
            {btn_css}
        }}
        .btn-sci {{ {sci_css} font-weight: bold; }}
        .btn-op {{ background: #e67e22; color: #fff; font-weight: bold; }}
        .btn-sci-excess {{ background: #818cf8; color: #fff; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="calc-body" data-variant="{skin}">
        <div class="screen" id="screen">{badge}{screen_text}</div>
        <div class="grid">
            {body_buttons}
        </div>
    </div>
</body>
</html>"""


def build_policy_scientific_option_html(
    variant: str,
    keep_els: list[str],
    *,
    user_goal: str = "",
) -> str:
    """
    Build alt_a/b/c from Intract policy KEEP/DELETE (must-have controls in every variant).
    """
    trig = _trig_row(keep_els)
    screen = _policy_screen_text(variant, keep_els, user_goal=user_goal)
    if variant == "a":
        util = (
            _btn("x²", "pow2", extra_class="btn-sci")
            + _btn("√", "sqrt", extra_class="btn-sci")
            + _btn("C", "clear", extra_class="btn-op")
        )
        body = trig + util + _numpad_from_policy(keep_els, max_rows=3)
        return _option_shell(
            title="Option A (minimal)",
            accent="#2ecc71",
            screen_text=screen,
            grid_cols=3,
            body_buttons=body,
            skin="minimal",
        )
    if variant == "b":
        header = (
            _btn("C", "clear", extra_class="btn-op", style="grid-column: span 2;")
            + _btn("(", "lp", extra_class="btn-op")
            + _btn(")", "rp", extra_class="btn-op")
        )
        body = trig + header + _numpad_from_policy(keep_els)
        return _option_shell(
            title="Option B (standard)",
            accent="#38bdf8",
            screen_text=screen,
            grid_cols=4,
            body_buttons=body,
            skin="standard",
        )
    excess = _expanded_excess_row(keep_els)
    numpad_c = _numpad_from_policy(keep_els) + _btn("π", "pi", extra_class="btn-sci-excess")
    body = trig + excess + numpad_c
    return _option_shell(
        title="Option C (expanded)",
        accent="#a78bfa",
        screen_text=screen,
        grid_cols=5,
        body_buttons=body,
        skin="expanded",
        bg="#090d16",
    )


def build_chemical_option_html(
    variant: str,
    keep_els: list[str],
    *,
    user_goal: str = "",
) -> str:
    """Return full HTML document for alt_a | alt_b | alt_c chemical variants."""
    goal_line = _short_goal_label(user_goal) if user_goal else ""
    if variant == "a":
        elems = ["H", "O", "C", "N", "S", "Cl", "Na", "K"]
        chem = "".join(_btn(e, e, extra_class="btn-chem") for e in elems)
        mandatory_science = _trig_row(keep_els) if _mandatory_trig(keep_els) else ""
        body = (
            mandatory_science
            + chem
            + _btn("MW", "molar-mass", extra_class="btn-sci", style="grid-column: span 2;")
            + _btn("⌫", "clear", style="background:#e67e22;")
            + _numpad_rows()
        )
        screen = "H₂O → 18.02 g/mol"
        return _chemical_shell(
            title="Option A: Chemical (minimal)",
            accent="#34d399",
            screen_text=screen,
            grid_cols=4,
            body_buttons=body,
            caption=goal_line,
        )
    if variant == "b":
        chem = "".join(
            _btn(e, e, extra_class="btn-chem")
            for e in ("H", "O", "C", "N", "Fe", "Cu", "Zn", "Ag")
        )
        body = _trig_row(keep_els) + chem + _numpad_rows()
        screen = "Formula: C₆H₁₂O₆ · tap element keys"
        return _chemical_shell(
            title="Option B: Chemical (balanced)",
            accent="#38bdf8",
            screen_text=screen,
            grid_cols=4,
            body_buttons=body,
            caption=goal_line,
        )
    # variant c — expanded
    light = ["H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne"]
    heavy = ["Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca"]
    chem = "".join(_btn(e, e, extra_class="btn-chem") for e in light)
    chem += "".join(_btn(e, e, extra_class="btn-chem-heavy") for e in heavy)
    extra = _btn("MW", "molar-mass", extra_class="btn-sci")
    extra += _btn("π", "pi", extra_class="btn-sci")
    extra += _btn("EXP", "EXP", extra_class="btn-sci-excess")
    body = _trig_row(keep_els) + chem + extra + _numpad_rows()
    screen = "molar mass + formula"
    return _chemical_shell(
        title="Option C: Chemical (expanded)",
        accent="#a78bfa",
        screen_text=screen,
        grid_cols=5,
        body_buttons=body,
        caption=goal_line or "Chemical & scientific",
    )


def _render_packaged_alt(name: str) -> str:
    raw = files("nexu").joinpath("templates", "cinema", name).read_text(encoding="utf-8")
    from .cinema_scripts import CALCULATOR_RUNTIME_SCRIPT, SHIELD_SCRIPT

    return Template(raw).substitute(INJECTED_SCRIPTS=SHIELD_SCRIPT + CALCULATOR_RUNTIME_SCRIPT)


def write_goal_options_offline(
    cinema_dir: Path,
    *,
    keep_els: list[str] | None = None,
    delete_els: list[str] | None = None,
    hints: list[str] | None = None,
    user_goal: str = "",
    goal_contract_lines: list[str] | None = None,
    focus_scope: str = "",
) -> list[str]:
    """
    Write alt_a/b/c.html without LLM. Returns human labels for options written.
    """
    cinema_dir = Path(cinema_dir)
    keep = list(keep_els or [])
    delete = list(delete_els or [])
    hint_list = list(hints or [])
    goal_text = (user_goal or "").strip()
    traits = goal_traits_from_contract_lines(goal_contract_lines)
    chem_sources = ([goal_text] if goal_text else []) + hint_list
    use_chemical = traits.get("chemical") or is_chemical_goal(chem_sources)
    use_policy = _policy_constrained(keep, delete)
    use_calculator = _cinema_is_calculator(cinema_dir)
    active_kind = str(_active_project_meta(cinema_dir).get("kind") or "").lower()
    use_dashboard = traits.get("dashboard") or traits.get("api") or (
        not use_calculator
        and not use_chemical
        and active_kind
        in ("dashboard", "monitor", "ecosystem", "api", "frontend", "slice", "mcp", "imported")
    )
    use_project_stages = (
        (use_dashboard or active_kind == "imported" or (not use_calculator and not use_chemical))
        and (cinema_dir / "stage0.html").is_file()
    )
    use_scientific = (
        use_calculator or (use_policy and not _active_is_imported(cinema_dir))
    ) and not use_chemical
    raw_scope = (focus_scope or "").strip().lower()
    labels: list[str] = []
    if use_project_stages:
        labels = _write_project_options_from_stages(
            cinema_dir,
            delete_els=delete,
            keep_els=keep,
            user_goal=goal_text,
            focus_scope=focus_scope,
        )
        if labels:
            return labels
    if raw_scope and (use_calculator or use_chemical):
        from .cinema_scope import normalize_focus_scope

        scope = normalize_focus_scope(raw_scope, active_kind or "calculator")
        labels = _write_scoped_calculator_options(
            cinema_dir,
            scope=scope,
            delete_els=delete,
            keep_els=keep,
            user_goal=goal_text,
            use_chemical=use_chemical,
            use_scientific=use_scientific,
        )
        if labels:
            return labels
    if use_chemical:
        mapping = [
            ("alt_a.html", "a", "Option A (chemical minimal)"),
            ("alt_b.html", "b", "Option B (chemical balanced)"),
            ("alt_c.html", "c", "Option C (chemical expanded)"),
        ]
    elif use_scientific:
        mapping = [
            ("alt_a.html", "a", "Option A (minimal)"),
            ("alt_b.html", "b", "Option B (standard)"),
            ("alt_c.html", "c", "Option C (expanded)"),
        ]
    else:
        mapping = [
            ("alt_a.html", "a", "Option A (minimalist)"),
            ("alt_b.html", "b", "Option B (standard)"),
            ("alt_c.html", "c", "Option C (expanded)"),
        ]
    for filename, variant, label in mapping:
        if use_chemical:
            html = build_chemical_option_html(variant, keep, user_goal=goal_text)
        elif use_scientific:
            html = build_policy_scientific_option_html(
                variant, keep, user_goal=goal_text
            )
        else:
            tmpl = f"alt_{variant}.html.tmpl"
            html = _render_packaged_alt(tmpl)
        out = finalize_cinema_html(html)
        effective_delete = _delete_without_keeps(delete, keep)
        if effective_delete:
            out, _ = apply_spatial_deletes_to_html(out, effective_delete)
            out = finalize_cinema_html(out)
        (cinema_dir / filename).write_text(out, encoding="utf-8")
        labels.append(label)
    alt_b = cinema_dir / "alt_b.html"
    alt_c = cinema_dir / "alt_c.html"
    if labels and alt_b.is_file():
        (cinema_dir / "stage1.html").write_text(
            alt_b.read_text(encoding="utf-8"), encoding="utf-8"
        )
    if labels and alt_c.is_file():
        (cinema_dir / "stage2.html").write_text(
            alt_c.read_text(encoding="utf-8"), encoding="utf-8"
        )
    return labels
