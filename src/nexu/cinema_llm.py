"""In-process LiteLLM calls for Cinema HTML generation (avoids llx CLI overhead)."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from .config import load_config, load_env_files

_CONFIG_CACHE: tuple[float, object] | None = None
_COMPLETION = None


def _cached_config(root: Path):
    global _CONFIG_CACHE
    yaml_path = root / "nexu.yaml"
    mtime = yaml_path.stat().st_mtime if yaml_path.is_file() else 0.0
    if _CONFIG_CACHE is not None and _CONFIG_CACHE[0] == mtime:
        return _CONFIG_CACHE[1]
    load_env_files(root)
    config = load_config(root)
    _CONFIG_CACHE = (mtime, config)
    return config


def _litellm_completion():
    global _COMPLETION
    if _COMPLETION is None:
        from litellm import completion as _COMPLETION  # type: ignore
    return _COMPLETION


def _strip_markdown_fences(text: str) -> str:
    raw = text.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return raw


_RICH_BORDER_CHARS = ("│", "║", "╭", "╮", "╰", "╯", "─", "═")


def _strip_rich_console_artifacts(text: str) -> str:
    """Remove Rich/terminal box borders that some CLIs add around LLM output."""
    lines = str(text or "").splitlines()
    cleaned: list[str] = []
    for line in lines:
        s = line.rstrip()
        stripped = s.strip()
        if stripped and set(stripped) <= set("╭╮╰╯─═ "):
            continue
        if stripped.startswith(("│", "║")):
            stripped = stripped[1:].strip()
            if stripped.endswith(("│", "║")):
                stripped = stripped[:-1].rstrip()
            cleaned.append(stripped)
        else:
            cleaned.append(s)
    return "\n".join(cleaned).strip()


def has_terminal_artifacts(text: str) -> bool:
    """Detect box-drawing output that should never be persisted as app HTML."""
    sample = "\n".join(str(text or "").splitlines()[:24])
    return any(ch in sample for ch in _RICH_BORDER_CHARS)


def extract_html_document(text: str) -> str:
    cleaned = _strip_rich_console_artifacts(_strip_markdown_fences(text))
    match = re.search(r"<!DOCTYPE\s+html[\s\S]*?</html>", cleaned, flags=re.I)
    if match:
        return match.group(0).strip()
    match = re.search(r"<html[\s\S]*?</html>", cleaned, flags=re.I)
    if match:
        return "<!DOCTYPE html>\n" + match.group(0).strip()
    return cleaned


def _extract_content(response: Any) -> str:
    try:
        content = response["choices"][0]["message"]["content"]
        if content is not None:
            return str(content)
    except Exception:
        pass
    choices = getattr(response, "choices", None)
    if not choices:
        raise RuntimeError("LLM response did not contain choices")
    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", None) if message is not None else None
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    if content is None:
        raise RuntimeError("LLM response did not contain message content")
    return str(content)


def compact_llm_error(err_text: str) -> str:
    if "OpenrouterException - " in err_text:
        payload = err_text.split("OpenrouterException - ", 1)[1].strip()
        try:
            import json

            data = json.loads(payload)
            msg = data.get("error", {}).get("message")
            if isinstance(msg, str) and msg.strip():
                return msg.strip()
        except Exception:
            pass
    compact = " ".join(str(err_text).split())
    return compact[:260]


def call_cinema_html_llm(
    prompt: str,
    root: Path,
    *,
    model: str | None = None,
    max_tokens: int = 4096,
) -> tuple[str | None, str | None]:
    """
    Generate one complete HTML document via LiteLLM/OpenRouter.

    Returns (html, error). Uses nexu.yaml llm settings; no llx subprocess.
    """
    try:
        config = _cached_config(root)
        llm = config.llm
    except Exception as exc:
        return None, compact_llm_error(str(exc))

    if not llm.allow_network_calls:
        return None, "llm.allow_network_calls disabled in nexu.yaml"

    api_key = os.environ.get(llm.api_key_env, "")
    if not api_key:
        return None, f"{llm.api_key_env} not set"

    resolved_model = model or llm.model
    system = (
        "You are a UI evolution engine. Return only one complete HTML "
        "document. No markdown fences, no explanation."
    )

    try:
        completion = _litellm_completion()
    except Exception:
        return None, "Install litellm (uv sync) for Cinema live iteration"

    kwargs: dict[str, Any] = {
        "model": resolved_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": llm.temperature,
        "max_tokens": max_tokens,
        "timeout": llm.timeout,
        "api_key": api_key,
    }
    if llm.provider == "openrouter":
        kwargs["api_base"] = llm.base_url

    try:
        response = completion(**kwargs)
        raw = extract_html_document(_extract_content(response))
        if raw and "<!DOCTYPE" in raw.upper()[:80]:
            if has_terminal_artifacts(raw):
                return None, "LLM output contained terminal box-drawing artifacts, not clean HTML"
            return raw, None
        return None, "LLM did not return a complete HTML document"
    except Exception as exc:
        return None, compact_llm_error(str(exc))
