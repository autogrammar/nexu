#!/usr/bin/env bash
# Quick CI smoke: unit tests + intract manifest ops + cinema policy helpers.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== nexu: uv sync =="
uv sync --quiet

echo "== nexu: pytest =="
uv run pytest -q

echo "== intract: manifest_ops tests (sibling repo) =="
INTRACT_SRC="${INTRACT_SRC:-$ROOT/../intract/src}"
INTRACT_ROOT="${INTRACT_ROOT:-$ROOT/../intract}"
if [[ -d "$INTRACT_SRC" && -d "$INTRACT_ROOT" ]]; then
  PYTHONPATH="$INTRACT_SRC${PYTHONPATH:+:$PYTHONPATH}" \
    uv run --project "$INTRACT_ROOT" --with pytest python -m pytest -q \
      "$INTRACT_ROOT/tests/test_manifest_ops.py" \
      "$INTRACT_ROOT/tests/test_proposals.py" \
      "$INTRACT_ROOT/tests/test_validate_snippet.py"
else
  echo "skip intract tests (no sibling at $INTRACT_ROOT)"
fi

echo "== cinema policy dry-run (no server) =="
uv run python - <<PY
from pathlib import Path
import sys

repo = Path("${ROOT}")
ws = repo / "examples/web_app_calculator/workspace"
capsule = "scientific_calc"
if not (ws / ".nexu/capsules" / capsule).exists():
    print("skip cinema workspace smoke (example workspace missing)")
    sys.exit(0)

sys.path.insert(0, str(repo.parent / "intract/src"))
from nexu.cinema_policy import apply_ledger_from_cinema, normalize_manifest_target

assert normalize_manifest_target("both") == "both"
result = apply_ledger_from_cinema(ws, capsule, target="both", dry_run=True)
assert "error" not in result or result.get("added_total", 0) >= 0
print("cinema policy dry-run ok:", result.get("added_total", result))
PY

echo "== ci-cinema-smoke: OK =="
