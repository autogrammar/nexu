"""Option-file cache helpers for fast Cinema delivery."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nexu.cinema_html_validate import filter_valid_option_batch
from nexu.cinema_options_cache import (
    options_cache_key,
    read_options_cache,
    write_options_cache,
)

ALT_OPTION_FILES = ("alt_a.html", "alt_b.html", "alt_c.html")


def _looks_like_calculator(html: str) -> bool:
    text = str(html or "").lower()
    return "calc-body" in text or 'id="screen"' in text or "id='screen'" in text


def _compatible_with_stage(stage_html: str, files: dict[str, str], *, ui_type: str) -> bool:
    """Reject stale cached options from a different UI family."""
    if ui_type == "calculator":
        return True
    stage_is_calc = _looks_like_calculator(stage_html)
    cached_is_calc = any(_looks_like_calculator(html) for html in files.values())
    if cached_is_calc and not stage_is_calc:
        return False
    return True


def read_cached_options(
    *,
    cinema_dir: Path,
    cache_dir: Path,
    enabled: bool,
    stage_html: str,
    ledger: Any,
    focus_scope: str,
    goal: str,
    keep_els: list[str],
    delete_els: list[str],
    ui_type: str = "web",
) -> tuple[list[str], str] | None:
    """Apply cached alt_a/b/c files into a Cinema directory when available."""
    if not enabled:
        return None
    key = options_cache_key(
        stage_html=stage_html,
        ledger=ledger,
        focus_scope=focus_scope,
        goal=goal,
        keep_els=keep_els,
        delete_els=delete_els,
    )
    cached = read_options_cache(cache_dir, key)
    if not cached:
        return None
    valid_files, _errors = filter_valid_option_batch(
        dict(cached.get("files") or {}),
        ui_type=ui_type,
    )
    if not valid_files:
        return None
    if not _compatible_with_stage(stage_html, valid_files, ui_type=ui_type):
        return None
    labels = list(cached.get("labels") or [])
    written: list[str] = []
    root = Path(cinema_dir)
    for index, name in enumerate(ALT_OPTION_FILES):
        html = valid_files.get(name)
        if not html:
            continue
        (root / name).write_text(html, encoding="utf-8")
        written.append(str(labels[index]) if index < len(labels) else name)
    if len(written) < len(ALT_OPTION_FILES):
        return None
    return written, key


def store_options_cache(
    *,
    cache_dir: Path,
    enabled: bool,
    stage_html: str,
    ledger: Any,
    focus_scope: str,
    goal: str,
    keep_els: list[str],
    delete_els: list[str],
    files: dict[str, str],
    labels: list[str],
    source: str,
) -> str | None:
    """Store complete alt_a/b/c option HTML files and return the cache key."""
    if not enabled or len(files) < len(ALT_OPTION_FILES):
        return None
    key = options_cache_key(
        stage_html=stage_html,
        ledger=ledger,
        focus_scope=focus_scope,
        goal=goal,
        keep_els=keep_els,
        delete_els=delete_els,
    )
    write_options_cache(
        cache_dir,
        key,
        files=files,
        labels=labels,
        source=source,
        focus_scope=focus_scope,
        goal=goal,
    )
    return key


def read_option_files(cinema_dir: Path) -> dict[str, str]:
    """Read existing alt_a/b/c files from a Cinema directory."""
    out: dict[str, str] = {}
    root = Path(cinema_dir)
    for name in ALT_OPTION_FILES:
        path = root / name
        if path.is_file():
            out[name] = path.read_text(encoding="utf-8")
    return out
