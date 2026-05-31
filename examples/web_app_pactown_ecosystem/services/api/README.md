# 🔌 Nexu API Service

To jest mikroserwis API skompilowany przez Nexu jako wykonywalna piaskownica Markpact.

---

## 📦 Zależności

```text markpact:deps python
fastapi
uvicorn
```

## 📂 Pliki źródłowe

```python markpact:file path=main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "service": "api-backend"}

@app.get("/data")
def get_data():
    return {"stats": [12.5, 45.0, 78.2], "active_users": 42}
```

## 🚀 Komenda startowa

```bash markpact:run
uvicorn main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-9001}
```
