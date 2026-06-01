"""Validate and repair Cinema LLM HTML option documents."""

from __future__ import annotations

import re

from .cinema_html import ensure_html_document_closure

_ALT_FILES = frozenset({"alt_a.html", "alt_b.html", "alt_c.html"})
_STYLE_TAG_RE = re.compile(r"<\s*style\b[^>]*>[\s\S]*?<\s*/style\s*>", re.I)
_STYLE_BODY_RE = re.compile(r"<\s*style\b[^>]*>([\s\S]*?)<\s*/style\s*>", re.I)
_RULE_RE = re.compile(r"(?P<selectors>[^{}]+)\{(?P<body>[^{}]+)\}", re.S)
_DECL_RE = re.compile(r"(?P<name>[-a-zA-Z]+)\s*:\s*(?P<value>[^;]+)")
_NEXU_SELECTOR_RE = re.compile(r"(?:\.|#)nexu-", re.I)


def _strip_css_comments(css: str) -> str:
    return re.sub(r"/\*[\s\S]*?\*/", "", str(css or ""))


def _selector_is_runtime_only(selector: str) -> bool:
    return bool(_NEXU_SELECTOR_RE.search(selector or ""))


def validate_css_safety(css: str, *, source: str = "css") -> tuple[bool, list[str]]:
    """Reject CSS patterns that commonly break Cinema previews.

    Runtime Nexu overlay selectors are allowed to use fixed positioning; generated
    app CSS should stay in normal flow and use flex/grid for layout changes.
    """
    errors: list[str] = []
    text = _strip_css_comments(css)
    if not text.strip():
        return True, []
    if re.search(r"@import\b|url\s*\(|expression\s*\(|javascript\s*:", text, re.I):
        errors.append(f"{source}: external or executable CSS is not allowed")

    for match in _RULE_RE.finditer(text):
        selectors = " ".join(match.group("selectors").split())
        body = match.group("body")
        if _selector_is_runtime_only(selectors):
            continue
        declarations = {
            decl.group("name").strip().lower(): decl.group("value").strip().lower()
            for decl in _DECL_RE.finditer(body)
        }
        position = declarations.get("position", "")
        if position in {"absolute", "fixed"}:
            errors.append(f"{source}: {selectors} uses position:{position}")
        for name, value in declarations.items():
            if name.startswith("margin") and re.match(r"-\d", value):
                errors.append(f"{source}: {selectors} uses negative {name}")
            if name == "transform" and ":hover" not in selectors:
                errors.append(f"{source}: {selectors} uses transform outside hover state")
            if name in {"top", "left", "right", "bottom"} and position in {"absolute", "fixed"}:
                errors.append(f"{source}: {selectors} uses manual {name} offset")
    return len(errors) == 0, errors


def _looks_like_html_document(text: str) -> bool:
    sample = str(text or "").lstrip()[:4000].lower()
    return "<html" in sample or "<!doctype" in sample


def _has_open_tag(html: str, tag: str) -> bool:
    return re.search(rf"<\s*{tag}\b", html, re.I) is not None


def _has_close_tag(html: str, tag: str) -> bool:
    return re.search(rf"<\s*/{tag}\s*>", html, re.I) is not None


def relocate_style_tags_to_head(html: str) -> str:
    """Move <style> blocks that sit outside <head> into the document head."""
    text = str(html or "")
    head_open = re.search(r"<\s*head\b", text, re.I)
    head_close = re.search(r"<\s*/head\s*>", text, re.I)
    if not head_open or not head_close:
        return text

    head_start = head_open.start()
    head_end = head_close.end()
    extracted: list[str] = []
    kept: list[str] = []
    last = 0
    for match in _STYLE_TAG_RE.finditer(text):
        kept.append(text[last : match.start()])
        if head_start <= match.start() and match.end() <= head_end:
            kept.append(match.group(0))
        else:
            extracted.append(match.group(0))
        last = match.end()
    kept.append(text[last:])
    if not extracted:
        return text

    without = "".join(kept)
    close_idx = without.lower().rfind("</head>")
    if close_idx < 0:
        return text
    block = "\n".join(extracted) + "\n"
    return without[:close_idx] + block + without[close_idx:]


