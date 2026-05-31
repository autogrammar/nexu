"""Offline Cinema option previews when LLM network calls are disabled."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from string import Template

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


def _hints_text(hints: list[str]) -> str:
    return " ".join(str(h).strip() for h in hints if str(h).strip()).lower()


def is_chemical_goal(hints: list[str]) -> bool:
    text = _hints_text(hints)
    return any(
        token in text
        for token in (
            "chem",
            "chemicz",
            "molar",
            "element",
            "formula",
            "periodic",
            "scientific",
            "naukow",
            "molow",
            "wzór",
            "wzor",
        )
    )


def _btn(label: str, el_id: str, *, extra_class: str = "", style: str = "") -> str:
    classes = "btn"
    if extra_class:
        classes += f" {extra_class}"
    style_attr = f' style="{style}"' if style else ""
    safe_id = el_id.replace(" ", "-")
    return f'<div class="{classes}" id="btn-{safe_id}"{style_attr}>{label}</div>'


def _keep_ids_lower(keep_els: list[str]) -> set[str]:
    return {str(k).strip().lower() for k in keep_els if str(k).strip()}


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
    for i, row in enumerate(_NUMPAD_LAYOUT):
        if max_rows is not None and i >= max_rows:
            break
        for token in row:
            el_id = _TOKEN_TO_ID.get(token, token)
            if el_id in keep_lower:
                parts.append(_numpad_token_btn(token))
    return "".join(parts) if parts else _numpad_rows(max_rows=max_rows)


def _policy_screen_text(variant: str, keep_els: list[str]) -> str:
    trig = _mandatory_trig(keep_els)
    prefix = {"a": "A", "b": "B", "c": "C"}.get(variant, variant.upper())
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
) -> str:
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
        <div class="screen" id="screen">{screen_text}</div>
        <div class="grid">
            {body_buttons}
        </div>
    </div>
</body>
</html>"""


def _cinema_is_calculator(cinema_dir: Path) -> bool:
    active = _active_project_meta(cinema_dir)
    if str(active.get("kind") or "").lower() == "calculator":
        return True
    path = cinema_dir / "stage0.html"
    if path.is_file() and "calc-body" in path.read_text(encoding="utf-8"):
        return True
    return False


def _has_stage0(cinema_dir: Path) -> bool:
    return (cinema_dir / "stage0.html").is_file()


def _active_project_meta(cinema_dir: Path) -> dict[str, str]:
    path = cinema_dir / "active_project.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items() if isinstance(v, str)}


def _project_option_label(meta: dict[str, str], variant: str) -> str:
    kind = meta.get("kind", "project").replace("_", " ")
    title = {
        "a": "Option A (project baseline)",
        "b": f"Option B ({kind} balanced)",
        "c": f"Option C ({kind} expanded)",
    }
    return title[variant]


def _write_project_options_from_stages(
    cinema_dir: Path,
    *,
    delete_els: list[str],
) -> list[str]:
    """Use active project's stage0/stage1/stage2 as default A-C proposals."""
    meta = _active_project_meta(cinema_dir)
    stage_map = [
        ("stage0.html", "alt_a.html", "a"),
        ("stage1.html", "alt_b.html", "b"),
        ("stage2.html", "alt_c.html", "c"),
    ]
    labels: list[str] = []
    for stage_name, alt_name, variant in stage_map:
        source = cinema_dir / stage_name
        if not source.exists():
            source = cinema_dir / "stage0.html"
        if not source.exists():
            return []
        out = finalize_cinema_html(source.read_text(encoding="utf-8"))
        if delete_els:
            out, _ = apply_spatial_deletes_to_html(out, delete_els)
            out = finalize_cinema_html(out)
        (cinema_dir / alt_name).write_text(out, encoding="utf-8")
        labels.append(_project_option_label(meta, variant))
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


def build_policy_scientific_option_html(variant: str, keep_els: list[str]) -> str:
    """
    Build alt_a/b/c from Intract policy KEEP/DELETE (must-have controls in every variant).
    """
    trig = _trig_row(keep_els)
    screen = _policy_screen_text(variant, keep_els)
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


def build_chemical_option_html(variant: str, keep_els: list[str]) -> str:
    """Return full HTML document for alt_a | alt_b | alt_c chemical variants."""
    if variant == "a":
        elems = ["H", "O", "C", "N", "S", "Cl", "Na", "K"]
        chem = "".join(_btn(e, e, extra_class="btn-chem") for e in elems)
        body = (
            chem
            + _btn("MW", "molar-mass", extra_class="btn-sci", style="grid-column: span 2;")
            + _btn("⌫", "clear", style="background:#e67e22;")
            + _numpad_rows()
        )
        return _chemical_shell(
            title="Option A: Chemical (minimal)",
            accent="#34d399",
            screen_text="H₂O → 18.02 g/mol",
            grid_cols=4,
            body_buttons=body,
        )
    if variant == "b":
        chem = "".join(
            _btn(e, e, extra_class="btn-chem")
            for e in ("H", "O", "C", "N", "Fe", "Cu", "Zn", "Ag")
        )
        body = _trig_row(keep_els) + chem + _numpad_rows()
        return _chemical_shell(
            title="Option B: Chemical (balanced)",
            accent="#38bdf8",
            screen_text="Formula: C₆H₁₂O₆ · tap element keys",
            grid_cols=4,
            body_buttons=body,
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
    return _chemical_shell(
        title="Option C: Chemical (expanded)",
        accent="#a78bfa",
        screen_text="Chemical & scientific · molar mass + formula",
        grid_cols=5,
        body_buttons=body,
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
) -> list[str]:
    """
    Write alt_a/b/c.html without LLM. Returns human labels for options written.
    """
    cinema_dir = Path(cinema_dir)
    keep = list(keep_els or [])
    delete = list(delete_els or [])
    hint_list = list(hints or [])
    labels: list[str] = []
    use_chemical = is_chemical_goal(hint_list)
    use_policy = _policy_constrained(keep, delete)
    use_calculator = _cinema_is_calculator(cinema_dir)
    use_project_stages = not use_calculator and not use_chemical and _has_stage0(cinema_dir)
    use_scientific = use_policy or (use_calculator and not use_chemical)
    if use_project_stages:
        labels = _write_project_options_from_stages(cinema_dir, delete_els=delete)
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
            html = build_chemical_option_html(variant, keep)
        elif use_scientific:
            html = build_policy_scientific_option_html(variant, keep)
        else:
            tmpl = f"alt_{variant}.html.tmpl"
            html = _render_packaged_alt(tmpl)
        out = finalize_cinema_html(html)
        if delete:
            out, _ = apply_spatial_deletes_to_html(out, delete)
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
