"""Cinema policy ledger, manifest merge, and capsule verification (shared with generated server hooks)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from .paths import capsule_dir, project_root
from .verify import verify_capsule

ManifestTarget = Literal["project", "capsule", "both"]

_VALID_TARGETS = frozenset({"project", "capsule", "both"})


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
    if pending_goal or (has_hints and delete_count == 0):
        return "goal_options"
    if delete_count > 0:
        return "active_workspace"
    if has_hints:
        return "goal_options"
    if keep_count > 0:
        return "active_workspace"
    return "none"


def normalize_manifest_target(target: str) -> ManifestTarget:
    normalized = (target or "both").strip().lower()
    if normalized in _VALID_TARGETS:
        return normalized  # type: ignore[return-value]
    return "both"


def cinema_model_label(root: Path) -> str:
    from .config import load_config, load_env_files

    load_env_files(root)
    model = load_config(root).llm.model
    return model.rsplit("/", 1)[-1] if model else "default"


def cinema_dir_for(root: Path, capsule_name: str) -> Path:
    return capsule_dir(project_root(root), capsule_name) / "cinema"


def policy_snapshot_path(root: Path, capsule_name: str) -> Path:
    return cinema_dir_for(root, capsule_name) / "intract_policy.json"


def policy_ledger_path(root: Path, capsule_name: str) -> Path:
    return cinema_dir_for(root, capsule_name) / "intract_policy_ledger.json"


def load_policy_snapshot(root: Path, capsule_name: str) -> dict[str, Any]:
    path = policy_snapshot_path(root, capsule_name)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_paths_from_snapshot(
    snapshot: dict[str, Any],
    root: Path,
    capsule_name: str,
    target: ManifestTarget,
) -> list[tuple[str, Path]]:
    from intract.manifest_ops import resolve_manifest_paths

    project = snapshot.get("project", {}) if isinstance(snapshot, dict) else {}
    capsule = snapshot.get("capsule", {}) if isinstance(snapshot, dict) else {}
    project_manifest = Path(project["intract_path"]) if project.get("intract_path") else None
    capsule_manifest = Path(capsule["intract_path"]) if capsule.get("intract_path") else None
    return resolve_manifest_paths(
        workspace_root=project_root(root),
        capsule_name=capsule_name,
        target=target,
        project_manifest=project_manifest,
        capsule_manifest=capsule_manifest,
    )


def apply_ledger_from_cinema(
    root: Path,
    capsule_name: str,
    *,
    target: ManifestTarget = "both",
    dry_run: bool = False,
    only_evolved: bool = True,
) -> dict[str, Any]:
    """Merge cinema policy ledger into project and/or capsule intract.yaml."""
    root = project_root(root)
    ledger_path = policy_ledger_path(root, capsule_name)
    if not ledger_path.exists():
        return {"error": f"ledger not found: {ledger_path}"}

    try:
        from intract.manifest_ops import apply_ledger_to_manifests
    except ImportError as exc:
        return {"error": f"intract package required: {exc}"}

    target = normalize_manifest_target(target)
    snapshot = load_policy_snapshot(root, capsule_name)
    project_manifest = None
    capsule_manifest = None
    if snapshot:
        project = snapshot.get("project", {})
        capsule = snapshot.get("capsule", {})
        if isinstance(project, dict) and project.get("intract_path"):
            project_manifest = Path(str(project["intract_path"]))
        if isinstance(capsule, dict) and capsule.get("intract_path"):
            capsule_manifest = Path(str(capsule["intract_path"]))

    batch = apply_ledger_to_manifests(
        workspace_root=root,
        capsule_name=capsule_name,
        ledger_path=ledger_path,
        target=target,
        dry_run=dry_run,
        only_evolved=only_evolved,
        project_manifest=project_manifest,
        capsule_manifest=capsule_manifest,
    )
    return batch.to_dict()


def ensure_intract_on_path(root: Path) -> bool:
    """Locate sibling semcod/intract and prepend its src to sys.path."""
    curr = project_root(root)
    for _ in range(6):
        for candidate in (curr / "intract" / "src", curr.parent / "intract" / "src"):
            if candidate.exists():
                path = str(candidate)
                if path not in sys.path:
                    sys.path.insert(0, path)
                return True
        curr = curr.parent
    return False


def propose_ui_delta_contract_dicts(
    *,
    stage: int,
    keep: list[str],
    delete: list[str],
    capsule_name: str,
    domain: str = "calculator",
) -> list[dict[str, Any]]:
    if ensure_intract_on_path(Path(".")):
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
        contract_id = f"cinema.{capsule_name}.S{stage}.ui.remove.{element_id}"
        proposals.append(
            {
                "id": contract_id,
                "kind": "delete",
                "element": element_id,
                "line": (
                    f"@intract.v1 id:{contract_id} scope:ui intent:ui:remove:{element_id} "
                    f"priority:3 domain:{domain} effect:ui_change forbid:destructive_write,secret_leak "
                    f"require:human_review validate:no_forbidden_effect "
                    f'meaning:"Cinema S{stage} removed #{element_id}"'
                ),
            }
        )
    for element_id in keep:
        contract_id = f"cinema.{capsule_name}.S{stage}.ui.keep.{element_id}"
        proposals.append(
            {
                "id": contract_id,
                "kind": "keep",
                "element": element_id,
                "line": (
                    f"@intract.v1 id:{contract_id} scope:ui intent:ui:keep:{element_id} "
                    f"priority:2 domain:{domain} effect:ui_change validate:input_presence "
                    f'meaning:"Cinema S{stage} kept #{element_id}"'
                ),
            }
        )
    return proposals


def append_policy_ledger_entry(root: Path, capsule_name: str, entry: dict[str, Any]) -> None:
    ledger_path = policy_ledger_path(root, capsule_name)
    ledger: list[Any] = []
    if ledger_path.exists():
        data = json.loads(ledger_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            ledger = data
    ledger.append(entry)
    ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False), encoding="utf-8")


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
    append_policy_ledger_entry(root, capsule_name, entry)
    return entry


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


def validate_intract_artifact(
    artifact: str,
    proposals: list[dict[str, Any]],
    *,
    filename: str,
    root: Path | None = None,
) -> dict[str, Any] | None:
    if not artifact or not proposals:
        return None
    if root is not None and not ensure_intract_on_path(root):
        return {"status": "unavailable", "score": 0.0, "issues": []}
    if root is None and not ensure_intract_on_path(Path(".")):
        return {"status": "unavailable", "score": 0.0, "issues": []}
    try:
        from intract.validate_snippet import validate_artifact_with_proposals

        return validate_artifact_with_proposals(artifact, proposals, filename=filename)
    except Exception as exc:
        return {
            "status": "error",
            "score": 0.0,
            "issues": [{"rule": "intract", "message": str(exc), "severity": "error"}],
        }


def verify_capsule_workspace(root: Path, capsule_name: str) -> dict[str, Any]:
    """Run nexu capsule verify and return JSON-serializable report."""
    try:
        report = verify_capsule(project_root(root), capsule_name)
        return report.to_dict()
    except Exception as exc:
        return {
            "capsule": capsule_name,
            "status": "error",
            "score": 0.0,
            "findings": [
                {
                    "code": "verify_error",
                    "status": "fail",
                    "message": str(exc),
                }
            ],
        }
