"""Capsule verification: a pipeline of small, named checks over a VerifyContext."""

from __future__ import annotations

from .context import CapsuleCheck, VerifyContext
from .engine import DEFAULT_CHECKS, run_checks, verify_capsule
from .summary import summary_status

__all__ = [
    "CapsuleCheck",
    "DEFAULT_CHECKS",
    "VerifyContext",
    "run_checks",
    "summary_status",
    "verify_capsule",
]
