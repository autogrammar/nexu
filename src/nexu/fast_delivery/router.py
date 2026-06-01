"""Route selection for low-latency Nexu option generation."""

from __future__ import annotations

from dataclasses import dataclass

READY_OPTION_STATUSES = frozenset(
    {
        "proposed_options_cached",
        "proposed_options_by_llm_patch",
        "proposed_options_offline",
        "proposed_options_by_intract_patch",
        "proposed_options_by_llm",
    }
)


@dataclass(frozen=True)
class DeliveryRoute:
    """Selected route for one improvement-loop step."""

    name: str
    status: str
    source: str
    requires_llm: bool = False


def choose_options_route(
    *,
    cache_hit: bool,
    force_refresh: bool,
    llm_patch_options: bool,
    llm_patch_supported: bool,
    fast_scope_options: bool,
    offline_supported: bool,
    option_generation_mode: str,
) -> DeliveryRoute:
    """Choose the cheapest viable A-C option path."""
    if cache_hit and not force_refresh:
        return DeliveryRoute("cache", "proposed_options_cached", "cache")
    if llm_patch_options and llm_patch_supported:
        return DeliveryRoute(
            "llm_patch",
            "proposed_options_by_llm_patch",
            "LLM patch",
            requires_llm=True,
        )
    if fast_scope_options and offline_supported:
        return DeliveryRoute("offline", "proposed_options_offline", "scope offline")
    mode = (option_generation_mode or "batch").strip().lower()
    if mode in {"batch", "single", "1"}:
        return DeliveryRoute("llm_batch", "proposed_options_by_llm", "LLM", requires_llm=True)
    return DeliveryRoute("llm_parallel", "proposed_options_by_llm", "LLM", requires_llm=True)


def is_options_ready_status(status: str) -> bool:
    return str(status or "") in READY_OPTION_STATUSES


def options_source_label(status: str) -> str:
    value = str(status or "")
    if value == "proposed_options_cached":
        return "cache"
    if value == "proposed_options_by_llm_patch":
        return "LLM patch"
    if value in {"proposed_options_offline", "proposed_options_by_intract_patch"}:
        return "scope offline"
    return "LLM"
