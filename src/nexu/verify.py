"""Compatibility wrapper — implementation moved to :mod:`nexu.contracts.verify`."""

from __future__ import annotations

from .contracts.verify import verify_capsule
from .contracts.verify.baseline import _check_baseline_lock
from .contracts.verify.contracts_presence import _check_contracts_presence
from .contracts.verify.engine import _scan_capsule_contracts
from .contracts.verify.forbidden_effects import (
    SECRET_PATTERNS,
    WRITE_PATTERNS,
    _check_forbidden_secret,
    _check_forbidden_write,
    _contains_patterns,
    _text,
)
from .contracts.verify.iterations import _check_iteration_count
from .contracts.verify.outputs import _check_output_presence, _find_term_evidence
from .contracts.verify.requirements import _check_required_intents
from .contracts.verify.source_files import _check_source_files_presence
from .contracts.verify.summary import summary_status as _summary_status

__all__ = ["verify_capsule"]
