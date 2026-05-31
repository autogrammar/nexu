import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nexu.init_project import init_project
from nexu.freeze import freeze_project
from nexu.capsule import create_capsule
from nexu.iterate import iterate_capsule
from nexu.runtime import build_capsule_runtime

def main():
    work = Path(__file__).parent / "workspace"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    
    src_dir = work / "src"
    src_dir.mkdir()
    shutil.copy(Path(__file__).parent / "src" / "calculator.py", src_dir / "calculator.py")
    
    fixtures_dir = work / "fixtures"
    fixtures_dir.mkdir()
    shutil.copy(Path(__file__).parent / "fixtures" / "inputs.json", fixtures_dir / "inputs.json")

    init_project(work)
    snapshot = freeze_project(work, "baseline")

    # 1. Generate Simple Calculator Capsule (S0)
    print("=== Step 1: Generating Simple Calculator Capsule (S0) ===")
    capsule_s0 = create_capsule(
        work,
        "simple_calc",
        domain="ui",
        include=["src/**", "fixtures/**"],
        routes=["/simple"],
        snapshot_id=snapshot.id,
    )
    runtime_s0 = build_capsule_runtime(work, capsule_s0.name)
    print(f"Generated Simple Calc Runtime: {runtime_s0['index']}")

    # 2. Generate Scientific Calculator Capsule (S2)
    print("\n=== Step 2: Generating Scientific Calculator Capsule (S2) ===")
    capsule_s2 = create_capsule(
        work,
        "scientific_calc",
        domain="ui",
        include=["src/**", "fixtures/**"],
        routes=["/scientific"],
        snapshot_id=snapshot.id,
    )
    
    # Simulate LLM adding scientific operations UI in the capsule
    capsule_file = next((work / ".nexu" / "capsules" / "scientific_calc" / "src").rglob("calculator.py"))
    s2_code = """# @intract.v1 scope:function intent:render:calculator priority:1 domain:ui input:calculator_state output:html_surface,operation_list,event_log effect:read forbid:secret_leak,destructive_write meaning:"Render the calculator UI with active operations"
def render_calculator(calculator_state: dict) -> dict:
    # S2 Final: Scientific calculator with advanced trigonometric and log operations
    html_surface = \"\"\"
    <div style='padding: 20px; font-family: sans-serif; background: #2c3e50; border-radius: 12px; max-width: 400px; color: #fff;'>
        <h2 style='text-align: center; margin-top: 0;'>Scientific Calc (S2)</h2>
        <div style='background: #ecf0f1; color: #2c3e50; padding: 15px; font-size: 24px; text-align: right; border-radius: 6px; margin-bottom: 15px;'>
            sin(45) = 0.707
        </div>
        
        <!-- Scientific row -->
        <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 10px;'>
            <button style='padding: 10px; font-size: 14px; font-weight: bold; background: #34495e; color: #fff;'>sin</button>
            <button style='padding: 10px; font-size: 14px; font-weight: bold; background: #34495e; color: #fff;'>cos</button>
            <button style='padding: 10px; font-size: 14px; font-weight: bold; background: #34495e; color: #fff;'>tan</button>
            <button style='padding: 10px; font-size: 14px; font-weight: bold; background: #34495e; color: #fff;'>log</button>
        </div>

        <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;'>
            <button style='padding: 15px; font-size: 18px; font-weight: bold;'>7</button>
            <button style='padding: 15px; font-size: 18px; font-weight: bold;'>8</button>
            <button style='padding: 15px; font-size: 18px; font-weight: bold;'>9</button>
            <button style='padding: 15px; font-size: 18px; font-weight: bold; background: #e67e22; color: #fff;'>/</button>
            
            <button style='padding: 15px; font-size: 18px; font-weight: bold;'>4</button>
            <button style='padding: 15px; font-size: 18px; font-weight: bold;'>5</button>
            <button style='padding: 15px; font-size: 18px; font-weight: bold;'>6</button>
            <button style='padding: 15px; font-size: 18px; font-weight: bold; background: #e67e22; color: #fff;'>*</button>
            
            <button style='padding: 15px; font-size: 18px; font-weight: bold;'>1</button>
            <button style='padding: 15px; font-size: 18px; font-weight: bold;'>2</button>
            <button style='padding: 15px; font-size: 18px; font-weight: bold;'>3</button>
            <button style='padding: 15px; font-size: 18px; font-weight: bold; background: #e67e22; color: #fff;'>-</button>
            
            <button style='padding: 15px; font-size: 18px; font-weight: bold;'>0</button>
            <button style='padding: 15px; font-size: 18px; font-weight: bold;'>.</button>
            <button style='padding: 15px; font-size: 18px; font-weight: bold; background: #2ecc71; color: #fff;'>=</button>
            <button style='padding: 15px; font-size: 18px; font-weight: bold; background: #e67e22; color: #fff;'>+</button>
        </div>
    </div>
    \"\"\"
    event_log = ["Scientific calculator rendered with trigonometric support"]
    return {
        "html_surface": html_surface,
        "operation_list": ["+", "-", "*", "/", "sin", "cos", "tan", "log"],
        "event_log": event_log
    }
"""
    capsule_file.write_text(s2_code, encoding="utf-8")
    runtime_s2 = build_capsule_runtime(work, capsule_s2.name)
    print(f"Generated Scientific Calc Runtime: {runtime_s2['index']}")

if __name__ == "__main__":
    main()
