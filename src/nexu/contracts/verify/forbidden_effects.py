"""Checks: forbidden write/secret-leak effects declared by contracts vs source evidence."""

from __future__ import annotations

from pathlib import Path

from ...models import VerificationFinding
from .context import VerifyContext

WRITE_PATTERNS = [
    "session.commit(",
    ".commit(",
    "INSERT ",
    "UPDATE ",
    "DELETE ",
    "open(",
    ".write(",
    "fs.writeFile",
    "fetch(",
    "requests.post",
    "httpx.post",
]

SECRET_PATTERNS = [
    "OPENAI_API_KEY=",
    "OPENROUTER_API_KEY=",
    "SECRET_KEY=",
    "password=",
    "api_key=",
]


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


def _contains_patterns(path: Path, patterns: list[str]) -> list[str]:
    text = _text(path)
    evidence = []
    for pattern in patterns:
        if pattern in text:
            evidence.append(f"{path.name}: contains `{pattern}`")
    return evidence


def _check_forbidden_write(
    contracts,
    source_files: list[Path],
) -> list[VerificationFinding]:
    forbids_write = any(
        "write" in contract.forbid or "destructive_write" in contract.forbid
        for contract in contracts
    )
    if not forbids_write:
        return []

    write_evidence: list[str] = []
    for path in source_files:
        write_evidence.extend(_contains_patterns(path, WRITE_PATTERNS))

    if write_evidence:
        return [
            VerificationFinding(
                code="forbidden_write_detected",
                status="fail",
                message="A contract forbids write effects, but write-like patterns were detected.",
                evidence=write_evidence[:20],
            )
        ]
    return [
        VerificationFinding(
            code="no_forbidden_write",
            status="pass",
            message="No obvious forbidden write effect detected.",
        )
    ]


def _check_forbidden_secret(
    contracts,
    source_files: list[Path],
) -> list[VerificationFinding]:
    forbids_secret = any(
        "secret_leak" in contract.forbid or "secrets" in contract.forbid for contract in contracts
    )
    if not forbids_secret:
        return []

    secret_evidence: list[str] = []
    for path in source_files:
        secret_evidence.extend(_contains_patterns(path, SECRET_PATTERNS))
    return [
        VerificationFinding(
            code="secret_leak_check",
            status="fail" if secret_evidence else "pass",
            message=(
                "Secret-like values detected."
                if secret_evidence
                else "No obvious secret-like values detected."
            ),
            evidence=secret_evidence[:20],
        )
    ]


class ForbiddenWriteCheck:
    name = "forbidden_write"

    def run(self, context: VerifyContext) -> list[VerificationFinding]:
        return _check_forbidden_write(context.contracts, context.source_files)


class ForbiddenSecretCheck:
    name = "forbidden_secret"

    def run(self, context: VerifyContext) -> list[VerificationFinding]:
        return _check_forbidden_secret(context.contracts, context.source_files)
