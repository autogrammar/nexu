"""Running capsule verification for a cinema workspace."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..paths import project_root
from ..verify import verify_capsule


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
