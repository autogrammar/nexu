#!/usr/bin/env python3
"""
Nexu to Markpact Exporter & Runner
This script showcases the synergy between Nexu and Markpact by:
1. Reading the active Nexu capsule files from web_app_calculator.
2. Packaging them into a single, standard executable Markpact README.md.
3. Launching the generated Markpact README to bootstrap and execute the project in a zero-dependency sandbox!
"""

import os
import sys
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent

def main():
    print("=== Step 1: Loading Nexu Capsule Context ===")
    capsule_dir = ROOT / "examples" / "web_app_calculator"
    src_file = capsule_dir / "src" / "calculator.py"
    
    if not src_file.exists():
        print(f"Error: {src_file} does not exist. Run web_app_calculator first.")
        sys.exit(1)
        
    code_content = src_file.read_text()
    print(f"Loaded calculator.py: {len(code_content)} characters.")

    print("\n=== Step 2: Compiling into a single Markpact README.md ===")
    
    markpact_content = f"""# 🧮 Executable Nexu Calculator Capsule

This is a portable executable capsule compiled by Nexu into the **Markpact** format.
Everything required to run and test this code is contained in this single Markdown file.

---

## 📦 Dependencies

```text markpact:deps python
pydantic>=2.0
```

## 📂 Source Code

```python markpact:file path=src/calculator.py
{code_content}
```

## 🚀 Execution Command

```bash markpact:run
python -c "
from src.calculator import render_calculator
print('Testing calculator rendering inside isolated Markpact sandbox:')
res = render_calculator({{}})
print('Keys detected in render result:', list(res.keys()))
print('Operations available:', res['operation_list'])
"
```
"""

    output_dir = capsule_dir / "markpact_sandbox"
    output_dir.mkdir(parents=True, exist_ok=True)
    readme_path = output_dir / "README.md"
    readme_path.write_text(markpact_content)
    print(f"Created executable Markpact file: {readme_path}")

    print("\n=== Step 3: Executing Markpact Runner over the README ===")
    env = os.environ.copy()
    env["MARKPACT_SANDBOX"] = str(output_dir / "sandbox")
    
    # We run markpact using uv to ensure it runs inside our active virtualenv
    cmd = f"uv run markpact {readme_path}"
    print(f"Running command: {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            env=env,
            check=True,
            capture_output=True,
            text=True
        )
        print("\n=== [SUCCESS] Markpact Output: ===")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("\n=== [FAILURE] Markpact execution failed: ===")
        print(e.stderr)
        print(e.stdout)
        sys.exit(1)

if __name__ == "__main__":
    main()
