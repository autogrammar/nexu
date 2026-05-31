import json
from pathlib import Path

from nexu.cinema_offline_options import (
    build_chemical_option_html,
    build_policy_scientific_option_html,
    is_chemical_goal,
    write_goal_options_offline,
)
from nexu.cinema_policy import enforce_deletes_on_option_previews


def test_is_chemical_goal():
    assert is_chemical_goal(["Chemical & scientific keypad evolution"])
    assert is_chemical_goal(["chemiczny"])
    assert not is_chemical_goal(["dashboard widgets"])


def test_write_chemical_options(tmp_path: Path):
    labels = write_goal_options_offline(
        tmp_path,
        keep_els=["sin", "cos", "7", "8"],
        hints=["Chemical calculator"],
    )
    assert len(labels) == 3
    for name in ("alt_a.html", "alt_b.html", "alt_c.html"):
        html = (tmp_path / name).read_text(encoding="utf-8")
        assert "btn-chem" in html or "btn-H" in html or 'id="btn-H"' in html
        assert "NEXU_MARK" in html or "nexuParam" in html


def test_calculator_chemical_goal_respects_colors_scope(tmp_path: Path):
    (tmp_path / "active_project.json").write_text(
        json.dumps({"id": "web_app_calculator", "kind": "calculator"}),
        encoding="utf-8",
    )
    (tmp_path / "stage0.html").write_text(
        '<div class="calc-body"><div class="screen" id="screen">0</div></div>',
        encoding="utf-8",
    )
    labels = write_goal_options_offline(
        tmp_path,
        keep_els=[],
        hints=["Chemical & scientific keypad evolution"],
        user_goal="Chemical & scientific keypad evolution",
        focus_scope="colors",
    )
    assert labels[0] == "Option A (colors: cool)"
    assert "colors:" in labels[1]
    assert "colors:" in labels[2]
    assert "chemical minimal" not in " ".join(labels).lower()
    html = (tmp_path / "alt_a.html").read_text(encoding="utf-8")
    assert "nexu-scope-variant" in html
    assert "btn-chem" in html or 'id="btn-H"' in html


def test_chemical_html_has_elements():
    html = build_chemical_option_html("a", [])
    assert "btn-H" in html
    assert "molar" in html.lower() or "g/mol" in html


def test_policy_scientific_includes_mandatory_trig():
    html = build_policy_scientific_option_html(
        "b",
        ["cos", "tan", "log", "ln", "7", "8"],
    )
    for key in ("cos", "tan", "log", "ln"):
        assert f'id="btn-{key}"' in html


def test_policy_options_a_and_b_differ():
    keep = ["cos", "tan", "log", "ln", "7", "8", "add"]
    html_a = build_policy_scientific_option_html("a", keep)
    html_b = build_policy_scientific_option_html("b", keep)
    html_c = build_policy_scientific_option_html("c", keep)
    assert html_a != html_b != html_c
    assert 'data-variant="minimal"' in html_a
    assert 'data-variant="standard"' in html_b
    assert 'data-variant="expanded"' in html_c
    assert 'id="btn-pow2"' in html_a
    assert 'id="btn-lp"' in html_b
    assert 'id="btn-pow2"' not in html_b
    assert "12.5 · A ·" in html_a
    assert "12.5 · B ·" in html_b


def test_calculator_cinema_uses_scientific_offline(tmp_path: Path):
    (tmp_path / "stage0.html").write_text(
        '<div class="calc-body"><div class="screen" id="screen">Simple Calc</div>'
        '<div id="btn-eq">=</div></div>',
        encoding="utf-8",
    )
    labels = write_goal_options_offline(tmp_path, keep_els=[], delete_els=[], hints=[])
    assert labels[0] == "Option A (minimal)"
    a = (tmp_path / "alt_a.html").read_text(encoding="utf-8")
    b = (tmp_path / "alt_b.html").read_text(encoding="utf-8")
    assert a != b
    assert 'data-variant="minimal"' in a


