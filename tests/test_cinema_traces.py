from pathlib import Path
from threading import Lock

from nexu.cinema_traces import (
    list_llm_traces,
    read_llm_trace,
    redact_secrets,
    write_llm_trace,
)
from nexu.config import load_config

CINEMA_LLM_MODEL = "openrouter/deepseek/deepseek-v4-pro"


def test_load_config_llm_model_default(tmp_path: Path) -> None:
    config = load_config(tmp_path)
    assert config.llm.model == CINEMA_LLM_MODEL


def test_load_config_llm_model_from_yaml(tmp_path: Path) -> None:
    (tmp_path / "nexu.yaml").write_text(
        "version: nexu.v1\nllm:\n  provider: openrouter\n  model: "
        f"{CINEMA_LLM_MODEL}\n",
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    assert config.llm.provider == "openrouter"
    assert config.llm.model == CINEMA_LLM_MODEL


def test_llm_model_env_overrides_yaml(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "nexu.yaml").write_text(
        "version: nexu.v1\nllm:\n  model: openrouter/other/model\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("LLM_MODEL", CINEMA_LLM_MODEL)
    config = load_config(tmp_path)
    assert config.llm.model == CINEMA_LLM_MODEL


def test_redact_secrets_masks_api_keys() -> None:
    secret = "sk-or-v1-abcdefghijklmnopqrstuvwxyz"
    text = f"Authorization: Bearer {secret}\nkey={secret}"
    redacted = redact_secrets(text, extra_values=(secret,))
    assert secret not in redacted
    assert "[REDACTED" in redacted


def test_write_and_read_llm_trace(tmp_path: Path) -> None:
    trace_dir = tmp_path / "llm_traces"
    index_path = trace_dir / "index.json"
    lock = Lock()
    trace_id = write_llm_trace(
        trace_dir,
        index_path,
        lock,
        label="Option A (functions: conservative)",
        prompt="## Prompt\nhello",
        output="<!DOCTYPE html><html></html>",
        model="test/model",
        duration_ms=1234,
        keep=5,
        redact_values=("super-secret-key-value",),
    )
    assert trace_id
    listed = list_llm_traces(trace_dir)
    assert len(listed["traces"]) == 1
    assert listed["traces"][0]["label"].startswith("Option A")
    payload = read_llm_trace(trace_dir, trace_id or "")
    assert "## Prompt sent to LLM" in payload["markdown"]
    assert "hello" in payload["markdown"]
    assert "super-secret-key-value" not in payload["markdown"]


def test_load_config_reads_cinema_section(tmp_path: Path) -> None:
    (tmp_path / "nexu.yaml").write_text(
        """
version: nexu.v1
cinema:
  markpact_context_chars: 2500
  markpact_context_mode: off
  html_context_chars: 6000
  max_tokens: 8192
  option_generation_mode: parallel
  llm_trace_keep: 12
""".strip(),
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    assert config.cinema.markpact_context_chars == 2500
    assert config.cinema.markpact_context_mode == "off"
    assert config.cinema.html_context_chars == 6000
    assert config.cinema.max_tokens == 8192
    assert config.cinema.option_generation_mode == "parallel"
    assert config.cinema.llm_trace_keep == 12
