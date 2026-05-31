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
from nexu.runtime import build_capsule_runtime
from nexu.promote import build_promotion_plan, apply_promotion_plan

def main():
    work = Path(__file__).parent / "workspace"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    
    # 1. Copy source files to workspace
    src_dir = work / "src"
    src_dir.mkdir()
    shutil.copy(Path(__file__).parent / "src" / "dashboard.py", src_dir / "dashboard.py")
    
    fixtures_dir = work / "fixtures"
    fixtures_dir.mkdir()
    shutil.copy(Path(__file__).parent / "fixtures" / "dashboard_data.json", fixtures_dir / "dashboard_data.json")

    print("=== Step 1: Initializing Nexu Project and freezing baseline ===")
    init_project(work)
    snapshot = freeze_project(work, "baseline")
    capsule = create_capsule(
        work,
        "web_dashboard",
        domain="ui",
        include=["src/**", "fixtures/**"],
        routes=["/dashboard"],
        endpoints=["GET:/api/telemetry"],
        snapshot_id=snapshot.id,
    )
    print(f"Created capsule: {capsule.name}")

    # Build baseline runtime (S0)
    runtime_s0 = build_capsule_runtime(work, capsule.name)
    print(f"Generated S0 Baseline Runtime: {runtime_s0['index']}")

    # 2. Iterate S1: Upgrade notifications logic
    print("\n=== Step 2: Transitioning to Iteration S1 (Notifications Backend) ===")
    iterate_capsule(work, capsule.name, steps=1, goal="Implement notifications mock backend")
    
    # Simulate LLM adding backend mock to S1 in the capsule
    capsule_file = next((work / ".nexu" / "capsules" / "web_dashboard" / "src").rglob("dashboard.py"))
    s1_code = """# @intract.v1 scope:function intent:render:dashboard priority:1 domain:ui input:telemetry_data output:html_surface,notification_list,event_log effect:read forbid:secret_leak,destructive_write meaning:"Render the system stats dashboard with live telemetry and notifications"
def render_dashboard(telemetry_data: dict) -> dict:
    # S1 Intermediate: Telemetry status + mock notifications backend lists populated
    notifications = [
        {"id": 1, "text": "High memory warning"},
        {"id": 2, "text": "Weekly report available"}
    ]
    html_surface = f"<div style='padding: 20px; font-family: sans-serif; background: #fafafa; border-radius: 8px;'><h1 style='color: #333;'>Dashboard (S1)</h1><p>Status: <strong>{telemetry_data.get('status')}</strong></p><p>CPU: {telemetry_data.get('cpu_usage')}%</p></div>"
    event_log = ["Dashboard S1 loaded", "Notifications backend simulated"]
    return {
        "html_surface": html_surface,
        "notification_list": notifications,
        "event_log": event_log
    }
"""
    capsule_file.write_text(s1_code, encoding="utf-8")
    runtime_s1 = build_capsule_runtime(work, capsule.name)
    print(f"Generated S1 Runtime: {runtime_s1['index']}")

    # 3. Iterate S2: Complete UI rendering for notifications
    print("\n=== Step 3: Transitioning to Iteration S2 (Notifications UI) ===")
    iterate_capsule(work, capsule.name, steps=1, goal="Render notifications list on UI dashboard")
    
    s2_code = """# @intract.v1 scope:function intent:render:dashboard priority:1 domain:ui input:telemetry_data output:html_surface,notification_list,event_log effect:read forbid:secret_leak,destructive_write meaning:"Render the system stats dashboard with live telemetry and notifications"
def render_dashboard(telemetry_data: dict) -> dict:
    # S2 Final: Telemetry status + mock notifications rendered on html surface
    notifications = [
        {"id": 1, "text": "High memory warning"},
        {"id": 2, "text": "Weekly report available"}
    ]
    noti_html = "".join([f"<li style='color: #d9534f; margin: 5px 0;'>⚠️ {n['text']}</li>" for n in notifications])
    html_surface = f\"\"\"
    <div style='padding: 20px; font-family: sans-serif; background: #fafafa; border-radius: 12px; border: 1px solid #e0e0e0; max-width: 400px;'>
        <h1 style='color: #2c3e50; font-size: 24px; margin-bottom: 10px;'>System Dashboard (S2)</h1>
        <p style='color: #7f8c8d;'>Status: <strong style='color: #2ecc71;'>{telemetry_data.get('status')}</strong></p>
        <p style='color: #7f8c8d;'>CPU: <strong>{telemetry_data.get('cpu_usage')}%</strong></p>
        <hr style='border: 0; border-top: 1px solid #eee; margin: 15px 0;'/>
        <h3 style='color: #2c3e50; font-size: 16px;'>Active Notifications</h3>
        <ul style='list-style: none; padding-left: 0;'>{noti_html}</ul>
    </div>
    \"\"\"
    event_log = ["Dashboard S2 loaded", "Notifications rendered successfully"]
    return {
        "html_surface": html_surface,
        "notification_list": notifications,
        "event_log": event_log
    }
"""
    capsule_file.write_text(s2_code, encoding="utf-8")
    runtime_s2 = build_capsule_runtime(work, capsule.name)
    print(f"Generated S2 Runtime: {runtime_s2['index']}")

    # Apply promotion
    print("\n=== Step 4: Applying Promotion to final source project ===")
    plan = build_promotion_plan(work, capsule.name)
    plan["ready_for_apply"] = True  # Mock bypass check for example
    apply_promotion_plan(work, plan)
    
    promoted_code = (src_dir / "dashboard.py").read_text(encoding="utf-8")
    print("\n[PROMOTED CODE IN SOURCE PROJECT]:")
    print(promoted_code)

if __name__ == "__main__":
    main()
