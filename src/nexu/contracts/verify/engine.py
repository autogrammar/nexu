"""Orchestrates capsule verification: gather contracts/sources, run checks, score, write report."""

from __future__ import annotations

from pathlib import Path

from ...capsule import load_capsule
from ...files import collect_files
from ...intract import IntentContract, read_manifest_contracts, read_toon_manifest_contracts, scan_contracts_in_file
from ...models import VerificationFinding, VerificationReport, write_yaml
from ...paths import capsule_dir
from ..adapter import check_intract_policy
from .baseline import BaselineLockCheck
from .capsule_goal import CapsuleGoalCheck
from .context import CapsuleCheck, VerifyContext
from .contracts_presence import ContractsPresenceCheck
from .forbidden_effects import ForbiddenSecretCheck, ForbiddenWriteCheck
from .iterations import IterationCountCheck
from .outputs import OutputPresenceCheck
from .requirements import RequiredIntentsCheck
from .source_files import SourceFilesPresenceCheck
from .summary import summary_status

DEFAULT_CHECKS: list[CapsuleCheck] = [
    ContractsPresenceCheck(),
    SourceFilesPresenceCheck(),
    BaselineLockCheck(),
    ForbiddenWriteCheck(),
    ForbiddenSecretCheck(),
    OutputPresenceCheck(),
    RequiredIntentsCheck(),
    IterationCountCheck(),
    CapsuleGoalCheck(),
]


def _scan_capsule_contracts(
    base: Path,
    manifest_name: str = "intract.yaml",
) -> list[IntentContract]:
    contracts = read_manifest_contracts(base / manifest_name)
    toon_path = base / "intract.toon.yaml"
    if toon_path.exists():
        contracts.extend(read_toon_manifest_contracts(toon_path))
    for path in collect_files(base / "src"):
        contracts.extend(scan_contracts_in_file(path, base))
    return contracts


def run_checks(context: VerifyContext, checks: list[CapsuleCheck]) -> list[VerificationFinding]:
    findings: list[VerificationFinding] = []
    for check in checks:
        findings.extend(check.run(context))
    return findings


def verify_capsule(root: Path, name: str) -> VerificationReport:
    capsule = load_capsule(root, name)
    base = capsule_dir(root, name)

    contracts = _scan_capsule_contracts(base, capsule.contracts_manifest)
    source_files = collect_files(base / "src")

    context = VerifyContext(
        root=root,
        name=name,
        base=base,
        contracts=contracts,
        source_files=source_files,
        baseline_files=capsule.baseline_files,
        iterations=capsule.iterations,
    )

    findings = run_checks(context, DEFAULT_CHECKS)

    findings.extend(
        check_intract_policy(
            root,
            base,
            base / capsule.contracts_manifest,
            source_files,
        )
    )

    status, score = summary_status(findings)

    report = VerificationReport(capsule=name, status=status, score=score, findings=findings)
    write_yaml(base / "evidence" / "verification.yaml", report.to_dict())
    return report
