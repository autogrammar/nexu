# 📊 Nexu Event Analytics Engine

To jest silnik telemetryczny generujący w czasie rzeczywistym logi i obciążenie systemu.

---

## 📦 Zależności

```text markpact:deps python
fastapi
uvicorn
```

## 📂 Pliki źródłowe

```python markpact:file path=main.py
from fastapi import FastAPI
import random
import time

app = FastAPI()

START_TIME = time.time()

@app.get("/health")
def health():
    return {"status": "healthy", "uptime": f"{int(time.time() - START_TIME)}s"}

@app.get("/metrics")
def get_metrics():
    # Symulujemy zmienne obciążenie serwera
    return {
        "cpu_usage": round(random.uniform(15.0, 95.0), 1),
        "memory_usage": round(random.uniform(40.0, 85.0), 1),
        "active_locks": random.randint(0, 8),
        "queries_per_sec": random.randint(150, 1200),
        "timestamp": time.time()
    }
```

## 🚀 Komenda startowa

```bash markpact:run
uvicorn main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-9101}
```
