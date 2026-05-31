from nexu.cinema_scripts import finalize_cinema_html


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
