#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
REF_RE = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)", re.MULTILINE)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)

EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".nexu",
    ".pytest_cache",
    ".ruff_cache",
    ".tmp_nexu_run",
    ".venv",
    "__pycache__",
    "markpact_sandbox",
    "node_modules",
    "venv",
    "workspace",
}


def _is_external(target: str) -> bool:
    parsed = urlsplit(target)
    return bool(parsed.scheme) or target.startswith("#") or target.startswith("mailto:")


def _slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"\s+", "-", text.strip().lower())


def _anchors(path: Path) -> set[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(errors="ignore")
    anchors = {""}
    for match in HEADING_RE.finditer(text):
        anchors.add(_slug(match.group(2)))
    return anchors


def _markdown_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if not any(part in EXCLUDED_PARTS for part in path.relative_to(root).parts)
    )


def _targets(text: str) -> list[str]:
    return [*LINK_RE.findall(text), *REF_RE.findall(text)]


def _resolve(base: Path, target: str) -> tuple[Path, str]:
    parsed = urlsplit(target.strip())
    path = unquote(parsed.path)
    return (base / path).resolve(), unquote(parsed.fragment)


def check_links(root: Path) -> list[str]:
    errors: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}
    root = root.resolve()

    for md_file in _markdown_files(root):
        text = md_file.read_text(encoding="utf-8", errors="ignore")
        for raw_target in _targets(text):
            target = raw_target.strip().strip("<>")
            if not target or _is_external(target):
                continue
            resolved, fragment = _resolve(md_file.parent, target)
            if resolved.is_dir():
                candidates = [resolved / "README.md", resolved / "index.md"]
                if not any(candidate.exists() for candidate in candidates):
                    errors.append(f"{md_file.relative_to(root)}: directory link has no README/index: {target}")
                continue
            if not resolved.exists():
                errors.append(f"{md_file.relative_to(root)}: missing link target: {target}")
                continue
            if fragment and resolved.suffix.lower() == ".md":
                anchors = anchor_cache.setdefault(resolved, _anchors(resolved))
                if fragment not in anchors:
                    errors.append(f"{md_file.relative_to(root)}: missing anchor '{fragment}' in {target}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local Markdown links.")
    parser.add_argument("root", nargs="?", default=".", type=Path)
    args = parser.parse_args()

    errors = check_links(args.root)
    if errors:
        print("Broken Markdown links:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Markdown links OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
