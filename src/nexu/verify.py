from __future__ import annotations

import re
from pathlib import Path

from .capsule import load_capsule
from .diff import diff_capsule
from .files import collect_files, rel
from .intract import IntentContract, read_manifest_contracts, scan_contracts_in_file
from .models import VerificationFinding, VerificationReport, write_yaml
from .paths import capsule_dir

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


def _scan_capsule_contracts(base: Path, manifest_name: str = "intract.yaml") -> list[IntentContract]:
    contracts = read_manifest_contracts(base / manifest_name)
    for path in collect_files(base / "src"):
        contracts.extend(scan_contracts_in_file(path, base))
    return contracts


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


def _find_term_evidence(source_files: list[Path], base: Path, terms: list[str]) -> dict[str, list[str]]:
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


def _check_contracts_presence(contracts: list[IntentContract]) -> list[VerificationFinding]:
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


def _check_baseline_lock(root: Path, name: str, baseline_files: dict[str, str]) -> list[VerificationFinding]:
    if baseline_files:
        diff = diff_capsule(root, name)
        return [
            VerificationFinding(
                code="baseline_lock",
                status="pass",
                message=f"Baseline lock tracks {len(baseline_files)} file(s).",
                evidence=[
                    f"modified={len(diff.modified)}",
                    f"added={len(diff.added)}",
                    f"deleted={len(diff.deleted)}",
                ],
            )
        ]
    return [
        VerificationFinding(
            code="baseline_lock_missing",
            status="warn",
            message="Capsule has no baseline file hash lock. Recreate capsule for stronger drift checks.",
        )
    ]


def _check_forbidden_write(
    contracts: list[IntentContract],
    source_files: list[Path],
) -> list[VerificationFinding]:
    forbids_write = any(
        "write" in contract.forbid or "destructive_write" in contract.forbid for contract in contracts
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
    contracts: list[IntentContract],
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
            message="Secret-like values detected." if secret_evidence else "No obvious secret-like values detected.",
            evidence=secret_evidence[:20],
        )
    ]


def _check_output_presence(
    contracts: list[IntentContract],
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


def _check_required_intents(contracts: list[IntentContract]) -> list[VerificationFinding]:
    required = sorted({item for contract in contracts for item in contract.require})
    if not required:
        return []
    provided_keys = {contract.intent for contract in contracts} | {contract.contract_id for contract in contracts}
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


def _summary_status(findings: list[VerificationFinding]) -> tuple[str, float]:
    statuses = [finding.status for finding in findings]
    fail_count = statuses.count("fail")
    warn_count = statuses.count("warn")
    if fail_count:
        status = "fail"
    elif warn_count:
        status = "partial"
    else:
        status = "pass"

    total = len(findings) or 1
    score = max(0.0, min(1.0, (total - fail_count - 0.4 * warn_count) / total))
    return status, round(score, 3)


def verify_capsule(root: Path, name: str) -> VerificationReport:
    capsule = load_capsule(root, name)
    base = capsule_dir(root, name)
    findings: list[VerificationFinding] = []

    contracts = _scan_capsule_contracts(base, capsule.contracts_manifest)
    findings.extend(_check_contracts_presence(contracts))

    source_files = collect_files(base / "src")
    findings.extend(_check_source_files_presence(source_files, base))

    findings.extend(_check_baseline_lock(root, name, capsule.baseline_files))
    findings.extend(_check_forbidden_write(contracts, source_files))
    findings.extend(_check_forbidden_secret(contracts, source_files))
    findings.extend(_check_output_presence(contracts, source_files, base))
    findings.extend(_check_required_intents(contracts))
    findings.extend(_check_iteration_count(capsule.iterations))

    # Dynamic integration with the actual sibling intract package
    try:
        import sys
        # Robust search to locate sibling intract package directory
        sibling_intract = None
        curr = root.resolve()
        for _ in range(6):
            if (curr / "intract" / "src").exists():
                sibling_intract = curr / "intract" / "src"
                break
            if (curr.parent / "intract" / "src").exists():
                sibling_intract = curr.parent / "intract" / "src"
                break
            curr = curr.parent

        if sibling_intract and str(sibling_intract) not in sys.path:
            sys.path.insert(0, str(sibling_intract))

        from intract.check import validate_selected_paths
        from intract.policy import decide_policy

        files_to_check = [rel(p, base) for p in collect_files(base / "src")]
        manifest_path = base / capsule.contracts_manifest
        
        intract_report = validate_selected_paths(base, files_to_check, manifest=manifest_path)
        policy = decide_policy(
            intract_report,
            manifest_path=manifest_path,
            fail_on=["violation", "invalid_manifest"],
            warn_on=["partial", "unknown"],
        )

        intract_codes: set[str] = set()
        for result in getattr(intract_report, "results", []) or []:
            raw_status = getattr(getattr(result, "status", ""), "value", str(getattr(result, "status", "")))
            contract = getattr(result, "contract", "unknown.contract")
            file_path = getattr(result, "file_path", "")
            evidence = getattr(result, "evidence", {}) or {}
            is_manifest_gap = bool(evidence.get("manifest_contract")) and str(file_path).endswith(
                ("intract.yaml", "intent.yaml", ".intract.yaml")
            )
            if raw_status == "violation":
                intract_codes.add("intract_policy_violation")
                findings.append(
                    VerificationFinding(
                        code="intract_policy_violation",
                        status="fail",
                        message=f"{raw_status}: {contract} {file_path}".strip(),
                    )
                )
            elif raw_status == "fail" and is_manifest_gap:
                intract_codes.add("intract_manifest_gap")
                findings.append(
                    VerificationFinding(
                        code="intract_manifest_gap",
                        status="warn",
                        message=f"Manifest contract not yet reflected in capsule sources: {contract}",
                        evidence=[str(file_path)] if file_path else [],
                    )
                )
            elif raw_status == "fail":
                intract_codes.add("intract_policy_violation")
                findings.append(
                    VerificationFinding(
                        code="intract_policy_violation",
                        status="fail",
                        message=f"{raw_status}: {contract} {file_path}".strip(),
                    )
                )
            elif raw_status == "partial":
                intract_codes.add("intract_policy_warning")
                findings.append(
                    VerificationFinding(
                        code="intract_policy_warning",
                        status="warn",
                        message=f"{raw_status}: {contract} {file_path}".strip(),
                    )
                )

        for reason in policy.reasons:
            intract_codes.add("intract_policy_violation")
            findings.append(
                VerificationFinding(
                    code="intract_policy_violation",
                    status="fail",
                    message=reason,
                )
            )
        for warning in policy.warnings:
            intract_codes.add("intract_policy_warning")
            findings.append(
                VerificationFinding(
                    code="intract_policy_warning",
                    status="warn",
                    message=warning,
                )
            )
        if not intract_codes:
            findings.append(
                VerificationFinding(
                    code="intract_policy_check",
                    status="pass",
                    message="All scanned intract contracts are satisfied.",
                )
            )
    except Exception as e:
        findings.append(
            VerificationFinding(
                code="intract_integration_fallback",
                status="warn",
                message=f"Intract integration fallback: {str(e)}"
            )
        )

    status, score = _summary_status(findings)

    report = VerificationReport(capsule=name, status=status, score=score, findings=findings)
    write_yaml(base / "evidence" / "verification.yaml", report.to_dict())
    return report
