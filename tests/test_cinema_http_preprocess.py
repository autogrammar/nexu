"""Tests for HTTP import preprocessing (visual CSS + HTML outline)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nexu.cinema_http_preprocess import (
    build_html_outline,
    build_http_llm_context,
    ensure_http_preprocess_artifacts,
    extract_visual_css,
    http_preprocess_artifacts_present,
    load_cinema_seed_preprocess_artifacts,
    load_http_preprocess_artifacts,
    prepare_http_preview_html,
    preprocess_cinema_seed,
    preprocess_http_import,
    sanitize_http_preview_html,
)
from nexu.cinema_scope import load_cinema_ui_profile


SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head>
  <style>
    body { color: #112233; background: #fff; font-family: sans-serif; }
    .hero { border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,.2); width: 100%; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .noise { content: "ignore"; }
  </style>
  <link rel="stylesheet" href="assets/theme.css">
</head>
<body id="page" class="landing" data-nexu-target="root">
  <header class="top"><h1>Welcome</h1></header>
  <main class="hero"><p>Long paragraph with lots of marketing copy here.</p></main>
  <script>console.log('skip');</script>
</body>
</html>
"""

LINKED_CSS = """
:root { --accent: #ff5500; }
.card { color: var(--accent); border: 1px solid #ccc; min-height: 120px; }
@media print { body { display: none; } }
.btn { display: flex; gap: 8px; padding: 12px; }
"""


def test_extract_visual_css_keeps_color_and_shape_rules(tmp_path: Path) -> None:
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "theme.css").write_text(LINKED_CSS, encoding="utf-8")
    css, meta = extract_visual_css(SAMPLE_HTML, ["assets/theme.css"], tmp_path)
    assert "color:" in css or "color " in css
    assert "border-radius" in css
    assert "--accent" in css
    assert "display: flex" in css
    assert "@keyframes" not in css
    assert "@media print" not in css
    assert meta["visual_css_bytes"] > 0


def test_build_html_outline_smaller_than_source_and_strips_scripts() -> None:
    outline, meta = build_html_outline(SAMPLE_HTML)
    assert len(outline) < len(SAMPLE_HTML)
    assert "<script" not in outline.lower()
    assert 'id="page"' in outline
    assert 'data-nexu-target="root"' in outline
    assert "Welcome" not in outline
    assert meta["outline_node_count"] >= 4


def test_preprocess_cinema_seed_writes_artifacts_beside_stage0(tmp_path: Path) -> None:
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    (cinema / "stage0.html").write_text(SAMPLE_HTML, encoding="utf-8")

    fields = preprocess_cinema_seed(cinema)

    assert fields["llm_context_mode"] == "patch"
    assert fields["visual_css_path"] == "nexu-visual.css"
    assert fields["html_outline_path"] == "nexu-outline.html"
    assert (cinema / "nexu-visual.css").is_file()
    assert (cinema / "nexu-outline.html").is_file()
    assert fields["visual_css_bytes"] > 0


def test_load_cinema_ui_profile_includes_seed_preprocess(tmp_path: Path) -> None:
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    (cinema / "stage0.html").write_text(SAMPLE_HTML, encoding="utf-8")
    preprocess_fields = preprocess_cinema_seed(cinema)
    active = {"id": "web_app_dashboard", "kind": "dashboard", **preprocess_fields}
    (cinema / "active_project.json").write_text(json.dumps(active), encoding="utf-8")

    profile = load_cinema_ui_profile(active, cinema)

    assert profile["llm_context_mode"] == "patch"
    assert profile["visual_css"]
    assert profile["html_outline"]
    assert profile["ui_type"] == "dashboard"


def test_load_cinema_seed_preprocess_artifacts_reads_active_metadata(tmp_path: Path) -> None:
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    (cinema / "stage0.html").write_text(SAMPLE_HTML, encoding="utf-8")
    preprocess_fields = preprocess_cinema_seed(cinema)
    active = {"id": "vertical_slice", "kind": "slice", **preprocess_fields}

    artifacts = load_cinema_seed_preprocess_artifacts(cinema, active)

    assert artifacts["llm_context_mode"] == "patch"
    assert artifacts["visual_css"]
    assert artifacts["html_outline"]


