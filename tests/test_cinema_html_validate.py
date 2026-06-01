from nexu.cinema_html_validate import (
    filter_valid_option_batch,
    prepare_cinema_html_document,
    relocate_style_tags_to_head,
    repair_html_structure,
    validate_cinema_html_document,
    validate_css_safety,
)

_CALC_SHELL = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Calc</title></head>
<body>
<div class="calc-body">
  <div id="screen">0</div>
  <div class="btn" id="btn-7">7</div>
</div>
</body>
</html>
"""


def test_repair_adds_missing_head_and_doctype() -> None:
    raw = "<html><body><div id='screen' class='btn'>0</div></body></html>"
    repaired = repair_html_structure(raw)
    ok, errors = validate_cinema_html_document(repaired, ui_type="calculator")
    assert ok, errors
    assert repaired.startswith("<!DOCTYPE html>")
    assert "<head>" in repaired.lower()


def test_relocate_style_tags_to_head() -> None:
    raw = """<!DOCTYPE html>
<html><head><title>x</title></head><body>
<style>.screen{color:red;}</style>
<div id="screen" class="btn">0</div>
</body></html>"""
    repaired = relocate_style_tags_to_head(raw)
    assert ".screen{color:red;}" in repaired
    assert repaired.lower().index("</head>") > repaired.lower().index(".screen{color:red;}")
    assert "<body>" in repaired.lower()
    assert repaired.lower().index("<body>") > repaired.lower().index("</style>")


def test_validate_calculator_requires_screen_and_buttons() -> None:
    ok, errors = validate_cinema_html_document(_CALC_SHELL, ui_type="calculator")
    assert ok, errors

    broken = _CALC_SHELL.replace('class="btn"', 'class="control"')
    ok, errors = validate_cinema_html_document(broken, ui_type="calculator")
    assert not ok
    assert any("btn" in err for err in errors)


def test_prepare_rejects_non_html() -> None:
    doc, ok, errors = prepare_cinema_html_document("Just some CSS: .screen{color:red;}")
    assert not ok
    assert doc is None
    assert errors


def test_filter_valid_option_batch_requires_all_three() -> None:
    batch = {
        "alt_a.html": _CALC_SHELL,
        "alt_b.html": _CALC_SHELL,
        "alt_c.html": "<html><body>broken</body></html>",
    }
    valid, errors = filter_valid_option_batch(batch, ui_type="calculator")
    assert not valid
    assert errors

    good = {
        "alt_a.html": _CALC_SHELL,
        "alt_b.html": _CALC_SHELL.replace("0", "1"),
        "alt_c.html": _CALC_SHELL.replace("0", "2"),
    }
    valid, errors = filter_valid_option_batch(good, ui_type="calculator")
    assert not errors
    assert set(valid.keys()) == {"alt_a.html", "alt_b.html", "alt_c.html"}


def test_validate_css_safety_rejects_flow_breaking_layout_css() -> None:
    ok, errors = validate_css_safety(
        ".calc-body{position:absolute;left:50%;transform:translateX(-50%);}"
    )
    assert not ok
    assert any("position:absolute" in err for err in errors)
    assert any("transform" in err for err in errors)


def test_validate_css_safety_allows_runtime_overlay_css() -> None:
    ok, errors = validate_css_safety(
        ".nexu-review-btn{position:fixed;left:50%;bottom:12px;transform:translateX(-50%);}"
    )
    assert ok, errors


def test_html_validation_rejects_generated_absolute_layout() -> None:
    raw = _CALC_SHELL.replace(
        "</head>",
        "<style>.calc-body{position:fixed;left:20px;top:0;}</style></head>",
    )
    ok, errors = validate_cinema_html_document(raw, ui_type="calculator")
    assert not ok
    assert any("position:fixed" in err for err in errors)


def test_imported_html_validation_allows_original_theme_css() -> None:
    raw = _CALC_SHELL.replace(
        "</head>",
        "<style>.wp-lightbox-overlay{position:fixed;left:0;top:0;}</style></head>",
    )
    ok, errors = validate_cinema_html_document(raw, ui_type="imported")
    assert ok, errors
