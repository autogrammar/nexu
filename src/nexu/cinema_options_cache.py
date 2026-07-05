"""File cache for Cinema /iterate goal options (alt_a/b/c)."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

_ALT_FILES = ("alt_a.html", "alt_b.html", "alt_c.html")


def goal_slug(goal: str, *, max_len: int = 32) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", str(goal or "").lower()).strip("_")
    return (slug[:max_len] if slug else "none").strip("_") or "none"


def _digest(value: str) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()[:16]


def _is_noop_ledger_entry(entry: Any) -> bool:
    """True for audit-only entries that carry no keep/delete/proposal signal.

    Scope- or hint-only iterations append a ledger entry purely for audit
    trail purposes (see server.py.tmpl), with empty keep/delete and no
    proposed contracts. Such entries must not affect the options cache key,
    or every one of them would invalidate the cache for the very next
    identical request, defeating the cache entirely.
    """
    if not isinstance(entry, dict):
        return False
    return not (entry.get("keep") or entry.get("delete") or entry.get("proposed_contracts"))


def options_cache_key(
    *,
    stage_html: str,
    ledger: Any,
    focus_scope: str,
    goal: str,
    keep_els: list[str] | None = None,
    delete_els: list[str] | None = None,
) -> str:
    meaningful_ledger = [
        entry for entry in (ledger or []) if not _is_noop_ledger_entry(entry)
    ]
    ledger_blob = json.dumps(meaningful_ledger, sort_keys=True, ensure_ascii=False, default=str)
    parts = [
        _digest(stage_html),
        _digest(ledger_blob),
        (focus_scope or "functions").strip().lower(),
        goal_slug(goal),
        ",".join(sorted(str(x) for x in (keep_els or []))),
        ",".join(sorted(str(x) for x in (delete_els or []))),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def options_cache_dir(cinema_dir: Path) -> Path:
    return Path(cinema_dir) / "cache" / "options"


def read_options_cache(cache_root: Path, key: str) -> dict[str, Any] | None:
    entry_dir = cache_root / key
    meta_path = entry_dir / "meta.json"
    if not meta_path.is_file():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    files: dict[str, str] = {}
    for name in _ALT_FILES:
        path = entry_dir / name
        if not path.is_file():
            return None
        files[name] = path.read_text(encoding="utf-8")
    labels = meta.get("labels")
    if not isinstance(labels, list) or len(labels) != 3:
        labels = list(_ALT_FILES)
    return {
        "key": key,
        "files": files,
        "labels": [str(item) for item in labels],
        "source": str(meta.get("source") or "cache"),
        "meta": meta,
    }


def write_options_cache(
    cache_root: Path,
    key: str,
    *,
    files: dict[str, str],
    labels: list[str],
    source: str,
    focus_scope: str = "",
    goal: str = "",
) -> None:
    entry_dir = cache_root / key
    if entry_dir.exists():
        shutil.rmtree(entry_dir, ignore_errors=True)
    entry_dir.mkdir(parents=True, exist_ok=True)
    for name in _ALT_FILES:
        html = files.get(name)
        if html:
            (entry_dir / name).write_text(str(html), encoding="utf-8")
    meta = {
        "key": key,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "focus_scope": (focus_scope or "functions").strip().lower(),
        "goal_slug": goal_slug(goal),
        "labels": list(labels),
    }
    (entry_dir / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def apply_options_cache(cinema_dir: Path, cached: dict[str, Any]) -> list[str]:
    labels = list(cached.get("labels") or [])
    files = cached.get("files") or {}
    label_by_file = {}
    for index, name in enumerate(_ALT_FILES):
        if index < len(labels):
            label_by_file[name] = labels[index]
    written: list[str] = []
    for name in _ALT_FILES:
        html = files.get(name)
        if not html:
            continue
        (Path(cinema_dir) / name).write_text(str(html), encoding="utf-8")
        written.append(label_by_file.get(name, name))
    return written


def invalidate_options_cache(cache_root: Path) -> None:
    if cache_root.is_dir():
        shutil.rmtree(cache_root, ignore_errors=True)
