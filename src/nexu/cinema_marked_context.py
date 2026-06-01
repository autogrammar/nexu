"""Compact HTML/CSS context for Cinema marked workspace elements."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any

from .cinema_http_preprocess import _split_css_rules
from .cinema_scope import normalize_focus_scope

MAX_MARKED_CONTEXT_BYTES = 12_000
MAX_FRAGMENT_BYTES = 2_500
MAX_CSS_BYTES = 6_000

_VOID_TAGS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)
_TAG_OPEN_RE = re.compile(r"<\s*([a-zA-Z][\w:-]*)\b([^>]*)>", re.DOTALL)
_ATTR_RE = re.compile(
    r"""([\w:-]+)\s*=\s*(['"])(.*?)\2""",
    re.DOTALL,
)
_VISUAL_SCOPES = frozenset({"colors", "shapes", "display", "orientation", "keypad"})


def has_ui_marks(
    keep_els: list[str] | None = None,
    delete_els: list[str] | None = None,
) -> bool:
    """True when the session or ledger sent KEEP/DELETE element ids."""
    keep = [str(x).strip() for x in (keep_els or []) if str(x).strip()]
    delete = [str(x).strip() for x in (delete_els or []) if str(x).strip()]
    return bool(keep or delete)


def marked_css_selectors(element_ids: list[str]) -> list[str]:
    """CSS selectors for marked logical element ids (id, btn- prefix, data-nexu-target)."""
    selectors: list[str] = []
    seen: set[str] = set()
    for element_id in element_ids:
        for token in _id_candidates(element_id):
            for sel in (f"#{token}", f'[data-nexu-target="{token}"]'):
                if sel not in seen:
                    seen.add(sel)
                    selectors.append(sel)
    return selectors


def restrict_scope_css_to_marks(css: str, delete_ids: list[str]) -> str:
    """Limit offline/LLM scope CSS to DELETE-marked selectors; drop page-wide rules."""
    delete = [str(x).strip() for x in (delete_ids or []) if str(x).strip()]
    if not css or not delete:
        return css
    prefix_list = marked_css_selectors(delete)
    if not prefix_list:
        return css
    prefix = ", ".join(prefix_list)
    kept: list[str] = []
    for rule in _split_css_rules(css):
        chunk = rule.strip()
        if not chunk or "{" not in chunk:
            continue
        selector, rest = chunk.split("{", 1)
        sel = selector.strip().lower()
        if not sel or sel.startswith(("html", "body")):
            continue
        decl = rest.rsplit("}", 1)[0].strip()
        if not decl:
            continue
        kept.append(f"{prefix} {{{decl}}}")
    return "\n".join(kept)


def _id_candidates(element_id: str) -> set[str]:
    raw = str(element_id or "").strip()
    if not raw:
        return set()
    out = {raw, raw.lower()}
    if raw.startswith("btn-"):
        out.add(raw[4:])
        out.add(raw[4:].lower())
    else:
        prefixed = f"btn-{raw}"
        out.add(prefixed)
        out.add(prefixed.lower())
    return out


def _parse_attrs(attr_text: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in _ATTR_RE.finditer(attr_text or ""):
        key = match.group(1).lower()
        value = re.sub(r"\s+", " ", match.group(3)).strip()
        attrs[key] = value
    return attrs


def _logical_id(tag: str, attrs: dict[str, str], *, text: str = "") -> str | None:
    raw_id = str(attrs.get("id") or "").strip()
    if raw_id:
        return raw_id[4:] if raw_id.startswith("btn-") else raw_id
    target = str(attrs.get("data-nexu-target") or "").strip()
    if target:
        return target
    if tag.lower() == "button":
        label = re.sub(r"\s+", " ", text).strip()
        if label:
            return label
    return None


def _extract_balanced_html(html: str, start: int) -> tuple[str, int] | None:
    """Return outerHTML starting at ``start`` and the index after it."""
    open_match = _TAG_OPEN_RE.match(html, start)
    if not open_match:
        return None
    tag = open_match.group(1).lower()
    open_end = open_match.end()
    if open_match.group(0).rstrip().endswith("/>"):
        return html[start:open_end], open_end
    if tag in _VOID_TAGS:
        return html[start:open_end], open_end
    depth = 1
    pos = open_end
    length = len(html)
    open_pat = re.compile(rf"<\s*{re.escape(tag)}\b", re.IGNORECASE)
    close_pat = re.compile(rf"<\s*/\s*{re.escape(tag)}\s*>", re.IGNORECASE)
    while pos < length and depth > 0:
        next_open = open_pat.search(html, pos)
        next_close = close_pat.search(html, pos)
        if next_close is None:
            break
        if next_open is not None and next_open.start() < next_close.start():
            depth += 1
            pos = next_open.end()
            continue
        depth -= 1
        pos = next_close.end()
    if depth != 0:
        return None
    return html[start:pos], pos


def _find_marked_subtrees(html: str, marked_ids: set[str]) -> dict[str, str]:
    """Map logical element id → compact outerHTML fragment."""
    if not marked_ids:
        return {}
    wanted = {str(item).strip() for item in marked_ids if str(item).strip()}
    found: dict[str, str] = {}
    text = str(html or "")
    for match in _TAG_OPEN_RE.finditer(text):
        tag = match.group(1).lower()
        attrs = _parse_attrs(match.group(2))
        raw_id = str(attrs.get("id") or "").strip()
        candidates = _id_candidates(raw_id) if raw_id else set()
        target = str(attrs.get("data-nexu-target") or "").strip()
        if target:
            candidates |= _id_candidates(target)
        logical = _logical_id(tag, attrs)
        if logical:
            candidates |= _id_candidates(logical)
        hit = wanted & candidates
        if not hit and tag == "button" and not raw_id and not target:
            # Match buttons identified only by visible label.
            inner_start = match.end()
            inner_end = text.lower().find(f"</{tag}>", inner_start)
            label = re.sub(r"\s+", " ", text[inner_start:inner_end if inner_end >= 0 else inner_start]).strip()
            logical = _logical_id(tag, attrs, text=label)
            if logical:
                hit = wanted & _id_candidates(logical)
        if not hit:
            continue
        extracted = _extract_balanced_html(text, match.start())
        if not extracted:
            continue
        fragment, _ = extracted
        compact = re.sub(r"\s+", " ", fragment).strip()
        if len(compact.encode("utf-8")) > MAX_FRAGMENT_BYTES:
            compact = compact[: MAX_FRAGMENT_BYTES - 32].rstrip() + " <!-- truncated -->"
        for element_id in hit:
            found.setdefault(element_id, compact)
        if len(found) >= len(wanted):
            break
    return found


def _selector_tokens(subtrees: dict[str, str]) -> set[str]:
    tokens: set[str] = set()
    for element_id in subtrees:
        tokens |= {f"#{item}" for item in _id_candidates(element_id)}
    for fragment in subtrees.values():
        for match in re.finditer(r"""\bid\s*=\s*(['"])(.*?)\1""", fragment, re.IGNORECASE):
            raw = match.group(2).strip()
            if raw:
                tokens |= {f"#{raw}", f"#{raw.lower()}"}
        for match in re.finditer(r"""class\s*=\s*(['"])(.*?)\1""", fragment, re.IGNORECASE):
            for cls in re.split(r"\s+", match.group(2).strip()):
                if cls:
                    tokens.add(f".{cls}")
                    tokens.add(f".{cls.lower()}")
    return tokens


def _filter_css_for_tokens(css: str, tokens: set[str]) -> str:
    if not css or not tokens:
        return ""
    kept: list[str] = []
    for rule in _split_css_rules(css):
        selector = rule.split("{", 1)[0].lower()
        if any(token.lower() in selector for token in tokens):
            kept.append(rule)
    return "\n\n".join(kept)


def _collect_css_sources(html: str, ui_profile: dict[str, Any] | None) -> str:
    chunks: list[str] = []
    for match in re.finditer(r"<style\b[^>]*>([\s\S]*?)</style>", html or "", re.IGNORECASE):
        block = match.group(1).strip()
        if block:
            chunks.append(block)
    profile = ui_profile if isinstance(ui_profile, dict) else {}
    visual = str(profile.get("visual_css") or "").strip()
    if visual:
        chunks.append(visual)
    return "\n\n".join(chunks)


def _scope_semantics(scope: str) -> list[str]:
    normalized = (scope or "").strip().lower()
    if normalized == "functions":
        return [
            "DELETE-marked elements must be removed or fully redesigned in each variant.",
            "KEEP-marked elements must remain present and usable.",
        ]
    if normalized in _VISUAL_SCOPES:
        return [
            f"Apply #{normalized} changes primarily to DELETE-marked elements.",
            "KEEP-marked elements are hard constraints — preserve their colors/shapes/layout.",
            "Do not restyle unrelated controls outside the marked fragments.",
        ]
    return [
        "DELETE-marked elements are the primary redesign targets.",
        "KEEP-marked elements must remain present and usable.",
    ]


def _cap_text(text: str, limit: int) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= limit:
        return text
    trimmed = encoded[: limit - 48].decode("utf-8", errors="ignore").rstrip()
    return trimmed + "\n<!-- nexu: marked context truncated -->"


def _client_fragment_html(client_fragments: list[Any] | None, element_id: str) -> str | None:
    for item in client_fragments or []:
        if not isinstance(item, dict):
            continue
        ident = str(item.get("id") or "").strip()
        if ident != element_id:
            continue
        frag = item.get("fragment")
        if isinstance(frag, dict):
            html = re.sub(r"\s+", " ", str(frag.get("html") or "")).strip()
            if html:
                return html
    return None


def build_marked_element_context(
    html: str,
    *,
    keep_ids: list[str] | None = None,
    delete_ids: list[str] | None = None,
    focus_scope: str = "",
    project_kind: str = "",
    ui_profile: dict[str, Any] | None = None,
    client_fragments: list[Any] | None = None,
) -> str | None:
    """Extract HTML subtrees + relevant CSS for marked ids; None when no matches."""
    keep = [str(x).strip() for x in (keep_ids or []) if str(x).strip()]
    delete = [str(x).strip() for x in (delete_ids or []) if str(x).strip()]
    marked_ids = keep + [x for x in delete if x not in keep]
    if not marked_ids:
        return None

    subtrees = _find_marked_subtrees(html, set(marked_ids))
    for element_id in marked_ids:
        if element_id in subtrees:
            continue
        client_html = _client_fragment_html(client_fragments, element_id)
        if client_html:
            subtrees[element_id] = client_html
    if not subtrees:
        return None

    scope = normalize_focus_scope(focus_scope, project_kind)
    tokens = _selector_tokens(subtrees)
    css = _filter_css_for_tokens(_collect_css_sources(html, ui_profile), tokens)
    if len(css.encode("utf-8")) > MAX_CSS_BYTES:
        css = _cap_text(css, MAX_CSS_BYTES)

    profile = ui_profile if isinstance(ui_profile, dict) else {}
    patch_mode = str(profile.get("llm_context_mode") or "") == "patch"
    outline = str(profile.get("html_outline") or "").strip()

    parts = [
        "MARKED ELEMENT CONTEXT (send only marked fragments — not the full page).",
        f"Focus scope: #{scope}",
        f"KEEP: {keep or ['none']}",
        f"DELETE: {delete or ['none']}",
        "Scope semantics:",
        *[f"- {line}" for line in _scope_semantics(scope)],
    ]
    if patch_mode and outline:
        parts.append(
            "Patch mode: full-page skeleton lives in nexu-outline.html; "
            "change CSS values and minimal attributes for marked fragments only."
        )
    parts.append("Marked HTML fragments:")
    for element_id in marked_ids:
        fragment = subtrees.get(element_id)
        if not fragment:
            parts.append(f"- #{element_id}: (not found in current HTML)")
            continue
        role = "KEEP" if element_id in keep else "DELETE"
        parts.append(f"- #{element_id} [{role}]:\n```html\n{fragment}\n```")
    if css:
        parts.append("Relevant CSS for marked elements:\n```css\n" + css + "\n```")
    elif patch_mode:
        parts.append(
            "Relevant CSS: use visual CSS tokens from project preprocess; "
            "target selectors matching marked ids/classes only."
        )

    body = "\n\n".join(parts)
    return _cap_text(body, MAX_MARKED_CONTEXT_BYTES)


def resolve_marked_llm_context(
    html: str,
    *,
    keep_els: list[str] | None = None,
    delete_els: list[str] | None = None,
    focus_scope: str = "",
    project_kind: str = "",
    ui_profile: dict[str, Any] | None = None,
    client_fragments: list[Any] | None = None,
) -> str | None:
    """Preferred LLM context when session marks exist."""
    keep = list(keep_els or [])
    delete = list(delete_els or [])
    if not keep and not delete:
        return None
    return build_marked_element_context(
        html,
        keep_ids=keep,
        delete_ids=delete,
        focus_scope=focus_scope,
        project_kind=project_kind,
        ui_profile=ui_profile,
        client_fragments=client_fragments,
    )
