"""Rolling up individual check findings into an overall status and score."""

from __future__ import annotations

from ...models import VerificationFinding


def summary_status(findings: list[VerificationFinding]) -> tuple[str, float]:
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
