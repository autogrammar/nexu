import json
from pathlib import Path

from nexu.export_prompt import export_iteration_prompt
from nexu.paths import capsule_dir


def test_export_prompt_includes_cinema_ledger_block(tmp_path: Path):
    root = tmp_path / "ws"
    root.mkdir()
    name = "demo"
    base = capsule_dir(root, name)
    base.mkdir(parents=True)
    (base / "capsule.yaml").write_text(
        "name: demo\ncontracts_manifest: intract.yaml\niterations: [S0]\n",
        encoding="utf-8",
    )
    (base / "intract.yaml").write_text(
        "version: intract.v1\ncontracts:\n  - id: c1\n    scope: ui\n    intent: keep:ui\n",
        encoding="utf-8",
    )
    cinema = base / "cinema"
    cinema.mkdir()
    line = '@intract.v1 id:test scope:ui intent:ui:keep:x priority:1 domain:ui'
    (cinema / "intract_policy_ledger.json").write_text(
        json.dumps(
            [
                {
                    "status": "evolved_by_llm",
                    "stage": 0,
                    "proposed_contracts": [{"line": line}],
                }
            ]
        ),
        encoding="utf-8",
    )

    export = export_iteration_prompt(root, name)
    markdown = Path(export.path).read_text(encoding="utf-8")
    assert "Cinema policy ledger" in markdown
    assert line in markdown
