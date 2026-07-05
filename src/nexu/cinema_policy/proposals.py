"""Building and normalizing @intract.v1 UI-delta contract proposals."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .intract_validation import ensure_intract_on_path


def propose_ui_delta_contract_dicts(
    *,
    stage: int,
    keep: list[str],
    delete: list[str],
    capsule_name: str,
    domain: str = "calculator",
    project_id: str = "",
    focus_scope: str = "",
) -> list[dict[str, Any]]:
    contract_subject = (project_id or capsule_name).strip()
    contract_scope = (focus_scope or "ui").strip().lower()
    if not project_id and not focus_scope and ensure_intract_on_path(Path(".")):
        try:
            from intract.proposals import propose_ui_delta_contract_dicts as _propose

            return _propose(
                stage=stage,
                keep=keep,
                delete=delete,
                capsule=capsule_name,
                domain=domain,
            )
        except Exception:
            pass

    proposals: list[dict[str, Any]] = []
    for element_id in delete:
        contract_id = f"cinema.{contract_subject}.S{stage}.{contract_scope}.remove.{element_id}"
        proposals.append(
            {
                "id": contract_id,
                "kind": "delete",
                "element": element_id,
                "line": (
                    f"@intract.v1 id:{contract_id} scope:{contract_scope} "
                    f"intent:ui:{contract_scope}:remove:{element_id} "
                    f"priority:3 domain:{domain} effect:ui_change "
                    f"forbid:destructive_write,secret_leak "
                    f"require:human_review validate:no_forbidden_effect "
                    f'project:{contract_subject} meaning:"Cinema S{stage} removed #{element_id} in #{contract_scope}"'
                ),
            }
        )
    for element_id in keep:
        contract_id = f"cinema.{contract_subject}.S{stage}.{contract_scope}.keep.{element_id}"
        proposals.append(
            {
                "id": contract_id,
                "kind": "keep",
                "element": element_id,
                "line": (
                    f"@intract.v1 id:{contract_id} scope:{contract_scope} "
                    f"intent:ui:{contract_scope}:keep:{element_id} "
                    f"priority:2 domain:{domain} effect:ui_change validate:input_presence "
                    f'project:{contract_subject} meaning:"Cinema S{stage} kept #{element_id} in #{contract_scope}"'
                ),
            }
        )
    return proposals


def _proposal_kind_and_element(proposal: dict[str, Any]) -> tuple[str, str]:
    kind = str(proposal.get("kind") or "")
    element = str(proposal.get("element") or "")
    if kind and element:
        return kind, element
    intent = str(proposal.get("intent") or "")
    if ":remove:" in intent:
        maybe = intent.rsplit(":", 1)[-1]
        if maybe:
            return "delete", maybe
    if ":keep:" in intent:
        maybe = intent.rsplit(":", 1)[-1]
        if maybe:
            return "keep", maybe
    return (kind or "change"), (element or "unknown")


def normalize_proposals_for_ledger(
    stage: int, capsule_name: str, proposals: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        kind, element = _proposal_kind_and_element(proposal)
        item = dict(proposal)
        item.setdefault("kind", kind)
        item.setdefault("element", element)
        item.setdefault("based_on", f"cinema.{capsule_name}.S{stage}.ui.template")
        action = "remove" if kind == "delete" else ("keep" if kind == "keep" else kind)
        base_id = str(item.get("based_on"))
        delta = f"Δ {action} #{element} based_on={base_id}"
        if item.get("supersedes"):
            delta += f" supersedes={item['supersedes']}"
        item.setdefault("delta_text", delta)
        normalized.append(item)
    return normalized
