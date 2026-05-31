from pathlib import Path

from nexu.cinema import build_intract_policy_snapshot
from nexu.cinema_baseline_contracts import (
    calculator_baseline_contracts,
    ensure_capsule_intract_yaml,
    is_calculator_capsule,
    merge_calculator_baselines,
)


def test_calculator_baseline_contracts_count():
    contracts = calculator_baseline_contracts()
    assert len(contracts) >= 6
    ids = {c["id"] for c in contracts}
    assert "calc.app.kind" in ids
    assert "calc.ui.display" in ids
    assert "calc.options.variant_c" in ids


def test_is_calculator_capsule_by_name(tmp_path: Path):
    base = tmp_path / ".nexu" / "capsules" / "scientific_calc"
    (base / "src").mkdir(parents=True)
    (base / "src" / "calculator.py").write_text("def render_calculator(): pass\n")
    assert is_calculator_capsule(tmp_path, "scientific_calc")


def test_ensure_capsule_intract_yaml_writes(tmp_path: Path):
    base = tmp_path / ".nexu" / "capsules" / "scientific_calc"
    (base / "src").mkdir(parents=True)
    (base / "src" / "calculator.py").write_text("# calc\n")
    path = ensure_capsule_intract_yaml(tmp_path, "scientific_calc")
    assert path is not None
    text = path.read_text(encoding="utf-8")
    assert "calc.ui.display" in text
    assert "calc.options.variant_a" in text


def test_snapshot_includes_calculator_baselines(tmp_path: Path):
    base = tmp_path / ".nexu" / "capsules" / "scientific_calc"
    (base / "src").mkdir(parents=True)
    (base / "src" / "calculator.py").write_text("# calc\n")
    snap = build_intract_policy_snapshot(tmp_path, "scientific_calc")
    capsule = snap["baseline_contracts"]["capsule"]
    ids = {c["id"] for c in capsule}
    assert "calc.app.kind" in ids


def test_merge_does_not_duplicate(tmp_path: Path):
    existing = [{"id": "calc.app.kind", "intent": "x"}]
    merged = merge_calculator_baselines(existing, tmp_path, "scientific_calc")
    assert sum(1 for c in merged if c["id"] == "calc.app.kind") == 1