def repair_html_structure(html: str) -> str:
    """Apply lightweight fixes for common LLM HTML mistakes."""
    text = str(html or "").strip()
    if not text:
        return text

    if _looks_like_html_document(text) and not text.lstrip().upper().startswith("<!DOCTYPE"):
        text = "<!DOCTYPE html>\n" + text.lstrip()

    if _has_open_tag(text, "html"):
        text = ensure_html_document_closure(text)

    if _has_open_tag(text, "html") and not _has_open_tag(text, "head"):
        text = re.sub(
            r"(<\s*html[^>]*>)",
            r'\1\n<head><meta charset="utf-8"></head>',
            text,
            count=1,
            flags=re.I,
        )

    if _has_open_tag(text, "head") and not _has_open_tag(text, "body"):
        text = re.sub(
            r"(<\s*/head\s*>)",
            r"\1\n<body>",
            text,
            count=1,
            flags=re.I,
        )
        lower = text.lower()
        if "</body>" not in lower:
            if "</html>" in lower:
                idx = lower.rfind("</html>")
                text = text[:idx] + "\n</body>\n" + text[idx:]
            else:
                text = text.rstrip() + "\n</body>\n</html>\n"

    return relocate_style_tags_to_head(text).strip()


def _validate_basic_tags(text: str, errors: list[str]) -> None:
    if not _looks_like_html_document(text):
        errors.append("missing html root")
    lower = text.lower()
    if "<!doctype" not in lower[:240]:
        errors.append("missing doctype")
    for tag in ("html", "head", "body"):
        if not _has_open_tag(text, tag):
            errors.append(f"missing {tag} element")
    for tag in ("body", "html"):
        if not _has_close_tag(text, tag):
            errors.append(f"missing closing {tag} tag")


def _validate_calculator_elements(text: str, errors: list[str]) -> None:
    if not re.search(r'\bid=["\']screen["\']', text, re.I):
        errors.append("calculator missing #screen")
    if not re.search(r'class=["\'][^"\']*\bbtn\b', text, re.I):
        errors.append("calculator missing .btn controls")


def validate_cinema_html_document(html: str, *, ui_type: str = "web") -> tuple[bool, list[str]]:
    """Return whether HTML has the minimum structure expected in Cinema previews."""
    text = str(html or "").strip()
    errors: list[str] = []
    if not text:
        return False, ["empty document"]
    _validate_basic_tags(text, errors)

    lower = text.lower()
    head_close = lower.find("</head>")
    body_open = re.search(r"<\s*body\b", text, re.I)
    if head_close >= 0 and body_open:
        gap = text[head_close + len("</head>") : body_open.start()]
        if re.search(r"<\s*style\b", gap, re.I):
            errors.append("style element between head and body")

    if ui_type == "calculator":
        _validate_calculator_elements(text, errors)

    for index, style in enumerate(_STYLE_BODY_RE.findall(text), start=1):
        _ok, css_errors = validate_css_safety(style, source=f"style[{index}]")
        errors.extend(css_errors)

    return len(errors) == 0, errors


def prepare_cinema_html_document(
    html: str,
    *,
    ui_type: str = "web",
) -> tuple[str | None, bool, list[str]]:
    """Repair then validate one HTML document for Cinema option serving."""
    repaired = repair_html_structure(html)
    ok, errors = validate_cinema_html_document(repaired, ui_type=ui_type)
    if ok:
        return repaired, True, []
    return None, False, errors


def filter_valid_option_batch(
    batch: dict[str, str],
    *,
    ui_type: str = "web",
) -> tuple[dict[str, str], list[str]]:
    """Keep only structurally valid A/B/C option files; all three must pass."""
    if not batch:
        return {}, ["empty option batch"]

    prepared: dict[str, str] = {}
    errors: list[str] = []
    for filename in ("alt_a.html", "alt_b.html", "alt_c.html"):
        html = batch.get(filename)
        if not html:
            errors.append(f"{filename}: missing option")
            continue
        doc, ok, doc_errors = prepare_cinema_html_document(html, ui_type=ui_type)
        if ok and doc:
            prepared[filename] = doc
        else:
            errors.extend(f"{filename}: {err}" for err in doc_errors)

    if set(prepared.keys()) != _ALT_FILES:
        return {}, errors or ["incomplete option batch"]
    return prepared, []
