"""Check: does the capsule have any Intract-style contracts at all."""

from __future__ import annotations

from ...models import VerificationFinding
from .context import VerifyContext


def _check_contracts_presence(contracts) -> list[VerificationFinding]:
    if contracts:
        return [
            VerificationFinding(
                code="contracts_found",
                status="pass",
                message=f"Found {len(contracts)} intent contract(s).",
                evidence=[contract.key for contract in contracts if contract.key],
            )
        ]
    return [
        VerificationFinding(
            code="contracts_missing",
            status="fail",
            message="No Intract-style contracts found in capsule.",
        )
    ]


class ContractsPresenceCheck:
    name = "contracts_presence"

    def run(self, context: VerifyContext) -> list[VerificationFinding]:
        return _check_contracts_presence(context.contracts)
