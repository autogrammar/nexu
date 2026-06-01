"""Compact project/UI intermediate representation for Cinema iteration."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any


class _ProjectIRParser(HTMLParser):
    _SKIP = frozenset({"script", "style", "noscript", "svg"})
    _ACTION_TAGS = frozenset({"a", "button", "input", "select", "textarea"})
    _SECTION_TAGS = frozenset({"header", "nav", "main", "section", "article", "aside", "footer"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.headings: list[dict[str, str]] = []
        self.actions: list[dict[str, str]] = []
        self.sections: list[dict[str, str]] = []
        self.cards: list[dict[str, str]] = []
        self._stack: list[dict[str, Any]] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self._SKIP:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        attr = {k.lower(): v or "" for k, v in attrs}
        self._stack.append({"tag": tag, "attrs": attr, "text": []})

    def _classify_node(
        self, tag: str, text: str, attrs: dict[str, str], item: dict[str, str]
    ) -> None:
        if tag == "title" and text:
            self.title = text[:120]
        elif tag in {"h1", "h2", "h3"} and text:
            self.headings.append(item)
        elif tag in self._ACTION_TAGS:
            label = (
                text
                or attrs.get("aria-label")
                or attrs.get("placeholder")
                or attrs.get("value")
            )
            item["text"] = _clean_text(label)[:120]
            self.actions.append(item)
        elif tag in self._SECTION_TAGS:
            self.sections.append(item)
        if "card" in attrs.get("class", "").lower() or tag == "article":
            self.cards.append(item)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self._SKIP:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth or not self._stack:
            return
        node = self._stack.pop()
        if node["tag"] != tag and self._stack:
            self._stack[-1]["text"].extend(node["text"])
            return
        text = _clean_text(" ".join(node["text"]))
        attrs = node["attrs"]
        item = {
            "tag": tag,
            "id": attrs.get("id", ""),
            "class": attrs.get("class", ""),
            "role": attrs.get("role", ""),
            "text": text[:160],
        }
        self._classify_node(tag, text, attrs, item)
        if self._stack and text:
            self._stack[-1]["text"].append(text)

    def handle_data(self, data: str) -> None:
        if self._skip_depth or not self._stack:
            return
        text = _clean_text(data)
        if text:
            self._stack[-1]["text"].append(text)


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def build_project_ir(html: str, *, max_items: int = 24) -> dict[str, Any]:
    """Extract a small UI/function map from HTML for patch prompts and local rules."""
    parser = _ProjectIRParser()
    parser.feed(str(html or ""))
    parser.close()
    return {
        "title": parser.title,
        "headings": parser.headings[:max_items],
        "actions": parser.actions[:max_items],
        "sections": parser.sections[:max_items],
        "cards": parser.cards[:max_items],
        "counts": {
            "headings": len(parser.headings),
            "actions": len(parser.actions),
            "sections": len(parser.sections),
            "cards": len(parser.cards),
        },
    }


def summarize_project_ir(ir: dict[str, Any]) -> str:
    """Render IR as compact text for LLM/debug traces."""
    title = str(ir.get("title") or "(untitled)")
    counts = ir.get("counts") if isinstance(ir.get("counts"), dict) else {}
    lines = [
        f"title: {title}",
        "counts: "
        + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())),
    ]
    for key in ("headings", "actions", "sections", "cards"):
        items = ir.get(key) if isinstance(ir.get(key), list) else []
        if not items:
            continue
        values = []
        for item in items[:8]:
            if not isinstance(item, dict):
                continue
            label = item.get("text") or item.get("id") or item.get("class") or item.get("tag")
            values.append(str(label))
        lines.append(f"{key}: " + " | ".join(values))
    return "\n".join(lines)
