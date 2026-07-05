from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from ..files import rel
from ..models import VerificationFinding


def _sibling_intract_src(root: Path) -> Path | None:
    curr = root.resolve()
    for _ in range(6):
        for candidate in (curr / "intract" / "src", curr.parent / "intract" / "src"):
            if candidate.exists():
                return candidate
        curr = curr.parent
    return None


def _ensure_intract_on_path(root: Path) -> None:
    sibling_intract = _sibling_intract_src(root)
    if sibling_intract and str(sibling_intract) not in sys.path:
        sys.path.insert(0, str(sibling_intract))


def _result_status(result: Any) -> str:
    status = getattr(result, "status", "")
    return getattr(status, "value", str(status))


def _finding_for_result(result: Any) -> VerificationFinding | None:
    raw_status = _result_status(result)
    contract = getattr(result, "contract", "unknown.contract")
    file_path = getattr(result, "file_path", "")
    evidence = getattr(result, "evidence", {}) or {}
    is_manifest_gap = bool(evidence.get("manifest_contract")) and str(file_path).endswith(
        ("intract.yaml", "intent.yaml", ".intract.yaml")
    )

    if raw_status == "violation":
        return VerificationFinding(
            code="intract_policy_violation",
            status="fail",
            message=f"{raw_status}: {contract} {file_path}".strip(),
        )
    if raw_status == "fail" and is_manifest_gap:
        return VerificationFinding(
            code="intract_manifest_gap",
            status="warn",
            message=f"Manifest contract not yet reflected in capsule sources: {contract}",
            evidence=[str(file_path)] if file_path else [],
        )
    if raw_status == "fail":
        return VerificationFinding(
            code="intract_policy_violation",
            status="fail",
            message=f"{raw_status}: {contract} {file_path}".strip(),
        )
    if raw_status == "partial":
        return VerificationFinding(
            code="intract_policy_warning",
            status="warn",
            message=f"{raw_status}: {contract} {file_path}".strip(),
        )
    return None


def _policy_findings(policy: Any) -> list[VerificationFinding]:
    findings: list[VerificationFinding] = []
    for reason in policy.reasons:
        findings.append(
            VerificationFinding(
                code="intract_policy_violation",
                status="fail",
                message=reason,
            )
        )
    for warning in policy.warnings:
        findings.append(
            VerificationFinding(
                code="intract_policy_warning",
                status="warn",
                message=warning,
            )
        )
    return findings


def check_intract_policy(
    root: Path,
    base: Path,
    manifest_path: Path,
    source_files: list[Path],
) -> list[VerificationFinding]:
    try:
        _ensure_intract_on_path(root)

        from intract.check import validate_selected_paths
        from intract.policy import decide_policy

        files_to_check = [rel(path, base) for path in source_files]
        intract_report = validate_selected_paths(base, files_to_check, manifest=manifest_path)
        policy = decide_policy(
            intract_report,
            manifest_path=manifest_path,
            fail_on=["violation", "invalid_manifest"],
            warn_on=["partial", "unknown"],
        )

        findings = [
            finding
            for result in getattr(intract_report, "results", []) or []
            if (finding := _finding_for_result(result)) is not None
        ]
        findings.extend(_policy_findings(policy))
        if not findings:
            findings.append(
                VerificationFinding(
                    code="intract_policy_check",
                    status="pass",
                    message="All scanned intract contracts are satisfied.",
                )
            )
        return findings
    except Exception as exc:
        return [
            VerificationFinding(
                code="intract_integration_fallback",
                status="warn",
                message=f"Intract integration fallback: {exc}",
            )
        ]
