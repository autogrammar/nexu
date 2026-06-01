from __future__ import annotations

from nexu.cinema_project_ir import build_project_ir, summarize_project_ir


def test_build_project_ir_extracts_functional_outline() -> None:
    html = """
<!DOCTYPE html>
<html><head><title>Site</title></head>
<body>
  <header><h1>Malort Gdynia</h1><a href="/zapisy">Zapisy</a></header>
  <main><section class="hero"><h2>Warsztaty</h2><button>Rezerwuj</button></section></main>
</body></html>
"""

    ir = build_project_ir(html)
    summary = summarize_project_ir(ir)

    assert ir["title"] == "Site"
    assert ir["counts"]["actions"] == 2
    assert any(item["text"] == "Malort Gdynia" for item in ir["headings"])
    assert "Rezerwuj" in summary
