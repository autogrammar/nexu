"""Context compaction for fast Nexu LLM improvement loops."""

from __future__ import annotations

import re

_VISUAL_SCOPE_FALLBACKS = frozenset({"colors", "shapes", "display", "orientation", "keypad"})


def compact_html_for_llm(html: str, *, limit: int) -> str:
    """Remove runtime scripts and cap current HTML context before an LLM call."""
    cleaned = re.sub(r"<script\b[^>]*>[\s\S]*?</script>", "", str(html or ""), flags=re.I)
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned).strip()
    if len(cleaned) > limit:
        return cleaned[:limit].rstrip() + "\n<!-- current html context truncated -->"
    return cleaned


def effective_markpact_mode(
    focus_scope: str,
    project_kind: str,
    *,
    default_mode: str,
    env_off: str = "",
) -> str:
    """Disable Markpact context for visual-only scopes unless explicitly needed."""
    default = (default_mode or "summary").strip().lower()
    scope = (focus_scope or "").strip().lower()
    try:
        from nexu.cinema_scope import scope_supports_offline_fast_path

        is_visual = scope_supports_offline_fast_path(scope, project_kind)
    except Exception:
        is_visual = scope in _VISUAL_SCOPE_FALLBACKS
    if is_visual:
        return "off"
    if (env_off or "").strip().lower() in {"1", "true", "yes", "on"} and scope != "functions":
        return "off"
    return default


def compact_markpact_for_llm(markdown: str, *, mode: str, limit: int) -> str:
    """Keep only high-value Markpact sections for fast LLM requests."""
    text = str(markdown or "")
    effective_mode = (mode or "summary").strip().lower()
    text = re.sub(
        r"\n## Application UI\n\n```html markpact:file path=index\.html[\s\S]*?```\n",
        "\n## Application UI\n\n(omitted from Markpact context; see Current HTML block below)\n",
        text,
        flags=re.I,
    )
    if effective_mode in {"off", "none", "0"}:
        return "(Markpact context disabled for this LLM call)"
    if effective_mode in {"summary", "fast"}:
        sections: list[str] = []
        for heading in ("## Nexu context", "## Intract baseline model", "## Project context"):
            match = re.search(
                rf"{re.escape(heading)}\n[\s\S]*?(?=\n## |\Z)",
                text,
                flags=re.I,
            )
            if match:
                sections.append(match.group(0).strip())
        text = "\n\n".join(sections) if sections else text
    suffix = "\n\n<!-- markpact context truncated -->" if len(text) > limit else ""
    return text[:limit].rstrip() + suffix
