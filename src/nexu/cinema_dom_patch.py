"""Nexu Cinema hooks for repatch function DOM patches."""

from __future__ import annotations

from repatch.dom_patch import build_function_option_patches as _build_function_option_patches
from repatch.dom_patch import (
    build_function_patch_context,
    supports_function_patch,
)

__all__ = [
    "build_function_option_patches",
    "build_function_patch_context",
    "supports_function_patch",
]


def build_function_option_patches(html_text: str, **kwargs):
    from .cinema_html_validate import prepare_cinema_html_document
    from .cinema_scripts import finalize_cinema_html

    return _build_function_option_patches(
        html_text,
        prepare_html=prepare_cinema_html_document,
        finalize_html=finalize_cinema_html,
        **kwargs,
    )
