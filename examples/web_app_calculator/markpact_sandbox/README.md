# 🧮 Executable Nexu Calculator Capsule

This is a portable executable capsule compiled by Nexu into the **Markpact** format.
Everything required to run and test this code is contained in this single Markdown file.

---

## 📦 Dependencies

```text markpact:deps python
pydantic>=2.0
```

## 📂 Source Code

```python markpact:file path=src/calculator.py
# @intract.v1 scope:function intent:render:calculator priority:1 domain:ui input:calculator_state output:html_surface,operation_list,event_log effect:read forbid:secret_leak,destructive_write meaning:"Render the calculator UI with active operations"
def render_calculator(calculator_state: dict) -> dict:
    # S0 Baseline: Simple calculator with basic operations (+, -, *, /)
    html_surface = """
    <div style='padding: 20px; font-family: sans-serif; background: #2c3e50; border-radius: 12px; max-width: 300px; color: #fff;'>
        <h2 style='text-align: center; margin-top: 0;'>Simple Calc</h2>
        <div style='background: #ecf0f1; color: #2c3e50; padding: 15px; font-size: 24px; text-align: right; border-radius: 6px; margin-bottom: 15px;'>
            12.5
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
    """
    event_log = ["Simple calculator rendered"]
    return {
        "html_surface": html_surface,
        "operation_list": ["+", "-", "*", "/"],
        "event_log": event_log
    }

```

## 🚀 Execution Command

```bash markpact:run
python -c "
from src.calculator import render_calculator
print('Testing calculator rendering inside isolated Markpact sandbox:')
res = render_calculator({})
print('Keys detected in render result:', list(res.keys()))
print('Operations available:', res['operation_list'])
"
```
