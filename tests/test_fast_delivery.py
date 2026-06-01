from __future__ import annotations

from nexu.fast_delivery import (
    choose_options_route,
    compact_html_for_llm,
    compact_markpact_for_llm,
    effective_markpact_mode,
    is_options_ready_status,
    options_source_label,
    read_cached_options,
    read_option_files,
    store_options_cache,
)


def test_choose_options_route_prefers_cache() -> None:
    route = choose_options_route(
        cache_hit=True,
        force_refresh=False,
        llm_patch_options=True,
        llm_patch_supported=True,
        fast_scope_options=True,
        offline_supported=True,
        option_generation_mode="batch",
    )

    assert route.name == "cache"
    assert route.status == "proposed_options_cached"
    assert not route.requires_llm


def test_choose_options_route_uses_llm_patch_before_offline() -> None:
    route = choose_options_route(
        cache_hit=False,
        force_refresh=False,
        llm_patch_options=True,
        llm_patch_supported=True,
        fast_scope_options=True,
        offline_supported=True,
        option_generation_mode="batch",
    )

    assert route.name == "llm_patch"
    assert route.status == "proposed_options_by_llm_patch"
    assert route.requires_llm


def test_choose_options_route_falls_back_to_offline() -> None:
    route = choose_options_route(
        cache_hit=False,
        force_refresh=False,
        llm_patch_options=False,
        llm_patch_supported=True,
        fast_scope_options=True,
        offline_supported=True,
        option_generation_mode="batch",
    )

    assert route.name == "offline"
    assert route.status == "proposed_options_offline"


def test_choose_options_route_falls_back_to_parallel_llm() -> None:
    route = choose_options_route(
        cache_hit=False,
        force_refresh=False,
        llm_patch_options=False,
        llm_patch_supported=False,
        fast_scope_options=False,
        offline_supported=False,
        option_generation_mode="parallel",
    )

    assert route.name == "llm_parallel"
    assert route.status == "proposed_options_by_llm"


def test_options_status_helpers() -> None:
    assert is_options_ready_status("proposed_options_by_llm_patch")
    assert options_source_label("proposed_options_by_llm_patch") == "LLM patch"
    assert options_source_label("proposed_options_cached") == "cache"


def test_compact_html_for_llm_removes_scripts_and_limits() -> None:
    html = "<html><body><script>alert(1)</script><main>" + ("x" * 100) + "</main></body></html>"

    compact = compact_html_for_llm(html, limit=40)

    assert "<script" not in compact
    assert "current html context truncated" in compact


def test_markpact_context_helpers() -> None:
    assert (
        effective_markpact_mode(
            "colors",
            "calculator",
            default_mode="summary",
        )
        == "off"
    )
    markdown = """
## Nexu context
keep this

## Application UI

```html markpact:file path=index.html
<html>huge</html>
```

## Other
drop this
"""
    compact = compact_markpact_for_llm(markdown, mode="summary", limit=80)
    assert "keep this" in compact
    assert "huge" not in compact


def test_fast_delivery_options_cache_roundtrip(tmp_path) -> None:
    cinema_dir = tmp_path / "cinema"
    cache_dir = cinema_dir / "cache" / "options"
    cinema_dir.mkdir()
    files = {
        "alt_a.html": "<html>A</html>",
        "alt_b.html": "<html>B</html>",
        "alt_c.html": "<html>C</html>",
    }

    key = store_options_cache(
        cache_dir=cache_dir,
        enabled=True,
        stage_html="<html>stage</html>",
        ledger=[],
        focus_scope="colors",
        goal="",
        keep_els=[],
        delete_els=[],
        files=files,
        labels=["A", "B", "C"],
        source="test",
    )
    hit = read_cached_options(
        cinema_dir=cinema_dir,
        cache_dir=cache_dir,
        enabled=True,
        stage_html="<html>stage</html>",
        ledger=[],
        focus_scope="colors",
        goal="",
        keep_els=[],
        delete_els=[],
    )

    assert key
    assert hit == (["A", "B", "C"], key)
    written = read_option_files(cinema_dir)
    assert set(written) == set(files)
    assert "A" in written["alt_a.html"]
    assert written["alt_a.html"].startswith("<!DOCTYPE html>")


def test_fast_delivery_options_cache_rejects_invalid_cached_html(tmp_path) -> None:
    cinema_dir = tmp_path / "cinema"
    cache_dir = cinema_dir / "cache" / "options"
    cinema_dir.mkdir()
    key = store_options_cache(
        cache_dir=cache_dir,
        enabled=True,
        stage_html="<html>stage</html>",
        ledger=[],
        focus_scope="colors",
        goal="",
        keep_els=[],
        delete_els=[],
        files={
            "alt_a.html": "<html><body>missing calc controls</body></html>",
            "alt_b.html": "<html><body>missing calc controls</body></html>",
            "alt_c.html": "<html><body>missing calc controls</body></html>",
        },
        labels=["A", "B", "C"],
        source="test",
    )

    hit = read_cached_options(
        cinema_dir=cinema_dir,
        cache_dir=cache_dir,
        enabled=True,
        stage_html="<html>stage</html>",
        ledger=[],
        focus_scope="colors",
        goal="",
        keep_els=[],
        delete_els=[],
        ui_type="calculator",
    )

    assert key
    assert hit is None
    assert not (cinema_dir / "alt_a.html").exists()


def test_fast_delivery_options_cache_rejects_calculator_for_web_stage(tmp_path) -> None:
    cinema_dir = tmp_path / "cinema"
    cache_dir = cinema_dir / "cache" / "options"
    cinema_dir.mkdir()
    calc_doc = """
<!DOCTYPE html>
<html><head><title>Calc</title></head>
<body><div class="calc-body"><div id="screen">0</div>
<button class="btn">7</button></div></body></html>
"""
    key = store_options_cache(
        cache_dir=cache_dir,
        enabled=True,
        stage_html="<html><body><main>website</main></body></html>",
        ledger=[],
        focus_scope="colors",
        goal="",
        keep_els=[],
        delete_els=[],
        files={"alt_a.html": calc_doc, "alt_b.html": calc_doc, "alt_c.html": calc_doc},
        labels=["A", "B", "C"],
        source="test",
    )

    hit = read_cached_options(
        cinema_dir=cinema_dir,
        cache_dir=cache_dir,
        enabled=True,
        stage_html="<!DOCTYPE html><html><body><main>website</main></body></html>",
        ledger=[],
        focus_scope="colors",
        goal="",
        keep_els=[],
        delete_els=[],
        ui_type="web",
    )

    assert key
    assert hit is None
    assert not (cinema_dir / "alt_a.html").exists()
