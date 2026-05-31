from pathlib import Path

from nexu.cinema_llm import (
    call_cinema_html_llm,
    compact_llm_error,
    extract_html_document,
    has_terminal_artifacts,
)


def test_extract_html_document_from_fences() -> None:
    raw = "```html\n<!DOCTYPE html><html><body>ok</body></html>\n```"
    assert "ok" in extract_html_document(raw)


def test_extract_html_document_strips_rich_terminal_frame() -> None:
    raw = """╭────╮
│ <!DOCTYPE html>                                      │
│ <html><body>ok</body></html>                         │
╰────╯
"""
    html = extract_html_document(raw)
    assert html.startswith("<!DOCTYPE html>")
    assert "│" not in html
    assert "ok" in html


def test_has_terminal_artifacts_detects_box_drawing() -> None:
    assert has_terminal_artifacts("│ <!DOCTYPE html>")
    assert not has_terminal_artifacts("<!DOCTYPE html><html></html>")


def test_compact_llm_error_openrouter_payload() -> None:
    err = 'OpenrouterException - {"error":{"message":"Rate limited"}}'
    assert compact_llm_error(err) == "Rate limited"


def test_call_cinema_html_llm_blocks_when_network_disabled(tmp_path: Path) -> None:
    (tmp_path / "nexu.yaml").write_text(
        "version: nexu.v1\nllm:\n  allow_network_calls: false\n",
        encoding="utf-8",
    )
    html, err = call_cinema_html_llm("prompt", tmp_path)
    assert html is None
    assert err and "allow_network_calls" in err


def test_call_cinema_html_llm_requires_api_key(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "nexu.yaml").write_text(
        "version: nexu.v1\nllm:\n  allow_network_calls: true\n  api_key_env: TEST_CINEMA_KEY\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("TEST_CINEMA_KEY", raising=False)
    html, err = call_cinema_html_llm("prompt", tmp_path)
    assert html is None
    assert err == "TEST_CINEMA_KEY not set"


def test_call_cinema_html_llm_uses_litellm(monkeypatch, tmp_path: Path) -> None:
    (tmp_path / "nexu.yaml").write_text(
        "version: nexu.v1\nllm:\n  allow_network_calls: true\n  provider: openrouter\n"
        "  model: test/model\n  api_key_env: TEST_CINEMA_KEY\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TEST_CINEMA_KEY", "secret")

    captured: dict = {}

    def fake_completion(**kwargs):
        captured.update(kwargs)
        return {
            "choices": [
                {
                    "message": {
                        "content": "<!DOCTYPE html><html><body>done</body></html>",
                    }
                }
            ]
        }

    monkeypatch.setattr("nexu.cinema_llm._litellm_completion", lambda: fake_completion)
    html, err = call_cinema_html_llm("evolve this", tmp_path)
    assert err is None
    assert html and "done" in html
    assert captured["model"] == "test/model"
    assert captured["api_key"] == "secret"
    assert captured["api_base"] == "https://openrouter.ai/api/v1"
