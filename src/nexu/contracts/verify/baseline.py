"""Check: does the capsule have a baseline file-hash lock, and what does it show."""

from __future__ import annotations

from pathlib import Path

from ...diff import diff_capsule
from ...models import VerificationFinding
from .context import VerifyContext


def _check_baseline_lock(
    root: Path,
    name: str,
    baseline_files: dict[str, str],
) -> list[VerificationFinding]:
    if baseline_files:
        diff = diff_capsule(root, name)
        return [
            VerificationFinding(
                code="baseline_lock",
                status="pass",
                message=f"Baseline lock tracks {len(baseline_files)} file(s).",
                evidence=[
                    f"modified={len(diff.modified)}",
                    f"added={len(diff.added)}",
                    f"deleted={len(diff.deleted)}",
                ],
            )
        ]
    return [
        VerificationFinding(
            code="baseline_lock_missing",
            status="warn",
            message=(
                "Capsule has no baseline file hash lock. "
                "Recreate capsule for stronger drift checks."
            ),
        )
    ]


class BaselineLockCheck:
    name = "baseline_lock"

    def run(self, context: VerifyContext) -> list[VerificationFinding]:
        return _check_baseline_lock(context.root, context.name, context.baseline_files)