def test_dashboard_project_does_not_reuse_stale_calculator_options(tmp_path: Path):
    (tmp_path / "active_project.json").write_text(
        json.dumps({"id": "web_app_dashboard", "kind": "dashboard"}),
        encoding="utf-8",
    )
    (tmp_path / "stage0.html").write_text(
        "<!DOCTYPE html><html><head><title>Dashboard S0</title></head>"
        "<body><h1>System Dashboard (S0)</h1></body></html>",
        encoding="utf-8",
    )
    (tmp_path / "stage1.html").write_text(
        "<!DOCTYPE html><html><head><title>Dashboard S1</title></head>"
        "<body><h1>KPI Cards (S1)</h1></body></html>",
        encoding="utf-8",
    )
    (tmp_path / "stage2.html").write_text(
        "<!DOCTYPE html><html><head><title>Dashboard S2</title></head>"
        "<body><h1>Charts and Filters (S2)</h1></body></html>",
        encoding="utf-8",
    )
    (tmp_path / "alt_a.html").write_text(
        '<div class="calc-body"><div id="btn-cos">cos</div></div>',
        encoding="utf-8",
    )

    labels = write_goal_options_offline(
        tmp_path,
        keep_els=["cos", "tan", "7"],
        delete_els=["sin"],
        hints=["KPI cards, charts, and filters"],
    )

    assert labels[0] == "Option A (functions: overview)"
    assert "functions:" in labels[1]
    alt_a = (tmp_path / "alt_a.html").read_text(encoding="utf-8")
    alt_b = (tmp_path / "alt_b.html").read_text(encoding="utf-8")
    alt_c = (tmp_path / "alt_c.html").read_text(encoding="utf-8")
    assert "System Dashboard" in alt_a
    assert "KPI Cards" in alt_b
    assert "Charts and Filters" in alt_c
    assert "calc-body" not in alt_a


def test_offline_chemical_from_goal_contract_lines(tmp_path: Path):
    labels = write_goal_options_offline(
        tmp_path,
        keep_els=["sin", "cos"],
        hints=[],
        user_goal="UI for engineers",
        goal_contract_lines=["# @intract.v1 intent:evolve:chemical_calculator"],
    )
    assert len(labels) == 3
    html = (tmp_path / "alt_a.html").read_text(encoding="utf-8")
    assert "btn-chem" in html or 'id="btn-H"' in html


def test_offline_scientific_screen_shows_goal(tmp_path: Path):
    labels = write_goal_options_offline(
        tmp_path,
        keep_els=["cos", "tan", "7", "8"],
        hints=[],
        user_goal="precision engineering readout",
    )
    assert labels
    html = (tmp_path / "alt_a.html").read_text(encoding="utf-8")
    assert "🎯" in html
    assert "engineering" in html


def test_dashboard_seed_with_calc_body_class_stays_project_options(tmp_path: Path):
    (tmp_path / "active_project.json").write_text(
        json.dumps({"id": "web_app_analytics", "kind": "dashboard"}),
        encoding="utf-8",
    )
    for stage in (0, 1, 2):
        (tmp_path / f"stage{stage}.html").write_text(
            f"<!DOCTYPE html><html><head><title>Analytics S{stage}</title></head>"
            f"<body><div class='calc-body'><div id='btn-kpi'>kpi S{stage}</div></div>"
            "</body></html>",
            encoding="utf-8",
        )

    labels = write_goal_options_offline(
        tmp_path,
        keep_els=["kpi"],
        delete_els=[],
        hints=["analytics dashboard"],
    )

    assert labels[0] == "Option A (functions: overview)"
    assert "kpi S0" in (tmp_path / "alt_a.html").read_text(encoding="utf-8")
    assert "kpi S1" in (tmp_path / "alt_b.html").read_text(encoding="utf-8")


def test_enforce_deletes_respects_session_rekeep(tmp_path: Path):
    """Ledger may still list DELETE; session re-KEEP must win when patching alts."""
    for name in ("alt_a.html", "alt_b.html", "alt_c.html"):
        (tmp_path / name).write_text(
            '<div id="btn-5">5</div><div id="btn-7">7</div>',
            encoding="utf-8",
        )
    enforce_deletes_on_option_previews(
        tmp_path,
        delete_ids=["5"],
        session_keep=["5"],
        session_delete=[],
    )
    for name in ("alt_a.html", "alt_b.html", "alt_c.html"):
        assert 'id="btn-5"' in (tmp_path / name).read_text(encoding="utf-8")


