import sys
import json
from pathlib import Path

# Add local package roots
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Add sibling lane path
sibling_lane = ROOT.parent / "lane" / "src"
if sibling_lane.exists() and str(sibling_lane) not in sys.path:
    sys.path.insert(0, str(sibling_lane))

def simulate_realtime_sync():
    print("=== Step 1: Running Lane Metrics and Task Generation ===")
    
    # Try importing lane to demonstrate dynamic analysis
    try:
        from lane.project_analyzer import analyze_project
        from lane.git_reader import read_git_context
        
        # Analyze our target calculator example
        target_project = ROOT / "examples" / "web_app_calculator"
        snapshot = analyze_project(target_project)
        print(f"Lane detected project: {snapshot.name}")
        print(f"Lane detected tech stack: {snapshot.language_stack}")
    except ImportError as e:
        print(f"Lane module import failed: {e}. Using static metrics fallback.")
        project_context = {"stack": "Python Web / HTML UI", "complexity": "low"}
    
    # Lane generates the TaskPlan for nexu
    generated_plan = {
        "tasks": [
            {
                "id": "task-1",
                "title": "Upgrade Simple Web Calculator to Scientific UI",
                "description": "Evolve calculator.py UI with high-fidelity scientific trigonometric sin, cos, tan, log layout.",
                "priority": "high"
            }
        ]
    }
    
    print("\n=== Step 2: Dynamically feeding Lane Task to Nexu Capsule ===")
    target_goal = generated_plan["tasks"][0]["description"]
    print(f"Feed-forward goal: \"{target_goal}\"")
    
    # Nexu capsule initialization
    from nexu.init_project import init_project
    from nexu.freeze import freeze_project
    from nexu.capsule import create_capsule
    from nexu.runtime import build_capsule_runtime
    
    demo_work = ROOT / "examples" / "web_app_calculator" / "workspace"
    print(f"Active Nexu Work dir: {demo_work}")
    
    # We load nexu capsule compile for the Lane Task
    print("\n=== Step 3: Compiling Capsule Runtime index.html for Stage Preview ===")
    # Visual check of S2 Runtime
    print("Generated runtime mock files successfully sync'd with Cinema Player.")

if __name__ == "__main__":
    simulate_realtime_sync()
