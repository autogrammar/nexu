"""Test fixtures — sibling semcod/intract on PYTHONPATH when present."""

from __future__ import annotations

import sys
from pathlib import Path


def _prepend_intract_src() -> None:
    repo = Path(__file__).resolve().parents[1]
    for candidate in (
        repo.parent / "intract" / "src",
        repo / "intract" / "src",
    ):
        if candidate.is_dir():
            path = str(candidate)
            if path not in sys.path:
                sys.path.insert(0, path)
            break


_prepend_intract_src()
