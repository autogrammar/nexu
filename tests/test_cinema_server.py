from dataclasses import dataclass
from pathlib import Path

from nexu.cinema import _cinema_template_text, _render_cinema_template, write_cinema_nexu_hooks
from nexu.cinema_server import _render_server_script, start_cinema_player_server
from nexu.config import CinemaConfig, LLMConfig

CINEMA_LLM_MODEL = "openrouter/deepseek/deepseek-v4-pro"


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
        CinemaConfig(),
        "/usr/bin/python3",
    )

    assert script.startswith("#!/usr/bin/python3")
    assert "WORKSPACE_PATH = '/tmp/workspace'" in script
    assert "CAPSULE_NAME = 'demo'" in script
    assert "_load_cinema_ui_profile" in script
    assert "_llm_prompt_rules" in script
    assert "Intract LLM communication contract" in script
    assert "build_llm_contract_block" in script
    assert "build_llm_option_variants" in script
    assert "KPI overview workflow" not in script
    assert "Build chemical-calculator UIs" not in script
    assert "call_cinema_html_llm" in script
    assert "Markpact context pack" in script
    assert "_mp_payload = nexu_hooks.export_markpact_readme" in script
    assert "has_terminal_artifacts" in script
    assert "_compact_html_for_llm" in script
    assert "_compact_markpact_for_llm" in script
    assert "omitted from Markpact context" in script
    assert "DEFAULT_MARKPACT_CONTEXT_MODE" in script
    assert "DEFAULT_MARKPACT_CONTEXT_CHARS" in script
    assert "DEFAULT_HTML_CONTEXT_CHARS" in script
    assert "DEFAULT_LLM_TRACE_KEEP" in script
    assert "OPTION_GENERATION_MODE" in script
    assert "_call_llm_batch_options" in script
    assert "_generate_parallel_options" in script
    assert 'OPTION_GENERATION_MODE in {"batch", "single", "1"}' in script
    assert "parse_batch_alt_options" in script
    assert "from nexu.cinema_traces import write_llm_trace" in script
    assert "ThreadPoolExecutor" in script
    assert '"llx"' not in script
    assert "proposed_options_offline" not in script
    assert "SYS_EXE = '/usr/bin/python3'" in script
    assert "ALLOW_NETWORK_CALLS = False" in script
    assert "def _llm_network_allowed()" in script
    assert "def _llm_status_payload()" in script
    assert '"/llm/status"' in script
    assert '"/llm/traces"' in script
    assert '"/llm/trace"' in script
    assert "LLM_TRACE_DIR" in script
    assert '"cinema": {' in script
    assert "_cached_config(ROOT_PATH).llm.allow_network_calls" in script
    assert "API_KEY_ENV = 'OPENROUTER_API_KEY'" in script
    assert "DEFAULT_MODEL = 'test-model'" in script


def test_render_server_script_embeds_openrouter_model() -> None:
    llm = LLMConfig(
        provider="openrouter",
        model=CINEMA_LLM_MODEL,
        allow_network_calls=True,
    )
    script = _render_server_script(
        Path("/tmp/workspace"),
        "demo",
        llm,
        CinemaConfig(),
        "/usr/bin/python3",
    )

    assert f"DEFAULT_MODEL = '{CINEMA_LLM_MODEL}'" in script
    assert 'os.environ.get("LLM_MODEL")' in script


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
    assert (
        'src="stage0.html?role=workspace&amp;active=true&amp;mark=1&amp;'
        'calc=0&amp;review=0&amp;stage=0"'
    ) in html
    assert 'function calcEnabledForProject()' in html
    assert 'function flushPendingLogEvents()' in html
    assert 'src="alt_a.html?role=option&amp;pane=a&amp;mark=0&amp;calc=0"' in html
    assert 'id="goal-input"' in html
    assert "goalContractPayload" in html
    assert "focus_scope" in html
    assert "offline templates" not in html
    assert 'id="llm-status-badge"' in html
    assert "refreshLlmStatus" in html
    assert 'id="tab-llm"' in html
    assert 'id="llm-shell"' in html
    assert "loadLlmTraces" in html
    assert "renderTraceMarkdown" in html
    assert "user_goal" in html
    assert "active_example_project" in html
    assert "goal_bootstrap" in html
    assert "hasIterationContext" in html
    assert "ledgerGoalFromPolicy" in html
    assert "syncGoalFromLedger" in html
    assert "server-offline-banner" in html
    assert "updateServerOfflineBanner" in html


def test_start_cinema_player_server_returns_url_without_opening(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("nexu.cinema_server.start_persistent_http_server", lambda *_: 8099)

    url = start_cinema_player_server(tmp_path, Path("/tmp/workspace"), "demo", open_browser=False)

    assert url == "http://127.0.0.1:8099/cinema_player.html"
