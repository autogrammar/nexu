from pathlib import Path

from nexu.cinema_markpact import build_markpact_readme, markpact_download_filename


def test_build_markpact_readme(tmp_path: Path):
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    (cinema / "stage0.html").write_text(
        "<!DOCTYPE html><html><head><title>Chem Calc</title></head>"
        "<body><div id='screen'>0</div></body></html>",
        encoding="utf-8",
    )

    md = build_markpact_readme(
        cinema,
        stage=0,
        capsule_name="scientific_calc",
        user_goal="kalkulator chemiczny",
        effective_ui={"keep": ["sin"], "delete": ["cos"]},
    )

    assert "markpact:file path=index.html" in md
    assert "markpact:run" in md
    assert "Chem Calc" in md
    assert "kalkulator chemiczny" in md
    assert "sin" in md and "cos" in md
    assert "btn-screen" not in md  # raw html preserved


def test_markpact_download_filename():
    assert markpact_download_filename("scientific_calc", 0) == "scientific_calc-S0-markpact.md"
