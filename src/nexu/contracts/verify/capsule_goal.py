"""Check: surface the capsule's own declared goal contract (scope: capsule), if any.

A capsule may declare one or more top-level ``scope: capsule`` contracts in its
``intract.yaml`` to state its overarching intent and the sub-intents it requires
(see the ``@intract.v1`` capsule-contract convention). This check is purely
informational and additive: if a capsule has no ``scope: capsule`` contract,
it reports nothing and verification behaves exactly as before. If one exists,
it surfaces the declared intent and whether its required sub-intents are
present elsewhere in the manifest — the same "warn, don't fail" severity as
``RequiredIntentsCheck`` already uses for the same require/provide check
across all contracts, so this does not introduce a new promotion blocker.
"""

from __future__ import annotations

from ...intract import IntentContract
from ...models import VerificationFinding
from .context import VerifyContext


def _provided_keys(contracts: list[IntentContract]) -> set[str]:
    return {contract.intent for contract in contracts} | {
        contract.contract_id for contract in contracts
    }


def _goal_finding(goal: IntentContract, provided_keys: set[str]) -> VerificationFinding:
    missing = [item for item in goal.require if item not in provided_keys]
    label = goal.contract_id or goal.intent or "capsule.goal"
    presence = (
        "has unmet required sub-intents."
        if missing
        else "has all required sub-intents present."
    )
    return VerificationFinding(
        code="capsule_goal",
        status="warn" if missing else "pass",
        message=f"Capsule goal '{label}' (intent: {goal.intent or 'n/a'}) {presence}",
        evidence=[f"missing:{item}" for item in missing] or sorted(goal.require),
    )


def _check_capsule_goal(contracts: list[IntentContract]) -> list[VerificationFinding]:
    goal_contracts = [c for c in contracts if c.scope == "capsule"]
    if not goal_contracts:
        return []

    provided_keys = _provided_keys(contracts)
    return [_goal_finding(goal, provided_keys) for goal in goal_contracts]


class CapsuleGoalCheck:
    name = "capsule_goal"

    def run(self, context: VerifyContext) -> list[VerificationFinding]:
        return _check_capsule_goal(context.contracts)
