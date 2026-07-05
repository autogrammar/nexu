"""HTML normalization and option/stage-file distinctness checks."""

from __future__ import annotations

from pathlib import Path

from repatch import (
    html_files_distinct as _repatch_html_files_distinct,
    replace_html_title as _repatch_replace_html_title,
)


def _normalize_html_body(html: str) -> str:
    from repatch import normalize_html_body

    return normalize_html_body(html)


def _html_files_distinct(cinema_dir: Path, names: list[str]) -> bool:
    return _repatch_html_files_distinct(cinema_dir, names)


def option_previews_are_distinct(cinema_dir: Path) -> bool:
    return _html_files_distinct(
        cinema_dir, ["alt_a.html", "alt_b.html", "alt_c.html"]
    )


def stage_files_are_distinct(cinema_dir: Path) -> bool:
    return _html_files_distinct(
        cinema_dir, ["stage0.html", "stage1.html", "stage2.html"]
    )


def _replace_html_title(html: str, title: str) -> str:
    return _repatch_replace_html_title(html, title)
