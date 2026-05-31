# 🖥️ Nexu Glassmorphic Event Dashboard

Wielousługowy interfejs graficzny Dashboardu systemu monitoringowego.

---

## 📦 Zależności

```text markpact:deps python
fastapi
uvicorn
requests
```

## 📂 Pliki źródłowe

```python markpact:file path=main.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
import os

app = FastAPI()

ANALYTICS_URL = os.environ.get("ANALYTICS_SERVICE_URL", "http://localhost:9101")
ALERTS_URL = os.environ.get("ALERTS_SERVICE_URL", "http://localhost:9102")

@app.get("/health")
def health():
    return {"status": "healthy", "service": "dashboard-ui"}

@app.get("/", response_class=HTMLResponse)
def index():
    # Pobranie metryk
    try:
        m = requests.get(f"{ANALYTICS_URL}/metrics", timeout=1.0).json()
        cpu, mem, locks, qps = m["cpu_usage"], m["memory_usage"], m["active_locks"], m["queries_per_sec"]
    except Exception:
        cpu, mem, locks, qps = 0, 0, 0, 0
        
    # Pobranie alertów
    try:
        a = requests.get(f"{ALERTS_URL}/alerts", timeout=1.0).json()
        alerts = a.get("alerts", [])
    except Exception:
        alerts = []
        
    alerts_html = ""
    for item in alerts:
        color = "#ff4757" if item["severity"] == "CRITICAL" else "#ffa502" if item["severity"] == "WARNING" else "#2ed573"
        alerts_html += f"""
        <div style="background: rgba(255,255,255,0.02); border-left: 4px solid {color}; padding: 12px; margin-bottom: 8px; border-radius: 4px;">
            <strong style="color: {color};">[ {item['severity']} ]</strong> {item['message']}
        </div>
        """

    html = f"""
    <html>
    <head>
        <title>Nexu Live Telemetry Ecosystem</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Outfit', sans-serif;
                background: radial-gradient(circle at top right, #1e1b4b, #0f172a);
                color: #f1f5f9;
                margin: 0;
                padding: 40px;
            }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }}
            .header h1 {{ margin: 0; font-size: 2.2rem; font-weight: 600; color: #38bdf8; }}
            .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; }}
            .card {{
                background: rgba(255, 255, 255, 0.03);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                padding: 24px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            }}
            .metric {{ font-size: 2.5rem; font-weight: 600; color: #fff; margin: 15px 0 5px 0; }}
            .metric-label {{ color: #94a3b8; font-size: 0.9rem; text-transform: uppercase; }}
            .bar {{ background: rgba(255,255,255,0.1); height: 8px; border-radius: 4px; overflow: hidden; margin-top: 10px; }}
            .bar-fill {{ background: linear-gradient(90deg, #38bdf8, #818cf8); height: 100%; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🖥️ Nexu Telemetry Control Center</h1>
                <div style="background: rgba(46, 213, 115, 0.15); border: 1px solid #2ed573; color: #2ed573; padding: 6px 14px; border-radius: 20px; font-size: 0.9rem;">
                    🟢 ECOSYSTEM ACTIVE
                </div>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h2>📈 System Load metrics</h2>
                    <div style="margin-bottom: 20px;">
                        <div class="metric-label">CPU Core Saturation</div>
                        <div class="metric">{cpu}%</div>
                        <div class="bar"><div class="bar-fill" style="width: {cpu}%;"></div></div>
                    </div>
                    <div>
                        <div class="metric-label">Active Database Locks</div>
                        <div class="metric">{locks}</div>
                        <div class="bar"><div class="bar-fill" style="width: {locks * 12.5}%; background: #ffa502;"></div></div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🚨 Active Rules & Safety Alerts</h2>
                    <div style="margin-top: 15px;">
                        {alerts_html}
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html
```

## 🚀 Komenda startowa

```bash markpact:run
uvicorn main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-9103}
```
