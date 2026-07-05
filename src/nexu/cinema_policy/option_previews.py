"""Building and refreshing Option A/B/C preview files from stage HTML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from repatch import (
    enforce_deletes_on_option_previews as _repatch_enforce_deletes_on_option_previews,
    sync_option_previews_from_workspace as _repatch_sync_option_previews_from_workspace,
)

from ..cinema_scripts import finalize_cinema_html
from .constraints import load_effective_ui_constraints, merge_ui_constraint_lists
from .html_checks import _replace_html_title


def ensure_option_previews_from_stages(cinema_dir: Path) -> dict[str, Any]:
    """Build Options A–C from stage0/1/2 when they represent different layouts."""
    written: list[str] = []
    for alt_name, stage_name, title in (
        ("alt_a.html", "stage0.html", "Option A (minimal)"),
        ("alt_b.html", "stage1.html", "Option B (balanced)"),
        ("alt_c.html", "stage2.html", "Option C (expanded)"),
    ):
        stage_path = cinema_dir / stage_name
        if not stage_path.exists():
            continue
        html = _replace_html_title(stage_path.read_text(encoding="utf-8"), title)
        (cinema_dir / alt_name).write_text(html, encoding="utf-8")
        written.append(alt_name)
    return {"status": "options_built_from_stages", "files": written}


def ensure_http_option_previews_from_stage0(cinema_dir: Path) -> dict[str, Any]:
    """Clone fetched website stage0 into Options A–C (palette iterations stay on-site)."""
    stage0 = cinema_dir / "stage0.html"
    if not stage0.is_file():
        return {"status": "skipped", "files": []}
    html = stage0.read_text(encoding="utf-8")
    written: list[str] = []
    for alt_name, title in (
        ("alt_a.html", "Option A (site baseline)"),
        ("alt_b.html", "Option B (site balanced)"),
        ("alt_c.html", "Option C (site expanded)"),
    ):
        (cinema_dir / alt_name).write_text(_replace_html_title(html, title), encoding="utf-8")
        written.append(alt_name)
    return {"status": "options_cloned_from_stage0", "files": written}


def sync_option_previews_from_workspace(
    cinema_dir: Path,
    *,
    stage: int = 0,
    delete_ids: list[str] | None = None,
    root: Path | None = None,
    capsule_name: str | None = None,
) -> dict[str, Any]:
    """
    Refresh Options A–C (and stage1/stage2 templates) from the active workspace HTML.

    Called after window-1 changes so preview panels stay aligned with stage{N}.html.
    """
    stage_file = cinema_dir / f"stage{stage}.html"
    if not stage_file.exists():
        return {"error": f"missing {stage_file.name}"}

    def _resolve_delete_ids() -> list[str]:
        if root is None or not capsule_name:
            return []
        effective = load_effective_ui_constraints(root, capsule_name, stage=stage)
        return list(effective.get("delete") or [])

    return _repatch_sync_option_previews_from_workspace(
        cinema_dir,
        stage=stage,
        delete_ids=delete_ids,
        delete_resolver=_resolve_delete_ids if root is not None and capsule_name else None,
        finalize_html=finalize_cinema_html,
    )


def enforce_deletes_on_option_previews(
    cinema_dir: Path,
    delete_ids: list[str],
    *,
    session_keep: list[str] | None = None,
    session_delete: list[str] | None = None,
) -> dict[str, Any]:
    """Apply policy DELETE list to existing alt_a/b/c without replacing from workspace.

    Session lists override ledger when both are passed (e.g. re-KEEP after DELETE).
    """
    _keep, effective_delete = merge_ui_constraint_lists(
        ledger_keep=[],
        ledger_delete=list(delete_ids),
        session_keep=list(session_keep or []),
        session_delete=list(session_delete or []),
    )
    return _repatch_enforce_deletes_on_option_previews(
        cinema_dir,
        effective_delete,
        finalize_html=finalize_cinema_html,
    )
