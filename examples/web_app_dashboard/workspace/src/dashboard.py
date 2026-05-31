# @intract.v1 scope:function intent:render:dashboard priority:1 domain:ui input:telemetry_data output:html_surface,notification_list,event_log effect:read forbid:secret_leak,destructive_write meaning:"Render the system stats dashboard with live telemetry and notifications"
def render_dashboard(telemetry_data: dict) -> dict:
    # S2 Final: Telemetry status + mock notifications rendered on html surface
    notifications = [
        {"id": 1, "text": "High memory warning"},
        {"id": 2, "text": "Weekly report available"}
    ]
    noti_html = "".join([f"<li style='color: #d9534f; margin: 5px 0;'>⚠️ {n['text']}</li>" for n in notifications])
    html_surface = f"""
    <div style='padding: 20px; font-family: sans-serif; background: #fafafa; border-radius: 12px; border: 1px solid #e0e0e0; max-width: 400px;'>
        <h1 style='color: #2c3e50; font-size: 24px; margin-bottom: 10px;'>System Dashboard (S2)</h1>
        <p style='color: #7f8c8d;'>Status: <strong style='color: #2ecc71;'>{telemetry_data.get('status')}</strong></p>
        <p style='color: #7f8c8d;'>CPU: <strong>{telemetry_data.get('cpu_usage')}%</strong></p>
        <hr style='border: 0; border-top: 1px solid #eee; margin: 15px 0;'/>
        <h3 style='color: #2c3e50; font-size: 16px;'>Active Notifications</h3>
        <ul style='list-style: none; padding-left: 0;'>{noti_html}</ul>
    </div>
    """
    event_log = ["Dashboard S2 loaded", "Notifications rendered successfully"]
    return {
        "html_surface": html_surface,
        "notification_list": notifications,
        "event_log": event_log
    }
