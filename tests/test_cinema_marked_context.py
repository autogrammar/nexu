"""Tests for marked-element LLM context compaction."""

from __future__ import annotations

from repatch import (
    build_marked_element_context,
    has_ui_marks,
    inject_scope_style,
    marked_css_selectors,
    marked_scope_colors_css,
    resolve_marked_llm_context,
    resolve_marked_selectors,
    restrict_scope_css_to_marks,
    should_block_full_html_iterate,
)
from repatch.ui_patch import build_ui_patch_prompt

CALC_HTML = """<!DOCTYPE html>
<html>
<head>
  <style>
    #btn-7 { background: #334155; color: #fff; border-radius: 8px; }
    #btn-tan { background: #0ea5e9; color: #fff; }
    .btn-op { min-width: 48px; }
  </style>
</head>
<body>
  <div class="calc-body">
    <button class="btn btn-op" id="btn-7">7</button>
    <button class="btn btn-op" id="btn-tan">tan</button>
  </div>
</body>
</html>
"""

VARIANTS = [
    ("alt_a.html", "Option A (colors: cool)", "cool"),
    ("alt_b.html", "Option B (colors: contrast)", "contrast"),
    ("alt_c.html", "Option C (colors: expressive)", "expressive"),
]


def test_build_marked_element_context_extracts_subtree_and_css() -> None:
    ctx = build_marked_element_context(
        CALC_HTML,
        keep_ids=["7"],
        delete_ids=["tan"],
        focus_scope="colors",
        project_kind="calculator",
    )
    assert ctx is not None
    assert "MARKED ELEMENT CONTEXT" in ctx
    assert "btn-7" in ctx or "#7" in ctx
    assert "btn-tan" in ctx or "#tan" in ctx
    assert "#btn-7" in ctx or "background" in ctx
    assert "DELETE" in ctx
    assert "KEEP" in ctx
    assert "#colors" in ctx


def test_build_marked_element_context_uses_client_fragment_fallback() -> None:
    ctx = build_marked_element_context(
        "<html><body><div id='other'>x</div></body></html>",
        delete_ids=["missing"],
        focus_scope="functions",
        project_kind="web",
        client_fragments=[
            {
                "id": "missing",
                "type": "DELETE",
                "fragment": {"html": '<button id="btn-missing">Go</button>'},
            }
        ],
    )
    assert ctx is not None
    assert "btn-missing" in ctx


def test_build_marked_element_context_returns_none_without_marks() -> None:
    assert resolve_marked_llm_context(CALC_HTML, keep_els=[], delete_els=[]) is None


def test_build_marked_element_context_patch_mode_note() -> None:
    ctx = build_marked_element_context(
        CALC_HTML,
        delete_ids=["tan"],
        focus_scope="colors",
        project_kind="imported",
        ui_profile={
            "llm_context_mode": "patch",
            "html_outline": "<html><body></body></html>",
            "visual_css": "#btn-tan { color: red; }",
        },
    )
    assert ctx is not None
    assert "Patch mode" in ctx
    assert "color: red" in ctx or "#btn-tan" in ctx


def test_ui_patch_prompt_uses_marked_context_fragment() -> None:
    marked = build_marked_element_context(
        CALC_HTML,
        delete_ids=["tan"],
        focus_scope="colors",
        project_kind="calculator",
    )
    assert marked
    prompt = build_ui_patch_prompt(
        CALC_HTML,
        focus_scope="colors",
        project_kind="calculator",
        option_variants=VARIANTS,
        delete_els=["tan"],
        context_fragment=marked,
    )
    assert marked in prompt
    assert "DELETE-marked elements" in prompt or "primary redesign" in prompt
    assert "calc-body" not in prompt


def test_has_ui_marks() -> None:
    assert not has_ui_marks([], [])
    assert has_ui_marks(["7"], [])
    assert has_ui_marks([], ["tan"])
    assert has_ui_marks(["7"], ["tan"])


def test_restrict_scope_css_to_marks_targets_delete_only() -> None:
    css = (
        "html,body{background:#000!important;}"
        ".btn{background:#fff!important;color:#000!important;}"
    )
    scoped = restrict_scope_css_to_marks(css, ["tan"])
    assert "html,body" not in scoped
    assert "#btn-tan" in scoped or "#tan" in scoped
    assert "background:#fff" in scoped


def test_inject_scope_style_skips_global_css_for_keep_only_marks() -> None:
    html = (
        "<html><head></head><body><div class='calc-body'>"
        "<button class='btn' id='btn-7'>7</button></div></body></html>"
    )
    patched = inject_scope_style(
        html,
        "colors",
        "b",
        project_kind="calculator",
        keep_ids=["7"],
        delete_ids=[],
    )
    assert "nexu-scope-variant" not in patched


def test_inject_scope_style_scopes_css_to_delete_marks() -> None:
    html = (
        "<html><head></head><body><div class='calc-body'>"
        "<button class='btn' id='btn-tan'>tan</button></div></body></html>"
    )
    patched = inject_scope_style(
        html,
        "colors",
        "a",
        project_kind="calculator",
        delete_ids=["tan"],
    )
    assert "nexu-scope-variant" in patched
    assert "#btn-tan" in patched or "#tan" in patched
    assert "background-color:#38bdf8" in patched
    assert "html,body" not in patched


def test_resolve_marked_selectors_includes_classes() -> None:
    html = (
        "<body><a class='kb-btn2_237106-a1' href='#'>Zapisz dziecko</a>"
        "<button class='kb-btn2_999'>Nasza lokalizacja</button></body>"
    )
    selectors = resolve_marked_selectors(
        html,
        ["Zapisz dziecko", "Nasza lokalizacja"],
    )
    assert ".kb-btn2_237106-a1" in selectors
    assert ".kb-btn2_999" in selectors
    assert '[data-nexu-target="Zapisz dziecko"]' in selectors
    assert not any(sel.startswith("#Zapisz ") for sel in selectors)


def test_marked_scope_colors_css_differs_by_variant() -> None:
    selectors = [".kb-btn2_237106-a1"]
    a = marked_scope_colors_css(selectors, "a")
    b = marked_scope_colors_css(selectors, "b")
    assert "background-color:#38bdf8" in a
    assert "background-color:#facc15" in b
    assert a != b


def test_should_block_full_html_for_imported_marks() -> None:
    assert should_block_full_html_iterate("imported", ["hero"], [], focus_scope="colors")
    assert should_block_full_html_iterate("dashboard", [], ["kpi"], focus_scope="functions")
    assert not should_block_full_html_iterate("imported", [], [], focus_scope="colors")
    assert not should_block_full_html_iterate("calculator", ["7"], [], focus_scope="colors")


def test_marked_css_selectors_includes_btn_prefix() -> None:
    selectors = marked_css_selectors(["tan"])
    assert "#btn-tan" in selectors
    assert "#tan" in selectors
