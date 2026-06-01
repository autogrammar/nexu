"""Small LLM CSS patch workflow for Cinema option previews."""

from __future__ import annotations

import json
import re
from typing import Any

from .cinema_html_validate import validate_css_safety
from .cinema_scope import (
    SCOPE_STYLE_ID,
    normalize_focus_scope,
    scoped_html_fragment,
    strip_scope_style,
)

_ALT_FILES = ("alt_a.html", "alt_b.html", "alt_c.html")
_VISUAL_PATCH_SCOPES = frozenset({"colors", "shapes", "display", "orientation", "keypad"})
_BAD_CSS_TOKENS = (
    "<",
    "</style",
    "<script",
    "@import",
    "url(",
    "expression(",
    "javascript:",
)


def supports_llm_patch_scope(
    scope: str,
    project_kind: str,
    *,
    has_marks: bool = False,
) -> bool:
    """True when A-C options can be generated as a CSS patch instead of full HTML."""
    normalized = normalize_focus_scope(scope, project_kind)
    if has_marks and normalized == "functions":
        return False
    return normalized in _VISUAL_PATCH_SCOPES


def _compact_html(html: str, *, limit: int = 6000) -> str:
    text = re.sub(r"\s+", " ", str(html or "")).strip()
    if len(text) <= limit:
        return text
    head = text[: limit // 2]
    tail = text[-limit // 2 :]
    return head + "\n<!-- middle omitted for compact LLM patch prompt -->\n" + tail


def _patch_scope_rules(
    scope: str,
    *,
    keep_els: list[str] | None = None,
    delete_els: list[str] | None = None,
) -> list[str]:
    keep = list(keep_els or [])
    delete = list(delete_els or [])
    rules = [
        f"Focus only on #{scope}.",
        "Do not return HTML. Return CSS patches only.",
        "Preserve DOM structure, ids, labels, workflows, and JavaScript behavior.",
        "No external assets, imports, urls, scripts, or markdown.",
    ]
    if scope == "functions":
        rules.extend(
            [
                "DELETE-marked elements must be removed or fully redesigned.",
                "KEEP-marked elements are mandatory and must stay visually usable.",
            ]
        )
    elif scope in _VISUAL_PATCH_SCOPES:
        rules.extend(
            [
                f"Apply #{scope} changes primarily to DELETE-marked elements.",
                "KEEP-marked elements are hard constraints — preserve their styling.",
                "Do not restyle unrelated controls outside marked fragments.",
            ]
        )
    else:
        rules.extend(
            [
                "KEEP elements are mandatory and must stay visually usable.",
                "DELETE elements are the primary redesign targets.",
            ]
        )
    if keep:
        rules.append(f"KEEP ids: {', '.join(keep[:16])}.")
    if delete:
        rules.append(f"DELETE ids: {', '.join(delete[:16])}.")
    return rules


def build_ui_patch_prompt(
    html: str,
    *,
    focus_scope: str,
    project_kind: str,
    option_variants: list[tuple[str, str, str]],
    user_goal: str = "",
    keep_els: list[str] | None = None,
    delete_els: list[str] | None = None,
    context_fragment: str | None = None,
) -> str:
    """Build a compact JSON-only prompt for scoped CSS A-C options."""
    scope = normalize_focus_scope(focus_scope, project_kind)
    if context_fragment:
        fragment = context_fragment
    else:
        fragment = scoped_html_fragment(html, scope, project_kind) or _compact_html(html)
    variants = [
        {"file": filename, "label": label, "direction": note}
        for filename, label, note in option_variants
        if filename in _ALT_FILES
    ]
    contract = {
        "task": "Generate scoped UI option patches for Nexu Cinema.",
        "output": "JSON only, no markdown fences, no prose.",
        "schema": {
            "variants": {
                "alt_a.html": {"label": "short label", "css": "CSS patch only"},
                "alt_b.html": {"label": "short label", "css": "CSS patch only"},
                "alt_c.html": {"label": "short label", "css": "CSS patch only"},
            }
        },
        "rules": _patch_scope_rules(scope, keep_els=keep_els, delete_els=delete_els),
        "project_kind": project_kind or "web",
        "user_goal": user_goal or "",
        "keep": keep_els or [],
        "delete": delete_els or [],
        "variants": variants,
    }
    return (
        "INTRACT UI PATCH CONTRACT\n"
        + json.dumps(contract, ensure_ascii=False, indent=2)
        + "\n\nCURRENT UI HTML/FRAGMENT\n"
        + fragment
        + "\n\nReturn the JSON object now."
    )


def _strip_json_fence(text: str) -> str:
    raw = str(text or "").strip()
    fence = re.search(r"```(?:json|JSON)?\s*([\s\S]*?)```", raw)
    if fence:
        return fence.group(1).strip()
    return raw


def parse_ui_patch_response(text: str) -> dict[str, Any]:
    """Parse JSON object from an LLM patch response."""
    raw = _strip_json_fence(text)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("LLM patch response did not contain a JSON object") from None
        data = json.loads(raw[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("LLM patch response root must be an object")
    variants = data.get("variants")
    if not isinstance(variants, dict):
        raise ValueError("LLM patch response must contain variants object")
    return data


def _safe_css(css: object) -> str:
    text = str(css or "").strip()
    lowered = text.lower()
    if not text:
        raise ValueError("empty CSS patch")
    if len(text) > 5000:
        raise ValueError("CSS patch is too large")
    for token in _BAD_CSS_TOKENS:
        if token in lowered:
            raise ValueError(f"unsafe CSS token: {token}")
    if "{" not in text or "}" not in text:
        raise ValueError("CSS patch must contain CSS rules")
    ok, errors = validate_css_safety(text, source="LLM CSS patch")
    if not ok:
        raise ValueError("; ".join(errors[:4]))
    return text


def _label_for(filename: str, item: Any, fallback: dict[str, str]) -> str:
    if isinstance(item, dict):
        label = str(item.get("label") or "").strip()
        if label:
            return label[:120]
    return fallback.get(filename, filename)


def _css_for(item: Any) -> str:
    if isinstance(item, dict):
        return _safe_css(item.get("css"))
    return _safe_css(item)


def apply_ui_patch_options(
    html: str,
    patch: dict[str, Any],
    *,
    option_variants: list[tuple[str, str, str]],
) -> tuple[dict[str, str], list[str]]:
    """Apply validated CSS patches to one baseline HTML document."""
    variants = patch.get("variants")
    if not isinstance(variants, dict):
        raise ValueError("patch variants must be an object")
    fallback_labels = {filename: label for filename, label, _note in option_variants}
    base = strip_scope_style(str(html or ""))
    files: dict[str, str] = {}
    labels: list[str] = []
    for filename in _ALT_FILES:
        item = variants.get(filename)
        if item is None:
            raise ValueError(f"missing {filename} in LLM patch response")
        css = _css_for(item)
        label = _label_for(filename, item, fallback_labels)
        block = f'<style id="{SCOPE_STYLE_ID}">\n/* llm patch: {label} */\n{css}\n</style>\n'
        lower = base.lower()
        if "</head>" in lower:
            idx = lower.rfind("</head>")
            out = base[:idx] + block + base[idx:]
        elif "<body" in lower:
            match = re.search(r"<body[^>]*>", base, flags=re.I)
            if match:
                out = base[: match.start()] + block + base[match.start() :]
            else:
                out = block + base
        else:
            out = block + base
        files[filename] = out
        labels.append(label)
    return files, labels