def test_preprocess_http_import_writes_artifacts(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    assets = source / "assets"
    assets.mkdir()
    (assets / "theme.css").write_text(LINKED_CSS, encoding="utf-8")
    (source / "index.html").write_text(SAMPLE_HTML, encoding="utf-8")
    fetch_meta = {"stylesheets": [{"local": "assets/theme.css"}]}

    fields = preprocess_http_import(source, fetch_meta=fetch_meta)

    assert fields["llm_context_mode"] == "patch"
    assert (source / "nexu-visual.css").is_file()
    assert (source / "nexu-outline.html").is_file()
    assert fields["visual_css_bytes"] > 0
    assert fields["outline_node_count"] >= 4
    outline = (source / "nexu-outline.html").read_text(encoding="utf-8")
    assert len(outline) < len(SAMPLE_HTML)


def test_http_preprocess_artifacts_present_requires_files_and_patch_mode(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.html").write_text(SAMPLE_HTML, encoding="utf-8")
    assert not http_preprocess_artifacts_present(source, {})

    fields = preprocess_http_import(source)
    meta = {"llm_context_mode": "patch", **fields}
    assert http_preprocess_artifacts_present(source, meta)

    (source / "nexu-visual.css").unlink()
    assert not http_preprocess_artifacts_present(source, meta)


def test_ensure_http_preprocess_artifacts_skips_when_present(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.html").write_text(SAMPLE_HTML, encoding="utf-8")
    meta = preprocess_http_import(source)
    assert ensure_http_preprocess_artifacts(source, meta=meta) == {}


def test_ensure_http_preprocess_artifacts_regenerates_when_missing(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.html").write_text(SAMPLE_HTML, encoding="utf-8")
    preprocess_http_import(source)
    (source / "nexu-visual.css").unlink()
    (source / "nexu-outline.html").unlink()

    fields = ensure_http_preprocess_artifacts(source, meta={})
    assert fields["llm_context_mode"] == "patch"
    assert (source / "nexu-visual.css").is_file()
    assert (source / "nexu-outline.html").is_file()


def test_build_http_llm_context_combines_css_and_outline() -> None:
    ctx = build_http_llm_context(
        {
            "visual_css": "body { color: red; }",
            "html_outline": "<body><main>…</main></body>",
        }
    )
    assert "patch mode" in ctx.lower()
    assert "```css" in ctx
    assert "```html" in ctx


def test_build_http_llm_context_includes_organize_manifest() -> None:
    ctx = build_http_llm_context(
        {
            "visual_css": "body { color: red; }",
            "html_outline": "<body></body>",
            "organize": {
                "extracted_files": ["nexu-extracted.css"],
                "tagged_targets_count": 3,
                "stripped_lazy_img_count": 1,
            },
            "extracted_css": ".hero { padding: 1rem; }",
            "source_paths": {
                "index_html": "source/index.html",
                "visual_css": "source/nexu-visual.css",
                "nexu-extracted_css": "source/nexu-extracted.css",
            },
        }
    )
    assert "organize manifest" in ctx.lower()
    assert "nexu-extracted.css" in ctx
    assert "data-nexu-target" in ctx
    assert ".hero { padding: 1rem; }" in ctx
    assert "source/index.html" in ctx


def test_load_http_preprocess_artifacts_includes_organize(tmp_path: Path) -> None:
    cinema = tmp_path / "cinema"
    project_id = "http-example.com"
    project_dir = cinema / "imported_projects" / project_id
    source = project_dir / "source"
    source.mkdir(parents=True)
    (source / "index.html").write_text(SAMPLE_HTML, encoding="utf-8")
    (source / "nexu-extracted.css").write_text(".inline { color: blue; }", encoding="utf-8")
    preprocess_http_import(source)
    (project_dir / "project.json").write_text(
        json.dumps(
            {
                "id": project_id,
                "visual_css_path": "source/nexu-visual.css",
                "html_outline_path": "source/nexu-outline.html",
                "llm_context_mode": "patch",
                "visual_css_bytes": 42,
                "outline_node_count": 7,
                "organize": {
                    "extracted_files": ["nexu-extracted.css"],
                    "tagged_targets_count": 2,
                    "stripped_lazy_img_count": 0,
                },
            }
        ),
        encoding="utf-8",
    )

    artifacts = load_http_preprocess_artifacts(cinema, {"id": project_id, "kind": "imported"})

    assert artifacts["organize"]["tagged_targets_count"] == 2
    assert ".inline { color: blue; }" in artifacts["extracted_css"]
    assert artifacts["source_paths"]["index_html"] == "source/index.html"
    ctx = build_http_llm_context(artifacts)
    assert "Extracted inline CSS" in ctx


def test_load_cinema_ui_profile_includes_http_preprocess(tmp_path: Path) -> None:
    cinema = tmp_path / "cinema"
    project_id = "http-example.com"
    project_dir = cinema / "imported_projects" / project_id
    source = project_dir / "source"
    source.mkdir(parents=True)
    (source / "index.html").write_text(SAMPLE_HTML, encoding="utf-8")
    preprocess_http_import(source)
    (project_dir / "project.json").write_text(
        json.dumps(
            {
                "id": project_id,
                "visual_css_path": "source/nexu-visual.css",
                "html_outline_path": "source/nexu-outline.html",
                "llm_context_mode": "patch",
                "visual_css_bytes": 42,
                "outline_node_count": 7,
            }
        ),
        encoding="utf-8",
    )
    (cinema / "stage0.html").write_text(SAMPLE_HTML, encoding="utf-8")

    profile = load_cinema_ui_profile({"id": project_id, "kind": "imported"}, cinema)

    assert profile["llm_context_mode"] == "patch"
    assert profile["visual_css"]
    assert profile["html_outline"]
    assert profile["ui_type"] == "web"


def test_extract_visual_css_rejects_paths_outside_source_dir(tmp_path: Path) -> None:
    outside = tmp_path / "outside.css"
    outside.write_text("body { color: blue; }", encoding="utf-8")
    css, _ = extract_visual_css(SAMPLE_HTML, [str(outside)], tmp_path / "source")
    assert "color: blue" not in css


LITESPEED_FIXTURE = """<!DOCTYPE html>
<html>
<head>
  <base href="https://malortgdynia.pl/">
  <link rel="stylesheet" href="/wp-content/themes/kadence/style.css">
  <script src="https://malortgdynia.pl/wp-includes/js/jquery.min.js"></script>
  <script src="/wp-content/plugins/litespeed-cache/assets/js/instant_click.min.js"></script>
  <script>
    fetch('https://malortgdynia.pl/wp-content/plugins/litespeed-cache/guest.vary.php')
      .then(function(r){ return r.json(); })
      .then(function(d){ window.__lsc = d; });
  </script>
</head>
<body><h1>Malort</h1></body>
</html>
"""


def test_sanitize_http_preview_strips_external_and_fetch_scripts() -> None:
    cleaned, meta = sanitize_http_preview_html(LITESPEED_FIXTURE)
    assert meta["preview_scripts_removed"] == 3
    assert "guest.vary.php" not in cleaned
    assert "fetch(" not in cleaned
    assert "jquery.min.js" not in cleaned
    assert "instant_click.min.js" not in cleaned
    assert 'href="/wp-content/themes/kadence/style.css"' in cleaned
    assert "<h1>Malort</h1>" in cleaned


def test_prepare_http_preview_injects_network_shim() -> None:
    prepared, meta = prepare_http_preview_html(LITESPEED_FIXTURE)
    assert meta["preview_shim_injected"] is True
    assert "nexu preview: block cross-origin fetch" in prepared
    assert "window.kadenceConfig" in prepared
    assert prepared.index("nexu preview: block cross-origin fetch") < prepared.lower().index("<link")


def test_prepare_http_preview_with_shield_keeps_network_shim() -> None:
    from nexu.cinema_scripts import inject_cinema_shield

    prepared, _ = prepare_http_preview_html(LITESPEED_FIXTURE)
    body = inject_cinema_shield(
        prepared.replace(
            "<body>",
            '<body data-nexu-import-preview="http">',
            1,
        )
    )
    assert "nexu preview: block cross-origin fetch" in body
    assert "const NEXU_PARAMS = new URLSearchParams" in body
    assert "isHttpImportPreview" in body
    assert "SELECTOR_HTTP" in body
    assert "'p'" in body
    assert '\'img[alt]:not([alt=""])' in body
