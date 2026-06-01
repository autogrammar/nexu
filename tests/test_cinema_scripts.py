from nexu.cinema_scripts import finalize_cinema_html, inject_cinema_shield


def test_finalize_strips_truncated_llm_script_and_injects_canonical():
    broken = """<!DOCTYPE html>
<html><body><div id="screen">H2O</div>
<script>
document.addEventListener('mouseup', () => {
  const x = elRect.left ></script></body></html>"""
    out = finalize_cinema_html(broken)
    assert "elRect.left ></script>" not in out
    assert "[NEXU IFRAME]" in out
    assert "molarMass" in out
    assert out.lower().count("<script") >= 2


def test_finalize_marks_web_gui_components_as_selectable_targets():
    html = """<!DOCTYPE html><html><body>
    <section class="kpi-card" id="btn-revenue">Revenue</section>
    <section class="chart-card" id="btn-chart">Chart</section>
    <div class="nav-item" data-nexu-target="nav-overview">Overview</div>
    </body></html>"""
    out = finalize_cinema_html(html)
    assert ".kpi-card" in out
    assert ".chart-card" in out
    assert "[data-nexu-target]" in out


def test_inject_cinema_shield_preserves_existing_scripts():
    html = """<!DOCTYPE html><html><head>
<script>/* nexu preview: block cross-origin fetch */</script>
</head><body><main id="hero">Site</main></body></html>"""
    out = inject_cinema_shield(html)
    assert "nexu preview: block cross-origin fetch" in out
    assert "const NEXU_PARAMS = new URLSearchParams" in out
    assert out.lower().count("<script") >= 2


def test_inject_cinema_shield_posts_compact_marked_fragment():
    out = inject_cinema_shield("<html><body><button id='btn-x'>X</button></body></html>")

    assert "function compactFragment" in out
    assert "fragment: compactFragment" in out
    assert "outerHTML" in out
