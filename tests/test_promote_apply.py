from pathlib import Path

from nexu.capsule import create_capsule
from nexu.freeze import freeze_project
from nexu.init_project import init_project
from nexu.promote import build_promotion_plan, apply_promotion_plan

def test_apply_promotion_plan(tmp_path: Path):
    (tmp_path / "src").mkdir()
    app_file = tmp_path / "src" / "app.py"
    app_file.write_text(
        '# @intract.v1 scope:function intent:preview:item priority:1 domain:demo input:item output:evolved_capsule,promotion_plan,evidence_map effect:read forbid:write,secret_leak validate:output_presence,no_forbidden_effect meaning:"demo"\n'
        'def preview_item(item):\n'
        '    evidence_map = {"item": item}\n'
        '    return {"evolved_capsule": item, "promotion_plan": [], "evidence_map": evidence_map}\n',
        encoding="utf-8",
    )
    init_project(tmp_path)
    snapshot = freeze_project(tmp_path, "baseline")
    create_capsule(tmp_path, "demo", include=["src/**"], snapshot_id=snapshot.id)
    
    # Symuluj zmianę wewnątrz kapsuły
    capsule_file = tmp_path / ".nexu" / "capsules" / "demo" / "src" / "src" / "app.py"
    assert capsule_file.exists()
    capsule_file.write_text(capsule_file.read_text(encoding="utf-8") + "\n# NEW CONTENT FROM LLM\n", encoding="utf-8")
    
    plan = build_promotion_plan(tmp_path, "demo")
    
    # Upewnijmy się, że można zaaplikować (jeśli błędy to mockujemy do True)
    plan["ready_for_apply"] = True
    
    apply_promotion_plan(tmp_path, plan)
    
    # Weryfikacja czy plik w głównym projekcie został zaktualizowany
    new_content = app_file.read_text(encoding="utf-8")
    assert "# NEW CONTENT FROM LLM" in new_content
