"""Compatibility wrapper — implementation moved to :mod:`nexu.contracts.adapter`."""

from __future__ import annotations

from .contracts.adapter import (
    _ensure_intract_on_path,
    _finding_for_result,
    _policy_findings,
    _result_status,
    _sibling_intract_src,
    check_intract_policy,
)

__all__ = [
    "_ensure_intract_on_path",
    "_finding_for_result",
    "_policy_findings",
    "_result_status",
    "_sibling_intract_src",
    "check_intract_policy",
]
