import sys
import shutil
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nexu.init_project import init_project
from nexu.freeze import freeze_project
from nexu.capsule import create_capsule
from nexu.iterate import iterate_capsule
from nexu.export_prompt import export_iteration_prompt
from nexu.plan import build_iteration_plan
from nexu.orchestrate import build_capsule_orchestration

def main():
    work = ROOT / "examples" / ".tmp_calculator"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    (work / "src").mkdir()

    calc_code = """# @intract.v1 scope:module intent:evolve:scientific priority:1 domain:logic input:basic_math output:scientific_math effect:none forbid:network,destructive_write meaning:"Upgrade basic calculator to include scientific operations like sin, cos, tan"
def add(a: float, b: float) -> float:
    return a + b

def multiply(a: float, b: float) -> float:
    return a * b
"""
    (work / "src" / "calculator.py").write_text(calc_code, encoding="utf-8")

    print("=== 1. Inicjalizacja Nexu i tworzenie Kapsuły ===")
    init_project(work)
    snapshot = freeze_project(work, "baseline")
    capsule = create_capsule(
        work,
        "calc_upgrade",
        include=["src/**/*.py"],
        snapshot_id=snapshot.id,
    )
    print(f"Utworzono kapsułę '{capsule.name}' zawierającą wyizolowany kod bazowy.")

    print("\n=== 2. Generowanie Planu Iteracji ===")
    plan = build_iteration_plan(work, capsule.name, steps=2, goal="Upgrade calculator to include math.sin, math.cos, math.tan")
    print(json.dumps(plan, indent=2))

    print("\n=== 3. Zmiana stanu iteracji (Przejście do S1) ===")
    iterations = iterate_capsule(work, capsule.name, steps=1, goal="Implement scientific functions")
    print(f"Zaktualizowana oś czasu iteracji: {iterations}")

    print("\n=== 4. Wygenerowany Prompt dla LLM (S1) ===")
    prompt = export_iteration_prompt(work, capsule.name)
    prompt_text = Path(prompt.path).read_text(encoding="utf-8")
    
    # Wyświetlimy tylko pierwsze 1200 znaków promptu, by nie zaśmiecać wyjścia
    print(prompt_text[:1200])
    print("\n[... prompt continues with code and diffs ...]")

if __name__ == "__main__":
    main()
