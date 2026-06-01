from __future__ import annotations

import pytest
from repatch.ui_patch import (
    apply_ui_patch_options,
    build_ui_patch_prompt,
    parse_ui_patch_response,
    supports_llm_patch_scope,
)

HTML = """<!DOCTYPE html>
<html>
<head><title>Demo</title></head>
<body><div class="calc-body"><div id="screen" class="screen">0</div></div></body>
</html>
"""

VARIANTS = [
    ("alt_a.html", "Option A (colors: cool)", "cool"),
    ("alt_b.html", "Option B (colors: contrast)", "contrast"),
    ("alt_c.html", "Option C (colors: expressive)", "expressive"),
]


def test_build_ui_patch_prompt_is_json_contract() -> None:
    prompt = build_ui_patch_prompt(
        HTML,
        focus_scope="colors",
        project_kind="calculator",
        option_variants=VARIANTS,
        user_goal="make it clearer",
        keep_els=["7"],
        delete_els=["tan"],
    )

    assert "INTRACT UI PATCH CONTRACT" in prompt
    assert '"alt_a.html"' in prompt
    assert "Do not return HTML" in prompt
    assert "#colors" in prompt
    assert "make it clearer" in prompt
    assert "DELETE ids: tan" in prompt


def test_parse_and_apply_ui_patch_response() -> None:
    patch = parse_ui_patch_response(
        """
        ```json
        {
          "variants": {
            "alt_a.html": {"label": "Option A (colors: cool)", "css": ".screen{color:#38bdf8;}"},
            "alt_b.html": {"label": "Option B (colors: contrast)", "css": ".screen{color:#fff;}"},
            "alt_c.html": {"label": "Option C (colors: expressive)", "css": ".screen{color:#f47;}"}
          }
        }
        ```
        """
    )

    files, labels = apply_ui_patch_options(HTML, patch, option_variants=VARIANTS)

    assert labels == [
        "Option A (colors: cool)",
        "Option B (colors: contrast)",
        "Option C (colors: expressive)",
    ]
    assert set(files) == {"alt_a.html", "alt_b.html", "alt_c.html"}
    assert 'id="nexu-scope-variant"' in files["alt_a.html"]
    assert ".screen{color:#38bdf8;}" in files["alt_a.html"]
    assert "<script" not in files["alt_a.html"].lower()


def test_apply_ui_patch_restricts_visual_scope_to_red_marks() -> None:
    html = """<!DOCTYPE html><html><head></head><body>
    <button id="btn-keep" class="cta">Keep</button>
    <button id="btn-change" class="cta">Change</button>
    </body></html>"""
    patch = {
        "variants": {
            "alt_a.html": {"css": ".cta{background:#38bdf8;color:#000;}"},
            "alt_b.html": {"css": ".cta{background:#facc15;color:#000;}"},
            "alt_c.html": {"css": ".cta{background:#e879f9;color:#000;}"},
        }
    }

    files, _labels = apply_ui_patch_options(
        html,
        patch,
        option_variants=VARIANTS,
        focus_scope="colors",
        project_kind="imported",
        keep_els=["keep"],
        delete_els=["change"],
    )

    css_block = files["alt_a.html"]
    assert "#btn-change" in css_block or "#change" in css_block
    assert "#btn-keep" not in css_block
    assert ".cta{" not in css_block


def test_apply_ui_patch_noops_visual_scope_with_keep_only_marks() -> None:
    patch = {
        "variants": {
            "alt_a.html": {"css": ".screen{color:#38bdf8;}"},
            "alt_b.html": {"css": ".screen{color:#facc15;}"},
            "alt_c.html": {"css": ".screen{color:#e879f9;}"},
        }
    }

    files, _labels = apply_ui_patch_options(
        HTML,
        patch,
        option_variants=VARIANTS,
        focus_scope="colors",
        project_kind="calculator",
        keep_els=["screen"],
        delete_els=[],
    )

    assert "xpatch noop" in files["alt_a.html"]
    assert ".screen{color:#38bdf8;}" not in files["alt_a.html"]


def test_apply_ui_patch_rejects_unsafe_css() -> None:
    patch = {
        "variants": {
            "alt_a.html": {"css": ".x{background:url(https://example.test/a.png);}"},
            "alt_b.html": {"css": ".x{color:#fff;}"},
            "alt_c.html": {"css": ".x{color:#000;}"},
        }
    }

    with pytest.raises(ValueError, match="unsafe CSS token"):
        apply_ui_patch_options(HTML, patch, option_variants=VARIANTS)


def test_apply_ui_patch_rejects_flow_breaking_css() -> None:
    patch = {
        "variants": {
            "alt_a.html": {"css": ".calc-body{position:absolute;left:10px;}"},
            "alt_b.html": {"css": ".screen{color:#fff;}"},
            "alt_c.html": {"css": ".screen{color:#000;}"},
        }
    }

    with pytest.raises(ValueError, match="position:absolute"):
        apply_ui_patch_options(HTML, patch, option_variants=VARIANTS)


def test_supports_llm_patch_scope() -> None:
    assert supports_llm_patch_scope("colors", "dashboard")
    assert supports_llm_patch_scope("keypad", "calculator")
    assert not supports_llm_patch_scope("functions", "dashboard")
    assert not supports_llm_patch_scope("functions", "imported", has_marks=True)
    assert supports_llm_patch_scope("colors", "imported", has_marks=True)
