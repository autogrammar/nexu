"""Local DOM/function patches for fast Cinema A-C option generation."""

from __future__ import annotations

import html
import re
from typing import Any

from .cinema_html_validate import prepare_cinema_html_document
from .cinema_project_ir import build_project_ir, summarize_project_ir

_ALT_FILES = ("alt_a.html", "alt_b.html", "alt_c.html")
_FUNCTION_PATCH_STYLE_ID = "nexu-function-patch"


def supports_function_patch(scope: str, project_kind: str) -> bool:
    """True when #functions can be generated as local DOM patches."""
    normalized = (scope or "").strip().lower()
    kind = (project_kind or "").strip().lower()
    return normalized == "functions" and kind in {
        "imported",
        "web",
        "frontend",
        "dashboard",
        "slice",
    }


def build_function_patch_context(html_text: str, *, user_goal: str = "") -> str:
    ir = build_project_ir(html_text)
    goal = user_goal.strip() or "(none)"
    return "FUNCTION PATCH IR\n" + summarize_project_ir(ir) + "\nuser_goal: " + goal


def _strip_existing_patch(text: str) -> str:
    out = re.sub(
        rf'<style\s+id=["\']{_FUNCTION_PATCH_STYLE_ID}["\'][^>]*>[\s\S]*?</style>\s*',
        "",
        str(text or ""),
        flags=re.I,
    )
    out = re.sub(
        r'<section\s+class=["\']nexu-function-evolution\b[^>]*>[\s\S]*?</section>\s*',
        "",
        out,
        flags=re.I,
    )
    return out


def _goal_label(user_goal: str) -> str:
    label = re.sub(r"\s+", " ", user_goal or "").strip()
    return label[:120] if label else "doprecyzowana ścieżka użytkownika"


def _variant_section(variant: str, user_goal: str, ir: dict[str, Any]) -> str:
    goal = html.escape(_goal_label(user_goal))
    title = html.escape(str(ir.get("title") or "Projekt"))
    specs = {
        "a": (
            "Szybka ścieżka",
            "Jeden widoczny następny krok dla odbiorcy.",
            ("Cel", "Oferta", "Kontakt"),
        ),
        "b": (
            "Workflow konwersji",
            "Sekwencja: odkrycie wartości, wybór działania, kontakt.",
            ("Poznaj", "Wybierz", "Zarezerwuj"),
        ),
        "c": (
            "Rozszerzony funnel",
            "Dodatkowe wejścia dla segmentów, social proof i mocniejsze CTA.",
            ("Start", "Galeria", "Opinie", "Rezerwacja"),
        ),
    }
    heading, lead, chips = specs.get(variant, specs["b"])
    chip_html = "".join(f"<span>{html.escape(chip)}</span>" for chip in chips)
    return f"""
<section
  class="nexu-function-evolution nexu-function-{variant}"
  data-nexu-function-variant="{variant}"
>
  <div>
    <small>{html.escape(title)}</small>
    <h2>{html.escape(heading)}</h2>
    <p>{html.escape(lead)} Cel iteracji: {goal}.</p>
  </div>
  <div class="nexu-function-actions">{chip_html}</div>
</section>
"""


def _patch_style() -> str:
    return f"""<style id="{_FUNCTION_PATCH_STYLE_ID}">
.nexu-function-evolution {{
  margin: 24px auto;
  width: min(920px, calc(100% - 48px));
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) auto;
  gap: 16px;
  align-items: center;
  padding: 18px 20px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
}}
.nexu-function-evolution small {{
  display: block;
  margin-bottom: 4px;
  color: #64748b;
  font-size: 0.78rem;
}}
.nexu-function-evolution h2 {{
  margin: 0 0 6px;
  color: #0f172a;
  font-size: clamp(1.25rem, 2.4vw, 1.8rem);
}}
.nexu-function-evolution p {{
  margin: 0;
  color: #334155;
  line-height: 1.45;
}}
.nexu-function-actions {{
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}}
.nexu-function-actions span {{
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 7px 11px;
  border-radius: 999px;
  background: #0f172a;
  color: #f8fafc;
  font-weight: 700;
  font-size: 0.82rem;
}}
@media (max-width: 720px) {{
  .nexu-function-evolution {{ grid-template-columns: 1fr; width: min(100% - 24px, 920px); }}
  .nexu-function-actions {{ justify-content: flex-start; }}
}}
</style>
"""


def _inject_into_head(text: str, style: str) -> str:
    lower = text.lower()
    if "</head>" in lower:
        idx = lower.rfind("</head>")
        return text[:idx] + style + text[idx:]
    if "<body" in lower:
        match = re.search(r"<body[^>]*>", text, flags=re.I)
        if match:
            return text[: match.start()] + style + text[match.start() :]
    return style + text


def _inject_into_body(text: str, section: str) -> str:
    body = re.search(r"<body[^>]*>", text, flags=re.I)
    if body:
        return text[: body.end()] + section + text[body.end() :]
    return section + text


def build_function_option_patches(
    html_text: str,
    *,
    user_goal: str = "",
    project_kind: str = "web",
    keep_els: list[str] | None = None,
    delete_els: list[str] | None = None,
) -> tuple[dict[str, str], list[str], dict[str, Any]]:
    """Create A-C function variants by patching the current HTML locally."""
    if not supports_function_patch("functions", project_kind):
        return {}, [], {"status": "unsupported"}
    from .cinema_offline_options import _delete_without_keeps
    from .cinema_scripts import apply_spatial_deletes_to_html, finalize_cinema_html

    base = _strip_existing_patch(html_text)
    ir = build_project_ir(base)
    effective_delete = _delete_without_keeps(list(delete_els or []), list(keep_els or []))
    files: dict[str, str] = {}
    labels: list[str] = []
    for filename, variant, label in (
        ("alt_a.html", "a", "Option A (functions: quick path)"),
        ("alt_b.html", "b", "Option B (functions: workflow)"),
        ("alt_c.html", "c", "Option C (functions: funnel)"),
    ):
        out = _inject_into_head(base, _patch_style())
        out = _inject_into_body(out, _variant_section(variant, user_goal, ir))
        doc, ok, errors = prepare_cinema_html_document(out, ui_type="web")
        if not ok or not doc:
            return {}, [], {"status": "invalid", "errors": errors}
        if effective_delete:
            doc, _ = apply_spatial_deletes_to_html(doc, effective_delete)
            doc = finalize_cinema_html(doc)
        files[filename] = doc
        labels.append(label)
    return files, labels, {"status": "ok", "ir": ir}
