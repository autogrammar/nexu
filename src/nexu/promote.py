from __future__ import annotations

from pathlib import Path

from .capsule import load_capsule
from .diff import diff_capsule
from .drift import check_source_drift
from .files import collect_files, rel
from .models import utc_now, write_yaml
from .paths import capsule_dir
from .verify import verify_capsule


def _promotion_map(base: Path, root: Path, files: list[Path]) -> list[dict[str, str]]:
    mapped: list[dict[str, str]] = []
    src_base = base / "src"
    for path in files:
        relative = rel(path, src_base)
        mapped.append(
            {
                "capsule_path": rel(path, base),
                "target_path": relative,
                "target_absolute": str(root / relative),
                "action": "review_then_copy_or_patch",
            }
        )
    return mapped


def build_promotion_plan(root: Path, name: str) -> dict:
    capsule = load_capsule(root, name)
    base = capsule_dir(root, name)
    files = collect_files(base / "src")
    verification = verify_capsule(root, name)
    drift = check_source_drift(root, name)
    diff = diff_capsule(root, name)

    blocking_findings = [
        finding.to_dict() if hasattr(finding, "to_dict") else {
            "code": finding.code,
            "status": finding.status,
            "message": finding.message,
            "evidence": finding.evidence,
        }
        for finding in verification.findings
        if finding.status == "fail"
    ]
    ready_for_apply = verification.status == "pass" and drift.get("status") == "pass"

    plan = {
        "version": "nexu.promotion.v1",
        "capsule": name,
        "created_at": utc_now(),
        "source_project_root": capsule.source_project_root,
        "source_snapshot_id": capsule.source_snapshot_id,
        "source_git_sha": capsule.source_git_sha,
        "mode": "dry_run",
        "ready_for_apply": ready_for_apply,
        "prechecks": {
            "verification_status": verification.status,
            "verification_score": verification.score,
            "source_drift_status": drift.get("status"),
            "capsule_modified_files": len(diff.modified),
            "blocking_findings": len(blocking_findings),
        },
        "blocked_by": blocking_findings,
        "files_to_review": [rel(path, base / "src") for path in files],
        "promotion_map": _promotion_map(base, root, files),
        "instructions": [
            "Review every file before applying it to the source project.",
            "Prefer a patch/cherry-pick style promotion rather than blind overwrite.",
            "Run nexu capsule review and nexu capsule verify after promotion.",
            "If source_drift_status is drift, rebase or recreate the capsule before applying.",
        ],
    }
    write_yaml(base / "promotion-plan.yaml", plan)
    return plan

def apply_promotion_plan(root: Path, plan: dict) -> None:
    if not plan.get("ready_for_apply"):
        raise ValueError("Cannot apply: plan is not ready_for_apply. Fix blocking findings or drift first.")
    
    import shutil
    base = capsule_dir(root, plan["capsule"])
    
    for item in plan.get("promotion_map", []):
        source = base / item["capsule_path"]
        target = Path(item["target_absolute"])
        
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_file():
            shutil.copy2(source, target)
