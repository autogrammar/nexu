"""Build portable Markpact README exports from Nexu workspace HTML."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _escape_markdown_fence(text: str, fence: str = "```") -> str:
    """Avoid closing a fenced block early if the HTML contains ```."""
    if fence not in text:
        return text
    return text.replace(fence, fence + "\\")


def build_markpact_readme(
    cinema_dir: Path,
    *,
    stage: int = 0,
    capsule_name: str = "nexu",
    user_goal: str = "",
    effective_ui: dict[str, Any] | None = None,
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
    app_title = (title_match.group(1).strip() if title_match else None) or f"{capsule_name} S{stage}"

    effective = effective_ui or {}
    keep = list(effective.get("keep") or [])
    delete = list(effective.get("delete") or [])
    goal_line = user_goal.strip() or "(none recorded)"

    meta = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "capsule": capsule_name,
        "stage": stage,
        "source": stage_file.name,
        "user_goal": goal_line,
        "policy_keep": keep,
        "policy_delete": delete,
    }

    html_body = _escape_markdown_fence(html)

    return f"""# {app_title} — Nexu Markpact export

Portable **Markpact** capsule exported from Nexu (stage {stage}).
Open this file in Markpact and run the `markpact:run` block like any other app.

## Nexu context

- **Capsule:** `{capsule_name}`
- **Goal:** {goal_line}
- **Policy KEEP:** {", ".join(keep) if keep else "(none)"}
- **Policy DELETE:** {", ".join(delete) if delete else "(none)"}

```json markpact:file path=cinema/export-meta.json
{json.dumps(meta, indent=2, ensure_ascii=False)}
```

## Application UI

```html markpact:file path=index.html
{html_body}
```

## Run (local HTTP preview)

```bash markpact:run
python -m http.server ${{MARKPACT_PORT:-8765}}
```

Then open `http://127.0.0.1:${{MARKPACT_PORT:-8765}}/` in a browser (Markpact prints the URL in the shell).

> **Linux one-liner** (after `pip install markpact` or `uv pip install markpact`):
> `markpact "$(pwd)/{capsule_name}-S{stage}-markpact.md"`
"""


def markpact_download_filename(capsule_name: str, stage: int = 0) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", capsule_name).strip("-") or "nexu"
    return f"{safe}-S{stage}-markpact.md"
