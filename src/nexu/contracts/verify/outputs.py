"""Check: declared contract outputs have text evidence somewhere in capsule sources."""

from __future__ import annotations

import re
from pathlib import Path

from ...files import rel
from ...models import VerificationFinding
from .context import VerifyContext


def _find_term_evidence(
    source_files: list[Path],
    base: Path,
    terms: list[str],
) -> dict[str, list[str]]:
    from .forbidden_effects import _text

    evidence: dict[str, list[str]] = {}
    for term in terms:
        term_evidence: list[str] = []
        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", term).strip("_")
        variants = {term, normalized, normalized.lower(), normalized.upper()}
        for path in source_files:
            text = _text(path)
            if any(variant and variant in text for variant in variants):
                term_evidence.append(rel(path, base))
        evidence[term] = term_evidence
    return evidence


def _check_output_presence(
    contracts,
    source_files: list[Path],
    base: Path,
) -> list[VerificationFinding]:
    required_outputs = sorted({output for contract in contracts for output in contract.output})
    if not required_outputs or not source_files:
        return []

    output_evidence = _find_term_evidence(source_files, base, required_outputs)
    missing_outputs = [term for term, evidence in output_evidence.items() if not evidence]
    return [
        VerificationFinding(
            code="output_presence",
            status="warn" if missing_outputs else "pass",
            message=(
                "Some declared outputs have no text evidence."
                if missing_outputs
                else "Declared outputs have text evidence in capsule sources."
            ),
            evidence=[f"missing:{term}" for term in missing_outputs]
            or [f"{term}: {', '.join(paths[:3])}" for term, paths in output_evidence.items()],
        )
    ]


class OutputPresenceCheck:
    name = "output_presence"

    def run(self, context: VerifyContext) -> list[VerificationFinding]:
        return _check_output_presence(context.contracts, context.source_files, context.base)
