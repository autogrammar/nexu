"""Build portable Markpact README exports from Nexu workspace HTML."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_CONTEXT_INCLUDE_NAMES = {
    "nexu.yaml",
    "intract.yaml",
    "pyproject.toml",
    "package.json",
    "requirements.txt",
    "README.md",
}
_CONTEXT_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".json", ".yaml", ".yml"}


def _escape_markdown_fence(text: str, fence: str = "```") -> str:
    """Avoid closing a fenced block early if the HTML contains ```."""
    if fence not in text:
        return text
    return text.replace(fence, fence + "\\")


def _language_for(path: Path) -> str:
    return {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".jsx": "jsx",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".txt": "text",
        ".md": "markdown",
    }.get(path.suffix.lower(), "text")


def _project_context_block(workspace_root: Path | None, *, max_chars: int = 30000) -> str:
    if workspace_root is None or not workspace_root.exists():
        return "(workspace context not available)"
    root = workspace_root.resolve()
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        parts = set(rel.parts)
        if parts & {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules"}:
            continue
        if path.name in _CONTEXT_INCLUDE_NAMES or path.suffix.lower() in _CONTEXT_SUFFIXES:
            files.append(path)
    files = sorted(
        files,
        key=lambda p: (len(p.relative_to(root).parts), str(p.relative_to(root))),
    )[:80]
    tree = "\n".join(f"- {p.relative_to(root)}" for p in files) or "- (no context files found)"
    chunks = [f"### File tree\n\n{tree}\n"]
    used = len(chunks[0])
    for path in files:
        rel = path.relative_to(root)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        snippet = text[:4000]
        block = (
            f"\n### `{rel}`\n\n"
            f"```{_language_for(path)} markpact:file path=project/{rel}\n"
            f"{_escape_markdown_fence(snippet)}"
            + ("\n<!-- file truncated -->" if len(text) > len(snippet) else "")
            + "\n```\n"
        )
        if used + len(block) > max_chars:
            chunks.append("\n<!-- project context truncated -->\n")
            break
        chunks.append(block)
        used += len(block)
    return "".join(chunks)


def build_markpact_readme(
    cinema_dir: Path,
    *,
    stage: int = 0,
    capsule_name: str = "nexu",
    user_goal: str = "",
    effective_ui: dict[str, Any] | None = None,
    baseline_contracts: dict[str, Any] | None = None,
    workspace_root: Path | None = None,
) -> str:
    """
    Package the active Cinema stage HTML as a single Markpact README.md.

    Run in Markpact shell (Linux):
        markpact /path/to/downloaded.md
    """
    stage_file = cinema_dir / f"stage{stage}.html"
    if not stage_file.exists():
        raise FileNotFoundError(f"missing {stage_file.name} in {cinema_dir}")

    html = stage_file.read_text(encoding="utf-8")
    title_match = re.search(r"<title[^>]*>([^<]*)</title>", html, flags=re.I)
    app_title = (
        title_match.group(1).strip() if title_match else None
    ) or f"{capsule_name} S{stage}"

    effective = effective_ui or {}
    keep = list(effective.get("keep") or [])
    delete = list(effective.get("delete") or [])
    goal_line = user_goal.strip() or "(none recorded)"
    baselines = baseline_contracts or {}
    project_contracts = list(baselines.get("project") or [])
    capsule_contracts = list(baselines.get("capsule") or [])

    meta = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "capsule": capsule_name,
        "stage": stage,
        "source": stage_file.name,
        "user_goal": goal_line,
        "policy_keep": keep,
        "policy_delete": delete,
        "baseline_contracts": {
            "project": project_contracts,
            "capsule": capsule_contracts,
        },
    }

    html_body = _escape_markdown_fence(html)
    baseline_lines = [
        str(item.get("line") or item.get("id") or item)
        for item in project_contracts + capsule_contracts
    ]
    baseline_block = "\n".join(f"- `{line}`" for line in baseline_lines) or "- (none)"

    return f"""# {app_title} — Nexu Markpact export

Portable **Markpact** capsule exported from Nexu (stage {stage}).
Open this file in Markpact and run the `markpact:run` block like any other app.
The HTML is exported together with Nexu/Intract intent contracts so future edits can preserve the
baseline model instead of only copying pixels.

## Nexu context

- **Capsule:** `{capsule_name}`
- **Goal:** {goal_line}
- **Policy KEEP:** {", ".join(keep) if keep else "(none)"}
- **Policy DELETE:** {", ".join(delete) if delete else "(none)"}

## Intract baseline model

These contracts describe what the exported app is expected to remain. Treat them as regression
guards when changing the generated UI:

{baseline_block}

```json markpact:file path=cinema/export-meta.json
{json.dumps(meta, indent=2, ensure_ascii=False)}
```

## Application UI

```html markpact:file path=index.html
{html_body}
```

## Project context

This context is included so an LLM/agent can reason about the app beyond pixels: source files,
configuration, dependencies, and intent manifests.

{_project_context_block(workspace_root)}

## Run (local HTTP preview)

```bash markpact:run
python -m http.server ${{MARKPACT_PORT:-8765}}
```

Then open `http://127.0.0.1:${{MARKPACT_PORT:-8765}}/` in a browser.
Markpact prints the URL in the shell.

> **Linux one-liner** (after `pip install markpact` or `uv pip install markpact`):
> `markpact "$(pwd)/{capsule_name}-S{stage}-markpact.md"`
"""


def markpact_download_filename(capsule_name: str, stage: int = 0) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", capsule_name).strip("-") or "nexu"
    return f"{safe}-S{stage}-markpact.md"
