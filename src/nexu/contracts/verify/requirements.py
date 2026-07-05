"""Check: required sub-intents declared by contracts are explicitly present."""

from __future__ import annotations

from ...models import VerificationFinding
from .context import VerifyContext


def _check_required_intents(contracts) -> list[VerificationFinding]:
    required = sorted({item for contract in contracts for item in contract.require})
    if not required:
        return []
    provided_keys = {contract.intent for contract in contracts} | {
        contract.contract_id for contract in contracts
    }
    missing_required = [item for item in required if item not in provided_keys]
    return [
        VerificationFinding(
            code="required_intents",
            status="warn" if missing_required else "pass",
            message=(
                "Some required sub-intents are not explicitly present."
                if missing_required
                else "Required sub-intents are explicitly present."
            ),
            evidence=[f"missing:{item}" for item in missing_required] or sorted(required),
        )
    ]


class RequiredIntentsCheck:
    name = "required_intents"

    def run(self, context: VerifyContext) -> list[VerificationFinding]:
        return _check_required_intents(context.contracts)
