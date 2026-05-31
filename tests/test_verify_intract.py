from pathlib import Path

from nexu.capsule import create_capsule
from nexu.freeze import freeze_project
from nexu.init_project import init_project
from nexu.iterate import iterate_capsule
from nexu.verify import verify_capsule


def test_verify_treats_manifest_intract_fail_as_warn(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text(
        '# @intract.v1 scope:function intent:query:item priority:2 domain:test input:x output:y effect:read forbid:write validate:output_presence meaning:"demo"\n\n'
        'def item(x):\n    return {"y": x}\n',
        encoding="utf-8",
    )
    init_project(tmp_path)
    freeze_project(tmp_path, "baseline")
    create_capsule(tmp_path, "demo", include=["src/**"], snapshot_id="baseline")
    iterate_capsule(tmp_path, "demo", steps=1, goal="test")

    report = verify_capsule(tmp_path, "demo")
    codes = {finding.code for finding in report.findings}
    assert "intract_policy_violation" not in codes or report.status != "fail"
    assert report.status in {"pass", "partial"}
    if "intract_manifest_gap" in codes:
        gap = next(f for f in report.findings if f.code == "intract_manifest_gap")
        assert gap.status == "warn"
