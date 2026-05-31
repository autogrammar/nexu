from pathlib import Path

from nexu.cinema_offline_options import write_goal_options_offline
from nexu.cinema_scope import (
    allowed_scope_ids,
    default_scope_for_kind,
    inject_scope_style,
    normalize_focus_scope,
    scope_option_variants,
    strip_scope_style,
)


def test_dashboard_disallows_keypad_scope():
    assert "keypad" not in allowed_scope_ids("dashboard")
    assert normalize_focus_scope("keypad", "dashboard") == "functions"
    assert default_scope_for_kind("dashboard") == "functions"


def test_calculator_allows_keypad_scope():
    assert "keypad" in allowed_scope_ids("calculator")
    assert normalize_focus_scope("keypad", "calculator") == "keypad"


def test_dashboard_colors_offline_labels(tmp_path: Path):
    (tmp_path / "active_project.json").write_text(
        '{"id":"web_app_dashboard","kind":"dashboard"}',
        encoding="utf-8",
    )
    for name in ("stage0.html", "stage1.html", "stage2.html"):
        (tmp_path / name).write_text(
            f"<!DOCTYPE html><html><head></head><body><div class='app-shell kpi-grid'></div></body></html>",
            encoding="utf-8",
        )
    labels = write_goal_options_offline(
        tmp_path,
        user_goal="KPI cards",
        focus_scope="colors",
    )
    assert any("colors:" in label for label in labels)
    html = (tmp_path / "alt_a.html").read_text(encoding="utf-8")
    assert "nexu-scope-variant" in html


def test_scope_option_variants_dashboard_functions():
    specs = scope_option_variants("functions", "dashboard")
    assert specs[0][1].startswith("Option A (functions:")


def test_strip_and_inject_scope_style():
    html = "<html><head></head><body></body></html>"
    patched = inject_scope_style(html, "shapes", "c", project_kind="dashboard")
    assert "nexu-scope-variant" in patched
    assert "border-radius:999px" in patched
    assert strip_scope_style(patched) == html


def test_inject_scope_style_calculator_colors():
    html = (
        "<html><head></head><body><div class='calc-body'>"
        "<div class='screen'></div></div></body></html>"
    )
    patched = inject_scope_style(html, "colors", "b", project_kind="calculator")
    assert "nexu-scope-variant" in patched
    assert ".calc-body" in patched
    assert "#facc15" in patched
