"""Effective KEEP/DELETE UI constraints derived from the cinema policy ledger."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from repatch import VISUAL_REDESIGN_SCOPES

from .snapshot import policy_ledger_path


def _ledger_entry_matches_project(
    entry: dict[str, Any],
    *,
    project_id: str | None,
    project_kind: str | None,
) -> bool:
    """Ignore legacy calculator marks when an HTTP import is active."""
    entry_pid = str(entry.get("project_id") or "").strip()
    if entry_pid:
        return entry_pid == str(project_id or "").strip()
    kind = str(project_kind or "").lower()
    active_id = str(project_id or "").strip()
    if kind == "imported" or active_id.startswith("http-"):
        return False
    return True


def promote_applies_spatial_deletes(focus_scope: str | None) -> bool:
    """Promote may spatial-delete option previews only outside visual redesign scopes."""
    active = str(focus_scope or "").strip().lower()
    return active not in VISUAL_REDESIGN_SCOPES


def _ledger_entry_matches_scope(entry: dict[str, Any], *, focus_scope: str | None) -> bool:
    """Scope-specific marks apply only within the same #scope iteration."""
    entry_scope = str(entry.get("focus_scope") or "").strip().lower()
    active_scope = str(focus_scope or "").strip().lower()
    if not active_scope:
        return True
    if not entry_scope:
        return False
    return entry_scope == active_scope


def _process_keep_delete_entries(entry: dict[str, Any], state: dict[str, str]) -> None:
    """Process keep and delete entries from a ledger entry."""
    for element_id in entry.get("keep") or []:
        key = str(element_id).strip()
        if key:
            state[key] = "keep"
    for element_id in entry.get("delete") or []:
        key = str(element_id).strip()
        if key:
            state[key] = "delete"


def _process_proposed_contracts(entry: dict[str, Any], state: dict[str, str]) -> None:
    """Process proposed contracts from a ledger entry."""
    from .proposals import _proposal_kind_and_element

    for proposal in entry.get("proposed_contracts") or []:
        if not isinstance(proposal, dict):
            continue
        kind, element = _proposal_kind_and_element(proposal)
        if not element or element == "unknown":
            continue
        if kind == "keep":
            state[element] = "keep"
        elif kind == "delete":
            state[element] = "delete"


def _process_ledger_entry(
    entry: dict[str, Any],
    state: dict[str, str],
    stage: int | None,
    *,
    project_id: str | None = None,
    project_kind: str | None = None,
    focus_scope: str | None = None,
) -> None:
    """Process a single ledger entry and update the state."""
    if stage is not None:
        raw_stage = entry.get("stage")
        if raw_stage is not None and int(raw_stage) != stage:
            return
    if not _ledger_entry_matches_project(
        entry, project_id=project_id, project_kind=project_kind
    ):
        return
    if not _ledger_entry_matches_scope(entry, focus_scope=focus_scope):
        return

    _process_keep_delete_entries(entry, state)
    _process_proposed_contracts(entry, state)


def _build_constraint_result(state: dict[str, str]) -> dict[str, Any]:
    """Build the final result dictionary from the state."""
    keep = sorted(key for key, value in state.items() if value == "keep")
    delete = sorted(key for key, value in state.items() if value == "delete")
    return {"keep": keep, "delete": delete, "by_element": state}


def effective_ui_constraints_from_ledger(
    ledger: list[Any],
    *,
    stage: int | None = None,
    project_id: str | None = None,
    project_kind: str | None = None,
    focus_scope: str | None = None,
) -> dict[str, Any]:
    """
    Effective KEEP/DELETE per UI element from the cinema policy ledger.

    Walks entries in order; later keep/delete for the same element wins.
    Also reads ``proposed_contracts`` when present.
    """
    state: dict[str, str] = {}
    if not isinstance(ledger, list):
        return {"keep": [], "delete": [], "by_element": {}}

    for entry in ledger:
        if not isinstance(entry, dict):
            continue
        _process_ledger_entry(
            entry,
            state,
            stage,
            project_id=project_id,
            project_kind=project_kind,
            focus_scope=focus_scope,
        )

    return _build_constraint_result(state)


def merge_ui_constraint_lists(
    *,
    ledger_keep: list[str],
    ledger_delete: list[str],
    session_keep: list[str],
    session_delete: list[str],
) -> tuple[list[str], list[str]]:
    """Ledger baseline; current session annotations override per element."""
    state: dict[str, str] = {}
    for element_id in ledger_keep:
        key = str(element_id).strip()
        if key:
            state[key] = "keep"
    for element_id in ledger_delete:
        key = str(element_id).strip()
        if key:
            state[key] = "delete"
    for element_id in session_keep:
        key = str(element_id).strip()
        if key:
            state[key] = "keep"
    for element_id in session_delete:
        key = str(element_id).strip()
        if key:
            state[key] = "delete"
    keep = sorted(key for key, value in state.items() if value == "keep")
    delete = sorted(key for key, value in state.items() if value == "delete")
    return keep, delete


def load_effective_ui_constraints(
    root: Path,
    capsule_name: str,
    *,
    stage: int = 0,
    project_id: str | None = None,
    project_kind: str | None = None,
    focus_scope: str | None = None,
    cinema_dir: Path | None = None,
) -> dict[str, Any]:
    """Load ledger from disk and return effective UI constraints for a stage."""
    if cinema_dir is not None and (project_id is None or project_kind is None):
        from ..cinema_projects import load_active_project

        active = load_active_project(Path(cinema_dir)) or {}
        if project_id is None:
            project_id = str(active.get("id") or "").strip() or None
        if project_kind is None:
            project_kind = str(active.get("kind") or "").strip() or None
    ledger_path = (
        Path(cinema_dir) / "intract_policy_ledger.json"
        if cinema_dir is not None
        else policy_ledger_path(root, capsule_name)
    )
    ledger: list[Any] = []
    if ledger_path.exists():
        data = json.loads(ledger_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            ledger = data
    return effective_ui_constraints_from_ledger(
        ledger,
        stage=stage,
        project_id=project_id,
        project_kind=project_kind,
        focus_scope=focus_scope,
    )


def resolve_iteration_mode(
    *,
    has_hints: bool = False,
    delete_count: int = 0,
    keep_count: int = 0,
    pending_goal: bool = False,
) -> str:
    """
    Cinema iteration target.

    - Queued goal (pending_goal) → options A–C only, ignores spatial marks until Run.
    - Goal hint without DELETE → options A–C only (window 1 unchanged).
    - DELETE → active workspace (spatial patch / LLM).
    - KEEP-only without hint → active workspace.
    """
    if delete_count > 0:
        return "active_workspace"
    if keep_count > 0:
        return "active_workspace"
    if pending_goal or (has_hints and delete_count == 0 and keep_count == 0):
        return "goal_options"
    if has_hints:
        return "goal_options"
    return "none"
