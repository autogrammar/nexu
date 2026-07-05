"""Optional: static-analysis validation of a capsule's source via vallm, if installed.

Purely additive — vallm is not a core dependency of nexu (see the ``full``
extra in pyproject.toml). When it isn't installed, this check silently
produces no findings and verification behaves exactly as before. Uses
vallm's default validator set (syntax/imports/complexity), which is static
analysis only — no LLM/network calls (``enable_semantic``/``enable_security``
default to False in vallm's own settings).
"""

from __future__ import annotations

from pathlib import Path

from ...models import VerificationFinding
from .context import VerifyContext

_LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
}


def _check_vallm_validation(source_files: list[Path], base: Path) -> list[VerificationFinding]:
    try:
        from vallm import Proposal, validate
    except ImportError:
        return []

    candidates = [f for f in source_files if f.suffix in _LANGUAGE_BY_SUFFIX]
    if not candidates:
        return []

    failing: list[str] = []
    reviewing: list[str] = []
    checked = 0
    for path in candidates:
        try:
            code = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            rel_path = str(path.relative_to(base))
        except ValueError:
            rel_path = str(path)
        proposal = Proposal(
            code=code, language=_LANGUAGE_BY_SUFFIX[path.suffix], filename=rel_path
        )
        try:
            result = validate(proposal)
        except Exception as exc:
            return [
                VerificationFinding(
                    code="vallm_check_error",
                    status="warn",
                    message=f"vallm validation failed: {exc}",
                )
            ]
        checked += 1
        verdict = str(getattr(result.verdict, "value", result.verdict))
        if verdict == "fail":
            failing.append(rel_path)
        elif verdict == "review":
            reviewing.append(rel_path)

    if not checked:
        return []
    if failing:
        return [
            VerificationFinding(
                code="vallm_validation",
                status="warn",
                message=f"vallm flagged {len(failing)} of {checked} source file(s) as failing.",
                evidence=failing[:20],
            )
        ]
    if reviewing:
        return [
            VerificationFinding(
                code="vallm_validation",
                status="warn",
                message=f"vallm flagged {len(reviewing)} of {checked} source file(s) for review.",
                evidence=reviewing[:20],
            )
        ]
    return [
        VerificationFinding(
            code="vallm_validation",
            status="pass",
            message=f"vallm validated {checked} source file(s) with no issues.",
        )
    ]


class VallmValidationCheck:
    name = "vallm_validation"

    def run(self, context: VerifyContext) -> list[VerificationFinding]:
        return _check_vallm_validation(context.source_files, context.base)
