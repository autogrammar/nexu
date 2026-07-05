"""Locating the sibling intract package and validating artifacts against it."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from ..paths import project_root


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
