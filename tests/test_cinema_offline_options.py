from pathlib import Path

from nexu.cinema_offline_options import (
    build_chemical_option_html,
    build_policy_scientific_option_html,
    is_chemical_goal,
    write_goal_options_offline,
)


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


def test_write_policy_options_without_chemical_hints(tmp_path: Path):
    labels = write_goal_options_offline(
        tmp_path,
        keep_els=["cos", "tan", "log", "ln", "0", "1", "add"],
        delete_els=["EXP", "sin"],
        hints=[],
    )
    assert labels[0] == "Option A (minimal)"
    for name in ("alt_a.html", "alt_b.html", "alt_c.html"):
        html = (tmp_path / name).read_text(encoding="utf-8")
        for key in ("cos", "tan", "log", "ln"):
            assert f'id="btn-{key}"' in html
        assert "btn-EXP" not in html
        assert "btn-sin" not in html


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
