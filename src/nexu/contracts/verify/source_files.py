"""Check: does the capsule have any copied source files."""

from __future__ import annotations

from pathlib import Path

from ...files import rel
from ...models import VerificationFinding
from .context import VerifyContext


def _check_source_files_presence(source_files: list[Path], base: Path) -> list[VerificationFinding]:
    if source_files:
        return [
            VerificationFinding(
                code="source_files_found",
                status="pass",
                message=f"Capsule contains {len(source_files)} text source file(s).",
                evidence=[rel(path, base) for path in source_files[:20]],
            )
        ]
    return [
        VerificationFinding(
            code="source_files_missing",
            status="fail",
            message="Capsule has no copied source files.",
        )
    ]


class SourceFilesPresenceCheck:
    name = "source_files_presence"

    def run(self, context: VerifyContext) -> list[VerificationFinding]:
        return _check_source_files_presence(context.source_files, context.base)
