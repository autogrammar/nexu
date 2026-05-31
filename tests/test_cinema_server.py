from dataclasses import dataclass
from pathlib import Path

from nexu.cinema import _cinema_template_text, _render_cinema_template, write_cinema_nexu_hooks
from nexu.cinema_server import _render_server_script, start_cinema_player_server


@dataclass
class _LLMConfig:
    allow_network_calls: bool = False
    api_key_env: str = "OPENROUTER_API_KEY"
    model: str = "test-model"


def test_render_server_script_embeds_runtime_context() -> None:
    script = _render_server_script(
        Path("/tmp/workspace"),
        "demo",
        _LLMConfig(),
        "/usr/bin/python3",
    )

    assert script.startswith("#!/usr/bin/python3")
    assert "WORKSPACE_PATH = '/tmp/workspace'" in script
    assert "CAPSULE_NAME = 'demo'" in script
    assert "SYS_EXE = '/usr/bin/python3'" in script
    assert "ALLOW_NETWORK_CALLS = False" in script
    assert "API_KEY_ENV = 'OPENROUTER_API_KEY'" in script
    assert "DEFAULT_MODEL = 'test-model'" in script


def test_write_cinema_nexu_hooks_uses_template(tmp_path: Path) -> None:
    write_cinema_nexu_hooks(tmp_path, Path("/tmp/workspace"), "demo")

    hooks = (tmp_path / "nexu_hooks.py").read_text(encoding="utf-8")

    assert "ROOT = Path('/tmp/workspace')" in hooks
    assert "CAPSULE = 'demo'" in hooks
    assert "__ROOT_PATH__" not in hooks
    assert "__CAPSULE_NAME__" not in hooks


def test_render_stage_template_injects_runtime_scripts() -> None:
    html = _render_cinema_template("stage0.html.tmpl", injected_scripts="<script>ok()</script>")

    assert "<title>Simple Calculator</title>" in html
    assert "<script>ok()</script>" in html
    assert "$INJECTED_SCRIPTS" not in html


def test_cinema_player_template_is_externalized() -> None:
    html = _cinema_template_text("cinema_player.html.tmpl")

    assert "<title>Nexu" in html
    assert 'src="stage0.html?active=true"' in html
    assert 'src="alt_a.html"' in html


def test_start_cinema_player_server_returns_url_without_opening(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("nexu.cinema_server.start_persistent_http_server", lambda *_: 8099)

    url = start_cinema_player_server(tmp_path, Path("/tmp/workspace"), "demo", open_browser=False)

    assert url == "http://127.0.0.1:8099/cinema_player.html"
