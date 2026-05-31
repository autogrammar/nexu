"""Cinema UI + policy checkpoints: save, list, restore."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .cinema_policy import apply_ledger_from_cinema, cinema_dir_for
from .paths import project_root

_CHECKPOINT_FILES = (
    "stage0.html",
    "stage1.html",
    "stage2.html",
    "alt_a.html",
    "alt_b.html",
    "alt_c.html",
)


def history_dir(cinema_dir: Path) -> Path:
    return cinema_dir / "history"


def history_index_path(cinema_dir: Path) -> Path:
    return history_dir(cinema_dir) / "index.json"


def _load_index(cinema_dir: Path) -> list[dict[str, Any]]:
    path = history_index_path(cinema_dir)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def _write_index(cinema_dir: Path, entries: list[dict[str, Any]]) -> None:
    hdir = history_dir(cinema_dir)
    hdir.mkdir(parents=True, exist_ok=True)
    history_index_path(cinema_dir).write_text(
        json.dumps(entries, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _copy_checkpoint_files(cinema_dir: Path, dest: Path) -> list[str]:
    copied: list[str] = []
    for name in _CHECKPOINT_FILES:
        src = cinema_dir / name
        if src.exists():
            shutil.copy2(src, dest / name)
            copied.append(name)
    return copied


def _ledger_snapshot(cinema_dir: Path) -> list[Any]:
    path = cinema_dir / "intract_policy_ledger.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def _build_label(
    *,
    stage: int,
    status: str,
    action: str,
    keep: list[str],
    delete: list[str],
    extra: str = "",
) -> str:
    parts = [f"S{stage}", action, status.replace("_", " ")]
    if delete:
        parts.append(f"−{', '.join(delete)}")
    if keep:
        parts.append(f"+{', '.join(keep)}")
    if extra:
        parts.append(extra)
    return " · ".join(parts)


def save_history_checkpoint(
    cinema_dir: Path,
    *,
    action: str,
    stage: int,
    status: str,
    keep: list[str] | None = None,
    delete: list[str] | None = None,
    label: str = "",
    extra: str = "",
) -> dict[str, Any]:
    """Persist current cinema HTML files and policy ledger."""
    cinema_dir = Path(cinema_dir)
    keep = list(keep or [])
    delete = list(delete or [])
    index = _load_index(cinema_dir)
    checkpoint_id = f"cp_{len(index):04d}"
    cp_dir = history_dir(cinema_dir) / checkpoint_id
    cp_dir.mkdir(parents=True, exist_ok=True)

    files = _copy_checkpoint_files(cinema_dir, cp_dir)
    ledger = _ledger_snapshot(cinema_dir)
    (cp_dir / "ledger.json").write_text(
        json.dumps(ledger, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    ts = datetime.now(timezone.utc).isoformat()
    summary = {
        "id": checkpoint_id,
        "timestamp": ts,
        "label": label or _build_label(
            stage=stage, status=status, action=action, keep=keep, delete=delete, extra=extra
        ),
        "action": action,
        "stage": stage,
        "status": status,
        "keep": keep,
        "delete": delete,
        "files": files,
        "ledger_length": len(ledger),
    }
    (cp_dir / "meta.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    index.append(summary)
    _write_index(cinema_dir, index)
    return summary


def list_history_checkpoints(cinema_dir: Path) -> list[dict[str, Any]]:
    return list(reversed(_load_index(cinema_dir)))


def restore_history_checkpoint(
    root: Path,
    capsule_name: str,
    checkpoint_id: str,
    *,
    apply_manifest: bool = True,
    manifest_target: str = "both",
) -> dict[str, Any]:
    """Restore HTML + ledger from a checkpoint; optionally merge ledger into manifests."""
    root = project_root(root)
    cinema_dir = cinema_dir_for(root, capsule_name)
    cp_dir = history_dir(cinema_dir) / checkpoint_id
    meta_path = cp_dir / "meta.json"
    if not meta_path.exists():
        return {"error": f"checkpoint not found: {checkpoint_id}"}

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    restored_files: list[str] = []
    for name in meta.get("files") or _CHECKPOINT_FILES:
        src = cp_dir / name
        if src.exists():
            shutil.copy2(src, cinema_dir / name)
            restored_files.append(name)

    ledger_path = cp_dir / "ledger.json"
    if ledger_path.exists():
        ledger_text = ledger_path.read_text(encoding="utf-8")
        (cinema_dir / "intract_policy_ledger.json").write_text(ledger_text, encoding="utf-8")
        ledger_len = len(json.loads(ledger_text))
    else:
        ledger_len = 0

    _refresh_policy_snapshot(cinema_dir, root, capsule_name)

    manifest_result: dict[str, Any] | None = None
    if apply_manifest and ledger_len > 0:
        manifest_result = apply_ledger_from_cinema(
            root,
            capsule_name,
            target=manifest_target,  # type: ignore[arg-type]
            dry_run=False,
            only_evolved=True,
        )

    return {
        "status": "restored",
        "checkpoint_id": checkpoint_id,
        "label": meta.get("label"),
        "restored_files": restored_files,
        "ledger_length": ledger_len,
        "manifest": manifest_result,
    }


def _refresh_policy_snapshot(cinema_dir: Path, root: Path, capsule_name: str) -> None:
    from .cinema import write_intract_policy_files

    write_intract_policy_files(cinema_dir, root, capsule_name)


def ensure_initial_checkpoint(cinema_dir: Path) -> dict[str, Any] | None:
    """Save baseline snapshot once when history is empty."""
    if _load_index(cinema_dir):
        return None
    ledger_len = len(_ledger_snapshot(cinema_dir))
    label = (
        "Initial baseline"
        if ledger_len == 0
        else f"Snapshot at cinema restart (ledger had {ledger_len} entries)"
    )
    return save_history_checkpoint(
        cinema_dir,
        action="baseline",
        stage=0,
        status="initial",
        label=label,
    )


def ledger_archive_for_display(cinema_dir: Path) -> list[dict[str, Any]]:
    """Ledger iterations without HTML snapshots (read-only in history UI)."""
    ledger = _ledger_snapshot(cinema_dir)
    archive: list[dict[str, Any]] = []
    for i, entry in enumerate(reversed(ledger)):
        if not isinstance(entry, dict):
            continue
        delete = entry.get("delete") or []
        keep = entry.get("keep") or []
        archive.append(
            {
                "id": f"ledger_{len(ledger) - 1 - i}",
                "restorable": False,
                "timestamp": entry.get("timestamp", ""),
                "label": _build_label(
                    stage=int(entry.get("stage", 0)),
                    status=str(entry.get("status", "ledger")),
                    action="ledger",
                    keep=list(keep),
                    delete=list(delete),
                ),
                "ledger_length": i + 1,
            }
        )
    return archive
