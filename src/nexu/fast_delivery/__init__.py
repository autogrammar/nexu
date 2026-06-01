"""Fast delivery primitives for Nexu improvement loops."""

from .context import compact_html_for_llm, compact_markpact_for_llm, effective_markpact_mode
from .options import ALT_OPTION_FILES, read_cached_options, read_option_files, store_options_cache
from .router import (
    DeliveryRoute,
    choose_options_route,
    is_options_ready_status,
    options_source_label,
)

__all__ = [
    "DeliveryRoute",
    "ALT_OPTION_FILES",
    "choose_options_route",
    "compact_html_for_llm",
    "compact_markpact_for_llm",
    "effective_markpact_mode",
    "is_options_ready_status",
    "options_source_label",
    "read_cached_options",
    "read_option_files",
    "store_options_cache",
]
