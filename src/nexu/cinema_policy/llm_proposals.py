"""LLM-driven contract proposals for a cinema stage."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..paths import project_root
from .intract_validation import ensure_intract_on_path
from .ledger import append_policy_ledger_entry
from .snapshot import cinema_dir_for


def propose_llm_for_stage(
    root: Path,
    capsule_name: str,
    stage: int,
    goal: str,
    *,
    model: str,
) -> dict[str, Any]:
    stage_file = cinema_dir_for(root, capsule_name) / f"stage{stage}.html"
    if not stage_file.exists():
        return {"error": f"stage file not found: {stage_file.name}"}
    if not ensure_intract_on_path(root):
        return {"error": "intract package not found on PYTHONPATH"}

    try:
        from intract.propose_llm import propose_contracts_llm
    except ImportError as exc:
        return {"error": f"intract propose_llm unavailable: {exc}"}

    try:
        html = stage_file.read_text(encoding="utf-8")
        proposals = propose_contracts_llm(
            html,
            goal=goal or "Cinema UI evolution",
            fragment_name=stage_file.name,
        )
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "capsule": capsule_name,
            "workspace": str(project_root(root)),
            "stage": stage,
            "status": "proposed_by_llm",
            "model": model,
            "keep": [],
            "delete": [],
            "proposed_contracts": [item.to_dict() for item in proposals],
        }
        append_policy_ledger_entry(root, capsule_name, entry)
        return {
            "status": "proposed_by_llm",
            "count": len(proposals),
            "proposals": [item.to_dict() for item in proposals],
        }
    except Exception as exc:
        return {"error": str(exc)}
