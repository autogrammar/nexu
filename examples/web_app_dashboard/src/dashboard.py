# @intract.v1 scope:function intent:render:dashboard priority:1 domain:ui input:telemetry_data output:html_surface,notification_list,event_log effect:read forbid:secret_leak,destructive_write meaning:"Render the system stats dashboard with live telemetry and notifications"
def render_dashboard(telemetry_data: dict) -> dict:
    # S0 Baseline: Only renders telemetry status, no active notifications.
    html_surface = f"<div style='padding: 20px; font-family: sans-serif; background: #fafafa; border-radius: 8px;'><h1 style='color: #333;'>Dashboard</h1><p>Status: <strong>{telemetry_data.get('status')}</strong></p><p>CPU: {telemetry_data.get('cpu_usage')}%</p></div>"
    event_log = ["Dashboard baseline loaded"]
    return {
        "html_surface": html_surface,
        "notification_list": [],
        "event_log": event_log
    }
