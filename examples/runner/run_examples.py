from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nexu.blueprint import build_blueprint  # noqa: E402
from nexu.capsule import create_capsule  # noqa: E402
from nexu.diff import diff_capsule  # noqa: E402
from nexu.drift import check_source_drift  # noqa: E402
from nexu.export_prompt import export_iteration_prompt  # noqa: E402
from nexu.freeze import freeze_project  # noqa: E402
from nexu.init_project import init_project  # noqa: E402
from nexu.iterate import iterate_capsule  # noqa: E402
from nexu.plan import build_iteration_plan  # noqa: E402
from nexu.report import build_capsule_report  # noqa: E402
from nexu.review import build_review_packet  # noqa: E402
from nexu.bundle import build_capsule_bundle  # noqa: E402
from nexu.runtime import build_capsule_runtime  # noqa: E402
from nexu.orchestrate import build_capsule_orchestration  # noqa: E402
from nexu.verify import verify_capsule  # noqa: E402

EXAMPLES = [
    ROOT / "examples" / "frontend_view",
    ROOT / "examples" / "backend_service",
    ROOT / "examples" / "vertical_slice",
    ROOT / "examples" / "mcp_service",
]


def run_example(example: Path) -> None:
    work = example / ".tmp_nexu_run"
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(example, work, ignore=shutil.ignore_patterns(".tmp_nexu_run", ".nexu"))

    init_project(work)
    snapshot = freeze_project(work, "baseline")
    capsule = create_capsule(
        work,
        "demo",
        include=["**/*.py"],
        routes=["/demo"],
        endpoints=["GET:/api/demo"],
        snapshot_id=snapshot.id,
    )
    plan = build_iteration_plan(work, capsule.name, steps=3, goal="demo")
    blueprint = build_blueprint(work, capsule.name)
    iterations = iterate_capsule(work, capsule.name, steps=2, goal="demo")
    runtime = build_capsule_runtime(work, capsule.name)
    prompt = export_iteration_prompt(work, capsule.name)
    diff = diff_capsule(work, capsule.name)
    drift = check_source_drift(work, capsule.name)
    verify = verify_capsule(work, capsule.name)
    capsule_report = build_capsule_report(work, capsule.name)
    review = build_review_packet(work, capsule.name)
    bundle = build_capsule_bundle(work, capsule.name, include_src=False)
    orchestration = build_capsule_orchestration(work, capsule.name, steps=3, goal="demo")

    print(
        f"{example.name}: ok | files={len(capsule.baseline_files)} "
        f"plan_steps={len(plan['steps'])} iterations={','.join(iterations)} "
        f"blueprint={blueprint['version']} runtime={Path(runtime['index']).name} "
        f"prompt={Path(prompt.path).name} diff_modified={len(diff.modified)} "
        f"drift={drift['status']} verify={verify.status} report={capsule_report['status']} "
        f"review={review['decision']} bundle_files={bundle['file_count']} orchestration={orchestration['steps']}"
    )


def main() -> None:
    for example in EXAMPLES:
        run_example(example)


if __name__ == "__main__":
    main()
