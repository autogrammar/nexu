"""Running capsule verification for a cinema workspace."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..contracts.verify.summary import summary_status
from ..models import VerificationFinding, VerificationReport
from ..paths import project_root
from ..verify import verify_capsule
from .html_checks import option_previews_are_distinct, stage_files_are_distinct
from .snapshot import cinema_dir_for


def _cinema_distinctness_findings(cinema_dir: Path) -> list[VerificationFinding]:
    """Flag stale Option A/B/C previews: stages diverged but previews didn't.

    Mirrors the staleness check `_sync_project_options` already uses to decide
    whether to regenerate previews, surfaced here as a named, reportable
    validator instead of only an internal auto-fix trigger.
    """
    if not cinema_dir.is_dir():
        return []
    try:
        stages_distinct = stage_files_are_distinct(cinema_dir)
        options_distinct = option_previews_are_distinct(cinema_dir)
    except OSError:
        return []
    if stages_distinct and not options_distinct:
        return [
            VerificationFinding(
                code="option_previews_stale",
                status="warn",
                message=(
                    "stage0/1/2.html are distinct but alt_a/b/c.html are not — "
                    "Option A/B/C previews look stale relative to the active stages."
                ),
            )
        ]
    return [
        VerificationFinding(
            code="option_previews_distinctness",
            status="pass",
            message="Option A/B/C previews reflect the current stage variations.",
        )
    ]


def verify_capsule_workspace(root: Path, capsule_name: str) -> dict[str, Any]:
    """Run nexu capsule verify plus Cinema-specific checks; return a JSON-serializable report."""
    try:
        workspace_root = project_root(root)
        report = verify_capsule(workspace_root, capsule_name)
        findings = list(report.findings)
        findings.extend(
            _cinema_distinctness_findings(cinema_dir_for(workspace_root, capsule_name))
        )
        status, score = summary_status(findings)
        return VerificationReport(
            capsule=capsule_name,
            status=status,
            score=score,
            findings=findings,
            created_at=report.created_at,
        ).to_dict()
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
