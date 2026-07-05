"""Shared context and check protocol for capsule verification."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from ...intract import IntentContract
from ...models import VerificationFinding


@dataclass
class VerifyContext:
    """Everything a :class:`CapsuleCheck` needs to inspect a capsule."""

    root: Path
    name: str
    base: Path
    contracts: list[IntentContract]
    source_files: list[Path]
    baseline_files: dict[str, str] = field(default_factory=dict)
    iterations: list[str] = field(default_factory=list)


class CapsuleCheck(Protocol):
    """A single, named verification check over a :class:`VerifyContext`."""

    name: str

    def run(self, context: VerifyContext) -> list[VerificationFinding]: ...
