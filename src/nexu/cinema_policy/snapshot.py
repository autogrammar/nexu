"""Cinema policy snapshot/ledger paths, manifest targets, and ledger-to-manifest merge."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from ..paths import capsule_dir, project_root

ManifestTarget = Literal["project", "capsule", "both"]

_VALID_TARGETS = frozenset({"project", "capsule", "both"})


def _intract_manifest_path(raw: str | None) -> Path | None:
    """Return path only when it points at a readable intract YAML manifest."""
    if not raw:
        return None
    path = Path(str(raw))
    if path.suffix.lower() not in {".yaml", ".yml"}:
        return None
    return path if path.is_file() else None


def normalize_manifest_target(target: str) -> ManifestTarget:
    normalized = (target or "both").strip().lower()
    if normalized in _VALID_TARGETS:
        return normalized  # type: ignore[return-value]
    return "both"


def cinema_model_label(root: Path) -> str:
    from ..config import load_config, load_env_files

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
    project_manifest = _intract_manifest_path(project.get("intract_path"))
    capsule_manifest = _intract_manifest_path(capsule.get("intract_path"))
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
        if isinstance(project, dict):
            project_manifest = _intract_manifest_path(project.get("intract_path"))
        if isinstance(capsule, dict):
            capsule_manifest = _intract_manifest_path(capsule.get("intract_path"))

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
            "has_intract_yaml": False,
            "intract_path": None,
            "markpact_path": markpact_path or None,
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
    from ..cinema import build_intract_policy_snapshot
    from ..cinema_projects import load_active_project

    snapshot = build_intract_policy_snapshot(root, capsule_name)
    active = load_active_project(cinema_dir)
    if active:
        snapshot["active_example_project"] = active
    (cinema_dir / "intract_policy.json").write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
