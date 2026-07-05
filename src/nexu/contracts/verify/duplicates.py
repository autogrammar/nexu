"""Optional: surface code duplication in a capsule's source via redup, if installed.

Purely additive — redup is not a core dependency of nexu (see the
``full`` extra in pyproject.toml). When it isn't installed, this check
silently produces no findings and verification behaves exactly as before.
"""

from __future__ import annotations

from pathlib import Path

from ...models import VerificationFinding
from .context import VerifyContext


def _check_redup_duplicates(base: Path) -> list[VerificationFinding]:
    src_dir = base / "src"
    if not src_dir.is_dir():
        return []
    try:
        import redup
        from redup.core.models import ScanConfig
    except ImportError:
        return []

    try:
        result = redup.analyze(ScanConfig(root=src_dir))
    except Exception as exc:
        return [
            VerificationFinding(
                code="redup_check_error",
                status="warn",
                message=f"redup duplicate scan failed: {exc}",
            )
        ]

    groups = result.groups
    if not groups:
        return [
            VerificationFinding(
                code="redup_duplicates",
                status="pass",
                message="No duplicate code detected in capsule source.",
            )
        ]

    evidence = []
    for group in groups[:10]:
        if group.fragments:
            first = group.fragments[0]
            evidence.append(f"{first.file}:{first.line_start} (x{group.occurrences})")
    return [
        VerificationFinding(
            code="redup_duplicates",
            status="warn",
            message=f"redup found {len(groups)} duplicate group(s) in capsule source.",
            evidence=evidence,
        )
    ]


class RedupDuplicatesCheck:
    name = "redup_duplicates"

    def run(self, context: VerifyContext) -> list[VerificationFinding]:
        return _check_redup_duplicates(context.base)
