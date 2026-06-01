import json
from pathlib import Path

from nexu.cinema_offline_options import write_goal_options_offline
from nexu.cinema_project_imports import import_http_project
from nexu.cinema_scope import (
    allowed_scope_ids,
    can_use_offline_fast_iterate,
    cinema_has_offline_baseline,
    default_scope_for_kind,
    inject_scope_style,
    load_cinema_ui_profile,
    normalize_focus_scope,
    offline_fast_scopes_for_kind,
    scope_option_variants,
    scope_supports_offline_fast_path,
    scoped_html_fragment,
    strip_scope_style,
)


def test_dashboard_disallows_keypad_scope():
    assert "keypad" not in allowed_scope_ids("dashboard")
    assert normalize_focus_scope("keypad", "dashboard") == "functions"
    assert default_scope_for_kind("dashboard") == "functions"


def test_calculator_allows_keypad_scope():
    assert "keypad" in allowed_scope_ids("calculator")
    assert normalize_focus_scope("keypad", "calculator") == "keypad"


def test_offline_fast_scopes_per_kind():
    calc = offline_fast_scopes_for_kind("calculator")
    assert "colors" in calc
    assert "keypad" in calc
    assert "functions" not in calc
    dash = offline_fast_scopes_for_kind("dashboard")
    assert "colors" in dash
    assert "keypad" not in dash
    assert scope_supports_offline_fast_path("colors", "calculator")
    assert scope_supports_offline_fast_path("keypad", "calculator")
    assert not scope_supports_offline_fast_path("functions", "calculator")
    assert scope_supports_offline_fast_path("colors", "dashboard")


def test_dashboard_colors_offline_labels(tmp_path: Path):
    (tmp_path / "active_project.json").write_text(
        '{"id":"web_app_dashboard","kind":"dashboard"}',
        encoding="utf-8",
    )
    for name in ("stage0.html", "stage1.html", "stage2.html"):
        (tmp_path / name).write_text(
            "<!DOCTYPE html><html><head></head><body>"
            "<div class='app-shell kpi-grid'></div></body></html>",
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


def test_scoped_html_fragment_for_calculator_colors() -> None:
    html = (
        "<html><body><div class='calc-body'>"
        "<div class='screen'>0</div></div></body></html>"
    )
    fragment = scoped_html_fragment(html, "colors", "calculator")
    assert fragment is not None
    assert "calc-body" in fragment


def test_cinema_has_offline_baseline(tmp_path: Path) -> None:
    assert not cinema_has_offline_baseline(tmp_path)
    (tmp_path / "stage0.html").write_text("<html><body>x</body></html>", encoding="utf-8")
    assert not cinema_has_offline_baseline(tmp_path)
    html = "<!DOCTYPE html><html><body>" + ("x" * 200) + "</body></html>"
    (tmp_path / "stage0.html").write_text(html, encoding="utf-8")
    assert cinema_has_offline_baseline(tmp_path)


def test_inject_scope_style_calculator_colors():
    html = (
        "<html><head></head><body><div class='calc-body'>"
        "<div class='screen'></div></div></body></html>"
    )
    patched = inject_scope_style(html, "colors", "b", project_kind="calculator")
    assert "nexu-scope-variant" in patched
    assert ".calc-body" in patched
    assert "#facc15" in patched


def test_load_cinema_ui_profile_from_active_and_stage(tmp_path: Path) -> None:
    (tmp_path / "stage0.html").write_text(
        "<html><body><div class='calc-body'><div class='btn-eq'></div></div></body></html>",
        encoding="utf-8",
    )
    profile = load_cinema_ui_profile({"kind": "", "title": "Demo"}, tmp_path)
    assert profile["ui_type"] == "calculator"
    profile = load_cinema_ui_profile({"kind": "dashboard", "title": "Ops"}, tmp_path)
    assert profile["ui_type"] == "dashboard"


def test_ui_profile_ignores_runtime_script_tokens(tmp_path: Path) -> None:
    (tmp_path / "stage0.html").write_text(
        "<!DOCTYPE html><html><body><main>Imported page</main>"
        "<script>if (id === 'btn-eq') return '=';</script></body></html>",
        encoding="utf-8",
    )

    profile = load_cinema_ui_profile({"kind": "imported", "title": "Site"}, tmp_path)

    assert profile["ui_type"] == "web"


def test_can_use_offline_fast_iterate(tmp_path: Path) -> None:
    html = "<!DOCTYPE html><html><body>" + ("x" * 200) + "</body></html>"
    (tmp_path / "stage0.html").write_text(html, encoding="utf-8")
    assert can_use_offline_fast_iterate("colors", "calculator", tmp_path)
    assert not can_use_offline_fast_iterate("functions", "calculator", tmp_path)
    assert not can_use_offline_fast_iterate(
        "colors",
        "calculator",
        tmp_path,
        force_llm=True,
    )
    assert not can_use_offline_fast_iterate(
        "colors",
        "calculator",
        tmp_path,
        fast_scope_options=False,
    )
    assert not can_use_offline_fast_iterate("colors", "calculator", tmp_path / "missing")
    assert can_use_offline_fast_iterate("colors", "imported", tmp_path)


def test_imported_kind_uses_web_scopes() -> None:
    assert "keypad" not in allowed_scope_ids("imported")
    assert default_scope_for_kind("imported") == "functions"


def test_http_import_offline_colors_keeps_site_markers(tmp_path: Path, monkeypatch) -> None:
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    body = (
        b"<!DOCTYPE html><html><head></head>"
        b'<body data-nexu-import-preview="http"><main id="site-hero">'
        b"<h1>Malort Site</h1></main></body></html>"
    )

    class FakeResp:
        headers = {"Content-Type": "text/html; charset=utf-8"}
        url = "https://malort.example/"

        def __init__(self):
            self._done = False

        def read(self, n=-1):
            if self._done:
                return b""
            self._done = True
            return body if n == -1 else body[: max(n, 0)]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        "nexu.cinema_project_imports.urlopen",
        lambda req, timeout=0: FakeResp(),
    )
    imported = import_http_project(cinema, "https://malort.example/", allow_network=True)
    project_id = imported["project"]["id"]
    (cinema / "alt_a.html").write_text(
        '<div class="calc-body"><div class="screen" id="screen">0</div></div>',
        encoding="utf-8",
    )
    (cinema / "intract_policy_ledger.json").write_text(
        '[{"stage":0,"keep":["sin","cos"],"delete":["log"]}]',
        encoding="utf-8",
    )

    labels = write_goal_options_offline(
        cinema,
        keep_els=["sin", "cos"],
        delete_els=["log"],
        user_goal="nowoczesny design strony dla młodych",
        focus_scope="colors",
    )

    assert any("colors:" in label for label in labels)
    for name in ("alt_a.html", "alt_b.html", "alt_c.html"):
        html = (cinema / name).read_text(encoding="utf-8")
        assert "Malort Site" in html
        assert 'data-nexu-import-preview="http"' in html
        assert "calc-body" not in html
        assert "nexu-scope-variant" in html
    policy = json.loads((cinema / "intract_policy.json").read_text(encoding="utf-8"))
    assert policy["capsule"]["is_calculator"] is False
    assert project_id.startswith("http-")
