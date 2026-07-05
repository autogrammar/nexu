"""Reading and appending entries to the cinema policy ledger file on disk."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..paths import project_root
from .proposals import normalize_proposals_for_ledger, propose_ui_delta_contract_dicts
from .snapshot import policy_ledger_path


def _resolve_ledger_path(
    root: Path,
    capsule_name: str,
    *,
    cinema_dir: Path | None = None,
) -> Path:
    if cinema_dir is not None:
        return Path(cinema_dir) / "intract_policy_ledger.json"
    return policy_ledger_path(root, capsule_name)


def append_policy_ledger_entry(
    root: Path,
    capsule_name: str,
    entry: dict[str, Any],
    *,
    cinema_dir: Path | None = None,
) -> None:
    ledger_path = _resolve_ledger_path(root, capsule_name, cinema_dir=cinema_dir)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger: list[Any] = []
    if ledger_path.exists():
        data = json.loads(ledger_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            ledger = data
    ledger.append(entry)
    ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False), encoding="utf-8")


def append_goal_ledger_entry(
    root: Path,
    capsule_name: str,
    *,
    stage: int,
    goal: str,
    focus_scope: str = "",
    focus_scope_label: str = "",
    current_state: str = "",
    expected_version: str = "",
    project_context: str = "",
    project_kind: str = "",
    cinema_dir: Path | None = None,
) -> dict[str, Any]:
    from ..cinema_goal_contracts import propose_goal_extension_contracts

    proposals = normalize_proposals_for_ledger(
        stage,
        capsule_name,
        propose_goal_extension_contracts(
            goal,
            capsule_name=capsule_name,
            stage=stage,
            focus_scope=focus_scope,
            focus_scope_label=focus_scope_label,
            current_state=current_state,
            expected_version=expected_version,
            project_context=project_context,
            project_kind=project_kind,
        ),
    )
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "capsule": capsule_name,
        "workspace": str(project_root(root)),
        "stage": stage,
        "status": "goal_defined",
        "model": "goal_to_intract",
        "user_goal": (goal or "").strip(),
        "focus_scope": (focus_scope or "").strip(),
        "focus_scope_label": (focus_scope_label or "").strip(),
        "current_state": (current_state or "").strip(),
        "expected_version": (expected_version or "").strip(),
        "project_context": (project_context or "").strip(),
        "keep": [],
        "delete": [],
        "proposed_contracts": proposals,
    }
    append_policy_ledger_entry(root, capsule_name, entry, cinema_dir=cinema_dir)
    return entry


def load_goal_contract_lines(
    root: Path,
    capsule_name: str,
    *,
    cinema_dir: Path | None = None,
) -> list[str]:
    """Latest goal-defined contracts for LLM / verify context."""
    ledger_path = _resolve_ledger_path(root, capsule_name, cinema_dir=cinema_dir)
    if not ledger_path.exists():
        return []
    data = json.loads(ledger_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []
    for entry in reversed(data):
        if not isinstance(entry, dict):
            continue
        if entry.get("status") != "goal_defined":
            continue
        lines: list[str] = []
        for proposal in entry.get("proposed_contracts") or []:
            if isinstance(proposal, dict):
                line = proposal.get("line") or proposal.get("delta_text")
                if line:
                    lines.append(str(line))
        if lines:
            return lines
    return []


def append_iteration_ledger_entry(
    root: Path,
    capsule_name: str,
    *,
    stage: int,
    keep: list[str],
    delete: list[str],
    status: str,
    model: str,
    domain: str = "calculator",
    project_id: str = "",
    focus_scope: str = "",
    cinema_dir: Path | None = None,
) -> dict[str, Any]:
    proposals = normalize_proposals_for_ledger(
        stage,
        capsule_name,
        propose_ui_delta_contract_dicts(
            stage=stage,
            keep=keep,
            delete=delete,
            capsule_name=capsule_name,
            domain=domain,
            project_id=project_id,
            focus_scope=focus_scope,
        ),
    )
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "capsule": capsule_name,
        "workspace": str(project_root(root)),
        "stage": stage,
        "status": status,
        "model": model,
        "keep": keep,
        "delete": delete,
        "proposed_contracts": proposals,
    }
    if project_id:
        entry["project_id"] = project_id
    if focus_scope:
        entry["focus_scope"] = focus_scope
    append_policy_ledger_entry(root, capsule_name, entry, cinema_dir=cinema_dir)
    return entry
