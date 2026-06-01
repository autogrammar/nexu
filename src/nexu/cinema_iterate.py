"""Shared helpers for Cinema ``/iterate`` responses (used by generated server.py)."""

from __future__ import annotations

import time
from typing import Any


def build_iterate_response_payload(
    *,
    status_msg: str,
    iteration_mode: str,
    focus_scope: str,
    focus_scope_label: str,
    current_stage: int,
    keep_els: list[str],
    delete_els: list[str],
    ledger_keep: Any,
    ledger_delete: Any,
    session_keep: Any,
    session_delete: Any,
    options_written: list[str],
    spatial_removed: list[str],
    llm_error: str | None,
    policy_entry: Any,
    intract_validation: Any,
    history_checkpoint: Any,
    options_sync: Any,
    options_stamp_ms: int | None = None,
) -> dict[str, Any]:
    """Build the JSON body returned by POST ``/iterate``."""
    normalized_scope = (focus_scope or "functions").strip() or "functions"
    normalized_label = focus_scope_label or (
        f"#{focus_scope}" if focus_scope else "#functions"
    )
    response_error = llm_error
    if str(status_msg or "").startswith("llm_failed") and normalized_scope == "functions":
        response_error = (
            llm_error
            or "Enable LLM network calls and API key in workspace nexu.yaml, "
            "or switch to a visual scope (#colors, #display, …) for offline Options A–C."
        )
    stamp = options_stamp_ms
    if stamp is None and options_written:
        stamp = int(time.time() * 1000)
    return {
        "status": status_msg,
        "mode": iteration_mode,
        "focus_scope": normalized_scope,
        "focus_scope_label": normalized_label,
        "new_stage": current_stage,
        "keep_count": len(keep_els),
        "delete_count": len(delete_els),
        "ledger_keep": ledger_keep,
        "ledger_delete": ledger_delete,
        "session_keep": session_keep,
        "session_delete": session_delete,
        "options_written": options_written,
        "options_stamp": stamp,
        "spatial_removed": spatial_removed,
        "error": response_error,
        "policy_updated": policy_entry is not None,
        "intract_validation": intract_validation,
        "history_checkpoint": history_checkpoint,
        "options_sync": options_sync,
    }
