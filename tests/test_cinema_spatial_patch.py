from nexu.cinema_scripts import apply_spatial_deletes_to_html, finalize_cinema_html


def test_apply_spatial_deletes_removes_dashboard_kpi_card():
    html = """<!DOCTYPE html><html><body>
    <section class="kpi-card nexu-selectable" id="btn-GET" data-nexu-target="GET">
        <span>Get</span><strong>2.1k</strong></section>
    <section class="kpi-card nexu-selectable" id="btn-POST" data-nexu-target="POST">
        <span>Post</span><strong>38 ms</strong></section>
    </body></html>"""
    patched, removed = apply_spatial_deletes_to_html(html, ["GET"])
    assert "btn-GET" not in patched
    assert "btn-POST" in patched
    assert removed


def test_apply_spatial_deletes_removes_only_marked_buttons():
    html = """<!DOCTYPE html><html><body><div class="grid">
    <div class="btn btn-sci" id="btn-sin">sin</div>
    <div class="btn btn-sci-excess" id="btn-Mod">Mod</div>
    <div class="btn btn-sci-excess" id="btn-deg">deg</div>
    <div class="btn btn-sci-excess" id="btn-rad">rad</div>
    <div class="btn btn-sci-excess" id="btn-pi">π</div>
    </div></body></html>"""
    base = finalize_cinema_html(html)
    patched, removed = apply_spatial_deletes_to_html(base, ["Mod", "deg", "rad"])
    assert set(removed) == {"Mod", "deg", "rad"}
    assert "btn-Mod" not in patched and "btn-deg" not in patched and "btn-rad" not in patched
    assert "btn-sin" in patched and "btn-pi" in patched
