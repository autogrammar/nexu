# 💻 Nexu Web Frontend Service

To jest mikroserwis Web UI skompilowany przez Nexu jako wykonywalna piaskownica Markpact.

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
API_URL = os.environ.get("API_SERVICE_URL", "http://localhost:9001")

@app.get("/health")
def health():
    return {"status": "ok", "service": "web-frontend"}

@app.get("/", response_class=HTMLResponse)
def index():
    # Pobieramy dane z mikroserwisu backendowego
    try:
        res = requests.get(f"{API_URL}/data").json()
        stats = res.get("stats", [])
        users = res.get("active_users", 0)
    except Exception as e:
        stats = [0, 0, 0]
        users = f"Error: {e}"
        
    html = f"""
    <html>
    <head>
        <title>Nexu Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;600&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Outfit', sans-serif; background: #0f172a; color: #fff; padding: 40px; }}
            .card {{ background: rgba(255,255,255,0.05); border-radius: 16px; padding: 25px; border: 1px solid rgba(255,255,255,0.1); max-width: 400px; }}
            h2 {{ color: #38bdf8; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Ecosystem Active Stats</h2>
            <p><strong>Active users:</strong> {users}</p>
            <p><strong>Telemetry data:</strong> {stats}</p>
            <p style="color: #2ecc71;">✓ Connected to API Backend via Pactown Discovery</p>
        </div>
    </body>
    </html>
    """
    return html
```

## 🚀 Komenda startowa

```bash markpact:run
uvicorn main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-9002}
```
