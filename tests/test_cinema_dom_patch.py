from __future__ import annotations

from nexu.cinema_dom_patch import (
    build_function_option_patches,
    build_function_patch_context,
    supports_function_patch,
)

HTML = """
<!DOCTYPE html>
<html>
<head><title>Malort Gdynia</title></head>
<body>
  <header><h1>Malort Gdynia</h1><nav><a href="/kontakt">Kontakt</a></nav></header>
  <main><section class="hero"><h2>Przestrzeń kreatywności</h2></section></main>
</body>
</html>
"""


def test_build_function_option_patches_returns_valid_abc() -> None:
    files, labels, meta = build_function_option_patches(
        HTML,
        user_goal="klienci social media 18-33",
        project_kind="imported",
    )

    assert meta["status"] == "ok"
    assert labels == [
        "Option A (functions: quick path)",
        "Option B (functions: workflow)",
        "Option C (functions: funnel)",
    ]
    assert set(files) == {"alt_a.html", "alt_b.html", "alt_c.html"}
    assert "nexu-function-evolution" in files["alt_a.html"]
    assert "klienci social media 18-33" in files["alt_b.html"]
    assert "<script" not in files["alt_c.html"].lower()


def test_build_function_option_patches_xpatches_delete_marks() -> None:
    html_with_control = HTML.replace(
        "</header>",
        '<a class="btn" id="btn-old" href="#old">Old</a></header>',
    )
    files, labels, meta = build_function_option_patches(
        html_with_control,
        user_goal="audience",
        project_kind="imported",
        delete_els=["old"],
    )

    assert meta["status"] == "ok"
    assert labels
    assert "btn-old" in files["alt_a.html"].lower()
    assert 'data-nexu-function-xpatch="a"' in files["alt_a.html"]
    assert "Sprawdź: audience" in files["alt_a.html"]
    assert "Umów krok: audience" in files["alt_b.html"]
    assert "nexu-function-evolution" in files["alt_a.html"]


def test_build_function_option_patches_allows_imported_theme_css() -> None:
    wordpress_html = HTML.replace(
        "</head>",
        (
            "<style>"
            "@import url('https://fonts.googleapis.com/css?family=Jost');"
            ".wp-lightbox-overlay{position:fixed;left:0;top:0;}"
            "</style></head>"
        ),
    )
    files, labels, meta = build_function_option_patches(
        wordpress_html,
        user_goal="audience",
        project_kind="imported",
        delete_els=["Kontakt"],
    )

    assert meta["status"] == "ok"
    assert labels
    assert set(files) == {"alt_a.html", "alt_b.html", "alt_c.html"}


def test_function_patch_context_is_compact_ir() -> None:
    context = build_function_patch_context(HTML, user_goal="audience")

    assert "FUNCTION PATCH IR" in context
    assert "Malort Gdynia" in context
    assert "user_goal: audience" in context


def test_supports_function_patch_only_for_web_like_projects() -> None:
    assert supports_function_patch("functions", "imported")
    assert supports_function_patch("functions", "dashboard")
    assert not supports_function_patch("colors", "imported")
    assert not supports_function_patch("functions", "calculator")
