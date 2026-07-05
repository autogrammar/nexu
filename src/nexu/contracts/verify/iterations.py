"""Check: how many planned iterations the capsule has."""

from __future__ import annotations

from ...models import VerificationFinding
from .context import VerifyContext


def _check_iteration_count(iterations: list[str]) -> list[VerificationFinding]:
    iteration_count = len(iterations)
    return [
        VerificationFinding(
            code="iteration_count",
            status="pass" if iteration_count else "warn",
            message=f"Capsule has {iteration_count} planned iteration(s).",
            evidence=iterations,
        )
    ]


class IterationCountCheck:
    name = "iteration_count"

    def run(self, context: VerifyContext) -> list[VerificationFinding]:
        return _check_iteration_count(context.iterations)