def test_write_policy_options_without_chemical_hints(tmp_path: Path):
    labels = write_goal_options_offline(
        tmp_path,
        keep_els=["cos", "tan", "log", "ln", "0", "1", "add"],
        delete_els=["EXP", "sin"],
        hints=[],
    )
    assert labels[0] == "Option A (minimal)"
    alt_a = (tmp_path / "alt_a.html").read_text(encoding="utf-8")
    alt_b = (tmp_path / "alt_b.html").read_text(encoding="utf-8")
    alt_c = (tmp_path / "alt_c.html").read_text(encoding="utf-8")
    assert alt_a != alt_b
    assert alt_b != alt_c
    for html in (alt_a, alt_b, alt_c):
        for key in ("cos", "tan", "log", "ln"):
            assert f'id="btn-{key}"' in html
        assert "btn-EXP" not in html
        assert "btn-sin" not in html


def test_policy_options_restore_digit_after_delete(tmp_path: Path):
    """Re-marking a digit as KEEP after DELETE must bring it back in all variants."""
    keep = ["7", "8", "9", "4", "6", "1", "2", "3", "5", "cos", "tan", "add", "div"]
    labels = write_goal_options_offline(
        tmp_path,
        keep_els=keep,
        delete_els=["EXP", "sin"],
        hints=[],
    )
    assert len(labels) == 3
    for name in ("alt_a.html", "alt_b.html", "alt_c.html"):
        html = (tmp_path / name).read_text(encoding="utf-8")
        assert 'id="btn-5"' in html, f"{name} missing digit 5 after re-keep"


def test_minimal_policy_keeps_all_marked_keys_even_when_compact(tmp_path: Path):
    keep = [
        "tan",
        "ln",
        "7",
        "8",
        "9",
        "4",
        "5",
        "6",
        "1",
        "2",
        "3",
        "0",
        "eq",
        "add",
    ]

    labels = write_goal_options_offline(
        tmp_path,
        keep_els=keep,
        delete_els=["ln", "add"],
        hints=[],
    )

    assert labels[0] == "Option A (minimal)"
    alt_a = (tmp_path / "alt_a.html").read_text(encoding="utf-8")
    for key in ("tan", "ln", "7", "8", "9", "4", "5", "0", "eq", "add"):
        assert f'id="btn-{key}"' in alt_a


def test_chemical_minimal_respects_keep_science_and_keep_wins_delete(tmp_path: Path):
    labels = write_goal_options_offline(
        tmp_path,
        keep_els=["tan", "ln", "7", "8", "9", "0", "add"],
        delete_els=["tan", "ln", "add"],
        hints=["chemical calculator"],
    )

    assert labels[0] == "Option A (chemical minimal)"
    alt_a = (tmp_path / "alt_a.html").read_text(encoding="utf-8")
    for key in ("tan", "ln", "7", "8", "9", "0", "add"):
        assert f'id="btn-{key}"' in alt_a


def test_chemical_goal_title_is_not_inside_calculator_screen():
    html = build_chemical_option_html(
        "a",
        [],
        user_goal="Chemical & scientific keypad evolution",
    )

    assert 'id="calc-title">Chemical &amp; scientific keypad evolution' in html
    screen = html.split('id="screen"', 1)[1].split("</div>", 1)[0]
    assert "Chemical & scientific keypad evolution" not in screen
    assert "H₂O → 18.02 g/mol" in screen


def test_write_chemical_options_respects_deletes(tmp_path: Path):
    labels = write_goal_options_offline(
        tmp_path,
        keep_els=["sin", "cos"],
        delete_els=["Mod", "deg"],
        hints=["chemiczny"],
    )
    assert len(labels) == 3
    html = (tmp_path / "alt_c.html").read_text(encoding="utf-8")
    assert "btn-Mod" not in html
    assert "btn-deg" not in html
    assert "btn-sin" in html
