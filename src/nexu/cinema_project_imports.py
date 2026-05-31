"""Import arbitrary projects into Cinema and migrate them to Markpact first."""
# ruff: noqa: E501

from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .cinema_policy import ensure_option_previews_from_stages
from .cinema_projects import ACTIVE_PROJECT_FILE
from .cinema_scripts import write_cinema_inject_files

IMPORTS_DIR = "imported_projects"
MAX_EMBED_FILES = 18
MAX_FILE_BYTES = 60_000
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__"}


def _slug(value: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-").lower()
    return safe[:64] or "imported-project"


def _imports_root(cinema_dir: Path) -> Path:
    root = cinema_dir / IMPORTS_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root


def _project_dir(cinema_dir: Path, project_id: str) -> Path:
    return _imports_root(cinema_dir) / project_id


def _safe_extract_zip(zip_path: Path, target: Path) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            dest = (target / info.filename).resolve()
            if not str(dest).startswith(str(target.resolve())):
                raise ValueError(f"unsafe zip path: {info.filename}")
        zf.extractall(target)


def _iter_project_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        files.append(path)
    return sorted(files)


def _detect_run_notes(root: Path) -> list[str]:
    notes: list[str] = []
    if (root / "package.json").exists():
        notes.append("npm install")
        notes.append("npm run dev")
    if (root / "pyproject.toml").exists():
        notes.append("uv sync")
        notes.append("uv run python -m pytest")
    if (root / "requirements.txt").exists():
        notes.append("python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt")
    if not notes:
        notes.append("inspect project files and define the first Markpact run block")
    return notes


def _read_text_for_markpact(path: Path) -> str | None:
    if path.stat().st_size > MAX_FILE_BYTES:
        return None
    try:
        data = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    return data


def _build_markpact_migration(root: Path, *, project_id: str, title: str, source: str) -> str:
    files = _iter_project_files(root)
    tree = "\n".join(f"- `{p.relative_to(root)}`" for p in files[:80])
    run_notes = "\n".join(f"# {line}" for line in _detect_run_notes(root))
    meta = {
        "project_id": project_id,
        "title": title,
        "source": source,
        "migrated_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
    }
    embedded: list[str] = []
    for path in files[:MAX_EMBED_FILES]:
        text = _read_text_for_markpact(path)
        if text is None:
            continue
        rel = str(path.relative_to(root))
        fence = "````" if "```" in text else "```"
        embedded.append(f"{fence}text markpact:file path={rel}\n{text}\n{fence}")
    embedded_block = "\n\n".join(embedded) or "_No small text files embedded yet._"
    return f"""# {title} — Markpact migration

This project was imported into Nexu. The first required step is Markpact migration:
turn the source tree into an explicit, runnable README contract before visual iterations.

```json markpact:file path=nexu-import-meta.json
{json.dumps(meta, indent=2, ensure_ascii=False)}
```

## Source Tree

{tree or "- (empty project)"}

## Suggested First Run

```bash markpact:run
{run_notes}
```

## Imported Files

{embedded_block}
"""


def _stage_html(meta: dict[str, Any], *, variant: str) -> str:
    project_id = str(meta["id"])
    title = str(meta["title"])
    count = int(meta.get("file_count") or 0)
    source = str(meta.get("source") or "")
    markpact = str(meta.get("markpact_path") or "")
    focus = {
        "stage0": ("Migration baseline", "Inspect imported project and Markpact README"),
        "stage1": ("Contract shape", "Add run/deps/file blocks and project intent"),
        "stage2": ("Executable app", "Promote runnable Markpact service"),
    }.get(variant, ("Migration baseline", "Inspect imported project"))
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{title} — {focus[0]}</title>
  <style>
    body {{ margin:0; min-height:100vh; background:#0b1020; color:#e2e8f0; font-family:Arial,sans-serif; }}
    .app-shell {{ display:grid; grid-template-columns:220px 1fr; gap:18px; padding:26px; min-height:100vh; }}
    aside, .panel, .card {{ background:#111827; border:1px solid rgba(148,163,184,.22); border-radius:8px; }}
    aside {{ padding:18px; }}
    main {{ display:grid; gap:16px; align-content:start; }}
    h1 {{ margin:0; color:#38bdf8; }}
    .grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }}
    .card {{ padding:16px; }}
    .card strong {{ display:block; color:#22c55e; font-size:1.5rem; margin-top:8px; }}
    .panel {{ padding:18px; }}
    code {{ color:#a5b4fc; word-break:break-all; }}
    .badge {{ display:inline-block; padding:6px 10px; border-radius:999px; background:#1e293b; color:#fbbf24; }}
  </style>
</head>
<body>
  <div class="app-shell" data-project="{project_id}" data-kind="imported">
    <aside class="nexu-selectable" data-nexu-target="markpact-nav">
      <h2>Markpact migration</h2>
      <p class="badge">{focus[0]}</p>
      <p>{focus[1]}</p>
    </aside>
    <main>
      <section class="panel nexu-selectable" id="btn-import-summary" data-nexu-target="import-summary">
        <h1>{title}</h1>
        <p>Imported source must become a Markpact contract before Nexu visual iterations.</p>
      </section>
      <section class="grid">
        <div class="card nexu-selectable" id="btn-files" data-nexu-target="files"><span>Files</span><strong>{count}</strong></div>
        <div class="card nexu-selectable" id="btn-source" data-nexu-target="source"><span>Source</span><strong>{source[:18] or "local"}</strong></div>
        <div class="card nexu-selectable" id="btn-markpact" data-nexu-target="markpact"><span>Markpact</span><strong>README</strong></div>
      </section>
      <section class="panel nexu-selectable" id="btn-markpact-path" data-nexu-target="markpact-path">
        <h2>First artifact</h2>
        <code>{markpact}</code>
      </section>
    </main>
  </div>
</body>
</html>"""


def _activate_imported(cinema_dir: Path, meta: dict[str, Any]) -> dict[str, Any]:
    for name, variant in (("stage0.html", "stage0"), ("stage1.html", "stage1"), ("stage2.html", "stage2")):
        (cinema_dir / name).write_text(_stage_html(meta, variant=variant), encoding="utf-8")
    options_sync = ensure_option_previews_from_stages(cinema_dir)
    write_cinema_inject_files(cinema_dir)
    active = {
        "id": meta["id"],
        "title": meta["title"],
        "subtitle": "Markpact migration workspace",
        "domain": "import",
        "kind": "imported",
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "source": meta.get("source", ""),
        "markpact_path": meta.get("markpact_path", ""),
    }
    (cinema_dir / ACTIVE_PROJECT_FILE).write_text(
        json.dumps(active, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {
        "status": "project_imported",
        "project": {
            **active,
            "tags": ["imported", "markpact"],
            "emoji": "📦",
            "source_paths": [],
        },
        "files_copied": ["stage0.html", "stage1.html", "stage2.html", "alt_a.html", "alt_b.html", "alt_c.html"],
        "options_sync": options_sync,
    }


def import_git_project(cinema_dir: Path, git_url: str) -> dict[str, Any]:
    source = git_url.strip()
    if not source:
        return {"error": "git_url required"}
    project_id = "git-" + _slug(Path(source.rstrip("/")).stem or source)
    dest = _project_dir(cinema_dir, project_id)
    if dest.exists():
        shutil.rmtree(dest)
    source_dir = dest / "source"
    dest.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["git", "clone", "--depth", "1", source, str(source_dir)],
        text=True,
        capture_output=True,
        timeout=120,
    )
    if proc.returncode != 0:
        return {"error": (proc.stderr or proc.stdout or "git clone failed").strip()[:500]}
    return _finish_import(cinema_dir, project_id=project_id, source_dir=source_dir, source=source)


def import_zip_project(cinema_dir: Path, filename: str, content_base64: str) -> dict[str, Any]:
    safe_name = Path(filename or "project.zip").name
    project_id = "zip-" + _slug(Path(safe_name).stem)
    dest = _project_dir(cinema_dir, project_id)
    if dest.exists():
        shutil.rmtree(dest)
    source_dir = dest / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest / safe_name
    zip_path.write_bytes(base64.b64decode(content_base64))
    _safe_extract_zip(zip_path, source_dir)
    return _finish_import(cinema_dir, project_id=project_id, source_dir=source_dir, source=safe_name)


def _finish_import(cinema_dir: Path, *, project_id: str, source_dir: Path, source: str) -> dict[str, Any]:
    title = project_id.removeprefix("git-").removeprefix("zip-").replace("-", " ").title()
    files = _iter_project_files(source_dir)
    markpact = _build_markpact_migration(source_dir, project_id=project_id, title=title, source=source)
    markpact_path = _project_dir(cinema_dir, project_id) / "README.markpact.md"
    markpact_path.write_text(markpact, encoding="utf-8")
    meta = {
        "id": project_id,
        "title": title,
        "source": source,
        "source_dir": str(source_dir),
        "markpact_path": str(markpact_path),
        "file_count": len(files),
    }
    (_project_dir(cinema_dir, project_id) / "project.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return _activate_imported(cinema_dir, meta)


def list_imported_projects(cinema_dir: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    root = _imports_root(cinema_dir)
    for path in sorted(root.glob("*/project.json")):
        try:
            meta = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        out.append(
            {
                "id": meta.get("id"),
                "title": meta.get("title"),
                "subtitle": "Imported project — Markpact migration",
                "domain": "import",
                "kind": "imported",
                "tags": ["imported", "markpact"],
                "emoji": "📦",
                "source_paths": [],
            }
        )
    return [item for item in out if item.get("id")]
