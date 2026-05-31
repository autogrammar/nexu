import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexu.init_project import init_project
from nexu.freeze import freeze_project
from nexu.capsule import create_capsule
from nexu.iterate import iterate_capsule

def print_code(title, path):
    print(f"\n=== {title} ===")
    print(path.read_text(encoding="utf-8").strip())
    print("=" * (8 + len(title)))

def main():
    work = ROOT / "examples" / ".tmp_calculator"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    (work / "src").mkdir()

    # Stan 0: Pierwotny (Baseline)
    calc_code_baseline = """# @intract.v1 scope:module intent:evolve:scientific priority:1 domain:logic input:basic_math output:scientific_math effect:none forbid:network
def add(a: float, b: float) -> float:
    return a + b

def multiply(a: float, b: float) -> float:
    return a * b
"""
    original_file = work / "src" / "calculator.py"
    original_file.write_text(calc_code_baseline, encoding="utf-8")
    
    print_code("STAN PIERWOTNY (Oryginał w projekcie)", original_file)

    # Inicjalizacja nexu
    init_project(work)
    snapshot = freeze_project(work, "baseline")
    capsule = create_capsule(work, "calc_upgrade", include=["src/**"], snapshot_id=snapshot.id)
    
    capsule_file = next((work / ".nexu" / "capsules" / "calc_upgrade" / "src").rglob("calculator.py"))

    # Symulacja iteracji S1 (Kod Pośredni - Agent LLM dodaje math i sin)
    iterate_capsule(work, capsule.name, steps=1, goal="Add math and sin")
    calc_code_s1 = """# @intract.v1 scope:module intent:evolve:scientific priority:1 domain:logic input:basic_math output:scientific_math effect:none forbid:network
import math

def add(a: float, b: float) -> float:
    return a + b

def multiply(a: float, b: float) -> float:
    return a * b

def sin(a: float) -> float:
    return math.sin(a)
"""
    capsule_file.write_text(calc_code_s1, encoding="utf-8")
    print_code("STAN POŚREDNI (Iteracja S1 wewnątrz kapsuły)", capsule_file)

    # Symulacja iteracji S2 (Kod Docelowy - Agent LLM dodaje cos i tan)
    iterate_capsule(work, capsule.name, steps=1, goal="Add cos and tan")
    calc_code_s2 = """# @intract.v1 scope:module intent:evolve:scientific priority:1 domain:logic input:basic_math output:scientific_math effect:none forbid:network
import math

def add(a: float, b: float) -> float:
    return a + b

def multiply(a: float, b: float) -> float:
    return a * b

def sin(a: float) -> float:
    return math.sin(a)

def cos(a: float) -> float:
    return math.cos(a)

def tan(a: float) -> float:
    return math.tan(a)
"""
    capsule_file.write_text(calc_code_s2, encoding="utf-8")
    print_code("STAN DOCELOWY (Iteracja S2 wewnątrz kapsuły - gotowe do wdrożenia)", capsule_file)

if __name__ == "__main__":
    main()
