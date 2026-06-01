"""Cinema policy ledger, manifest merge, and capsule verification."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from repatch import (
    OPTION_PREVIEW_FILES as _REPATCH_OPTION_PREVIEW_FILES,
    enforce_deletes_on_option_previews as _repatch_enforce_deletes_on_option_previews,
    html_files_distinct as _repatch_html_files_distinct,
    replace_html_title as _repatch_replace_html_title,
    sync_option_previews_from_workspace as _repatch_sync_option_previews_from_workspace,
)

from .cinema_scripts import finalize_cinema_html
from .paths import capsule_dir, project_root
from .verify import verify_capsule

_OPTION_PREVIEW_FILES = _REPATCH_OPTION_PREVIEW_FILES

ManifestTarget = Literal["project", "capsule", "both"]

_VALID_TARGETS = frozenset({"project", "capsule", "both"})


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


def _ledger_entry_matches_scope(entry: dict[str, Any], *, focus_scope: str | None) -> bool:
    """Scope-specific marks apply only within the same #scope iteration."""
    entry_scope = str(entry.get("focus_scope") or "").strip().lower()
    active_scope = str(focus_scope or "").strip().lower()
    if not active_scope:
        return True
    if not entry_scope:
        return False
    return entry_scope == active_scope


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


def refresh_imported_policy_snapshot(
    cinema_dir: Path,
    meta: dict[str, Any],
    active: dict[str, Any],
) -> None:
    """Rebuild intract_policy.json for imported projects without calculator baselines."""
    cinema_dir = Path(cinema_dir)
    project_id = str(meta.get("id") or "")
    import_kind = str(meta.get("import_kind") or "")
    markpact_path = str(meta.get("markpact_path") or "")
    template_id = f"cinema.{project_id}.S0.ui.template"
    snapshot = {
        "version": "intract.policy.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": {
            "root": str(cinema_dir),
            "name": project_id,
            "has_intract_yaml": bool(markpact_path),
            "intract_path": markpact_path or None,
        },
        "capsule": {
            "name": project_id,
            "exists": True,
            "path": str(cinema_dir / "imported_projects" / project_id),
            "is_calculator": False,
            "is_imported": True,
            "import_kind": import_kind,
        },
        "baseline_contracts": {
            "project": [],
            "capsule": [
                {
                    "id": template_id,
                    "scope": "capsule",
                    "intent": "layout:imported_web",
                    "priority": 2,
                    "domain": "ui",
                    "meaning": (
                        "Imported web UI snapshot; evolve palette, typography, and layout "
                        "without replacing the page information architecture."
                    ),
                    "source": "nexu.cinema.imported",
                }
            ],
        },
        "active_example_project": active,
    }
    (cinema_dir / "intract_policy.json").write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _replace_html_title(html: str, title: str) -> str:
    return _repatch_replace_html_title(html, title)


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


def reset_cinema_policy_ledger(cinema_dir: Path) -> None:
    """Clear UI marks/goals from a prior example project in this cinema directory."""
    cinema_dir = Path(cinema_dir)
    (cinema_dir / "intract_policy_ledger.json").write_text("[]\n", encoding="utf-8")


def refresh_cinema_policy_snapshot(
    cinema_dir: Path,
    root: Path,
    capsule_name: str,
) -> None:
    """Rebuild intract_policy.json and attach the active example project metadata."""
    from .cinema import build_intract_policy_snapshot
    from .cinema_projects import load_active_project

    snapshot = build_intract_policy_snapshot(root, capsule_name)
    active = load_active_project(cinema_dir)
    if active:
        snapshot["active_example_project"] = active
    (cinema_dir / "intract_policy.json").write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


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
        from .cinema_projects import load_active_project

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
                    f"priority:3 domain:{domain} effect:ui_change "
                    f"forbid:destructive_write,secret_leak "
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
    from .cinema_goal_contracts import propose_goal_extension_contracts

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
