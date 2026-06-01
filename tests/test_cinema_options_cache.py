from pathlib import Path

from nexu.cinema_options_cache import (
    apply_options_cache,
    options_cache_key,
    read_options_cache,
    write_options_cache,
)


def test_options_cache_key_changes_with_stage_or_ledger() -> None:
    base = options_cache_key(
        stage_html="<html>v1</html>",
        ledger=[],
        focus_scope="colors",
        goal="dark theme",
    )
    other_stage = options_cache_key(
        stage_html="<html>v2</html>",
        ledger=[],
        focus_scope="colors",
        goal="dark theme",
    )
    other_ledger = options_cache_key(
        stage_html="<html>v1</html>",
        ledger=[{"keep": ["btn-1"]}],
        focus_scope="colors",
        goal="dark theme",
    )
    assert base != other_stage
    assert base != other_ledger


def test_write_read_and_apply_options_cache(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache" / "options"
    cinema_dir = tmp_path / "cinema"
    cinema_dir.mkdir()
    files = {
        "alt_a.html": "<html>a</html>",
        "alt_b.html": "<html>b</html>",
        "alt_c.html": "<html>c</html>",
    }
    labels = ["Option A (colors)", "Option B (colors)", "Option C (colors)"]
    key = options_cache_key(
        stage_html="<html>stage</html>",
        ledger=[],
        focus_scope="colors",
        goal="palette",
    )
    write_options_cache(
        cache_root,
        key,
        files=files,
        labels=labels,
        source="offline",
        focus_scope="colors",
        goal="palette",
    )
    cached = read_options_cache(cache_root, key)
    assert cached is not None
    assert cached["labels"] == labels
    written = apply_options_cache(cinema_dir, cached)
    assert written == labels
    assert (cinema_dir / "alt_a.html").read_text(encoding="utf-8") == files["alt_a.html"]
