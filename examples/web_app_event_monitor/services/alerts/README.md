# 🚨 Nexu System Alerting Service

Mikroserwis analizujący parametry z silnika analityki i generujący alarmy bezpieczeństwa.

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
import requests
import os

app = FastAPI()

ANALYTICS_URL = os.environ.get("ANALYTICS_SERVICE_URL", "http://localhost:9101")
ALERTS_HISTORY = []

@app.get("/health")
def health():
    return {"status": "healthy", "service": "alerts-engine"}

@app.get("/alerts")
def get_alerts():
    # Pobieramy najnowsze dane telemetryczne
    try:
        data = requests.get(f"{ANALYTICS_URL}/metrics", timeout=1.0).json()
        cpu = data.get("cpu_usage", 0.0)
        locks = data.get("active_locks", 0)
        
        # Analiza reguł i generowanie alertów
        new_alerts = []
        if cpu > 80.0:
            new_alerts.append({
                "severity": "CRITICAL",
                "message": f"High CPU usage detected: {cpu}%",
                "rule": "CPU_THRESHOLD_EXCEEDED"
            })
        if locks > 5:
            new_alerts.append({
                "severity": "WARNING",
                "message": f"Database lock saturation: {locks} active locks",
                "rule": "DB_LOCK_WARNING"
            })
            
        if new_alerts:
            # Zachowujemy tylko ostatnie 10 alertów w historii
            ALERTS_HISTORY.extend(new_alerts)
            if len(ALERTS_HISTORY) > 10:
                ALERTS_HISTORY.pop(0)
    except Exception as e:
        return {"error": f"Failed to reach telemetry source: {e}", "alerts": []}
        
    return {"alerts": ALERTS_HISTORY or [{"severity": "OK", "message": "All systems nominal", "rule": "HEALTH_CHECK"}]}
```

## 🚀 Komenda startowa

```bash markpact:run
uvicorn main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-9102}
```
