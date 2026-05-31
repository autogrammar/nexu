"""Offline Cinema option previews when LLM network calls are disabled."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from string import Template

from .cinema_scripts import apply_spatial_deletes_to_html, finalize_cinema_html

_TRIGGERS = frozenset({"sin", "cos", "tan", "log", "ln"})


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


def _numpad_rows(cols: int = 4) -> str:
    op_style = "background:#e67e22;"
    rows = [
        ("7", "8", "9", "/"),
        ("4", "5", "6", "*"),
        ("1", "2", "3", "-"),
        ("0", ".", "=", "+"),
    ]
    parts: list[str] = []
    for row in rows:
        for token in row:
            cls = "btn-op" if token in "+-*/" else ("btn" if token != "=" else "btn")
            st = op_style if token in "+-*/" else ("background:#2ecc71;" if token == "=" else "")
            el_id = token.replace(".", "dot").replace("=", "eq")
            parts.append(_btn(token, el_id, extra_class=cls, style=st))
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


def _option_shell(
    *,
    title: str,
    accent: str,
    screen_text: str,
    grid_cols: int,
    body_buttons: str,
    bg: str = "#0f172a",
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
            background: {bg}; color: #fff; font-family: 'Outfit', sans-serif;
            display: flex; justify-content: center; align-items: center; user-select: none;
        }}
        .calc-body {{
            background: #1e293b; border-radius: 12px; padding: 12px;
            border: 1px solid rgba(255,255,255,0.1);
            width: 90%; height: 90%; max-width: 75vh; max-height: 115vw;
            aspect-ratio: 4/5; display: flex; flex-direction: column; box-sizing: border-box;
        }}
        .screen {{
            background: #0f172a; color: {accent}; font-size: calc(8px + 1.8vh);
            text-align: right; padding: 8px; border-radius: 6px; margin-bottom: 8px;
        }}
        .grid {{
            display: grid; grid-template-columns: repeat({grid_cols}, 1fr);
            grid-auto-rows: 1fr; gap: 6px; flex: 1;
        }}
        .btn {{
            background: rgba(255,255,255,0.05); color: #fff;
            font-size: calc(6px + 0.9vh); border-radius: 6px;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; user-select: none;
        }}
        .btn-sci {{ background: #38bdf8; color: #0f172a; font-weight: bold; }}
        .btn-op {{ background: #e67e22; color: #fff; font-weight: bold; }}
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


def build_policy_scientific_option_html(variant: str, keep_els: list[str]) -> str:
    """
    Build alt_a/b/c from Intract policy KEEP/DELETE (must-have controls in every variant).
    """
    keep_lower = _keep_ids_lower(keep_els)
    trig = _trig_row(keep_els)
    if variant == "a":
        body = trig + _numpad_rows(4)
        return _option_shell(
            title="Option A (minimal)",
            accent="#2ecc71",
            screen_text="12.5",
            grid_cols=4,
            body_buttons=body,
        )
    if variant == "b":
        body = trig + _numpad_rows(4)
        return _option_shell(
            title="Option B (standard)",
            accent="#38bdf8",
            screen_text="12.5",
            grid_cols=4,
            body_buttons=body,
        )
    extras = ""
    if "pi" in keep_lower:
        extras += _btn("π", "pi", extra_class="btn-sci-excess")
    if "exp" in keep_lower:
        extras += _btn("EXP", "EXP", extra_class="btn-sci-excess")
    body = trig + extras + _numpad_rows(5)
    return _option_shell(
        title="Option C (expanded)",
        accent="#a78bfa",
        screen_text="12.5",
        grid_cols=5,
        body_buttons=body,
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
    if use_chemical:
        mapping = [
            ("alt_a.html", "a", "Option A (chemical minimal)"),
            ("alt_b.html", "b", "Option B (chemical balanced)"),
            ("alt_c.html", "c", "Option C (chemical expanded)"),
        ]
    elif use_policy:
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
        elif use_policy:
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
    return labels
