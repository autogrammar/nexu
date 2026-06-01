"""Persist Cinema LLM exchange traces for the player debug tab."""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from threading import Lock

_SECRET_PATTERNS = (
    re.compile(r"sk-or-v1-[a-zA-Z0-9_-]{8,}", re.I),
    re.compile(r"sk-[a-zA-Z0-9_-]{16,}", re.I),
    re.compile(r"Bearer\s+[a-zA-Z0-9._-]{8,}", re.I),
)


def redact_secrets(text: str, *, extra_values: tuple[str, ...] = ()) -> str:
    """Remove API keys and bearer tokens from trace markdown."""
    out = str(text or "")
    for val in extra_values:
        if val and len(val) >= 8:
            out = out.replace(val, "[REDACTED:secret]")
    for key in (
        os.environ.get("OPENROUTER_API_KEY", ""),
        os.environ.get("OPENAI_API_KEY", ""),
        os.environ.get("ANTHROPIC_API_KEY", ""),
    ):
        if key and len(key) >= 8:
            out = out.replace(key, "[REDACTED:api_key]")
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub("[REDACTED:api_key]", out)
    return out


def trace_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value or "trace")).strip("-")
    return slug[:80] or "trace"


def text_metrics(text: str) -> dict[str, int]:
    """Small dependency-free metrics for LLM trace sizing."""
    value = str(text or "")
    return {
        "chars": len(value),
        "bytes": len(value.encode("utf-8")),
        "tokens_est": max(1, (len(value) + 3) // 4) if value else 0,
    }


def read_trace_index(index_path: Path) -> list[dict]:
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def write_llm_trace(
    trace_dir: Path,
    index_path: Path,
    lock: Lock,
    *,
    label: str,
    prompt: str,
    output: str = "",
    error: str = "",
    model: str = "",
    duration_ms: int = 0,
    keep: int = 80,
    redact_values: tuple[str, ...] = (),
) -> str | None:
    try:
        trace_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now().isoformat(timespec="seconds")
        trace_id = f"{int(time.time() * 1000)}-{trace_slug(label)}"
        prompt_text = redact_secrets(prompt, extra_values=redact_values)
        output_text = redact_secrets(output, extra_values=redact_values)
        error_text = redact_secrets(error, extra_values=redact_values)
        prompt_metrics = text_metrics(prompt_text)
        output_metrics = text_metrics(output_text)
        total_metrics = {
            key: prompt_metrics[key] + output_metrics[key]
            for key in ("chars", "bytes", "tokens_est")
        }
        markdown = (
            f"# LLM Trace: {label}\n\n"
            f"- timestamp: `{now}`\n"
            f"- model: `{model or 'unknown'}`\n"
            f"- duration_ms: `{duration_ms}`\n"
            f"- prompt_chars: `{prompt_metrics['chars']}`\n"
            f"- prompt_bytes: `{prompt_metrics['bytes']}`\n"
            f"- prompt_tokens_est: `{prompt_metrics['tokens_est']}`\n"
            f"- output_chars: `{output_metrics['chars']}`\n"
            f"- output_bytes: `{output_metrics['bytes']}`\n"
            f"- output_tokens_est: `{output_metrics['tokens_est']}`\n"
            f"- total_chars: `{total_metrics['chars']}`\n"
            f"- total_bytes: `{total_metrics['bytes']}`\n"
            f"- total_tokens_est: `{total_metrics['tokens_est']}`\n"
            f"- status: `{'error' if error_text else 'ok'}`\n\n"
            "## Prompt sent to LLM\n\n"
            "```markdown\n"
            + prompt_text.replace("```", "```\\")
            + "\n```\n\n"
            "## Response received from LLM\n\n"
            "```html\n"
            + output_text.replace("```", "```\\")
            + "\n```\n"
        )
        if error_text:
            markdown += "\n## Error\n\n```text\n" + error_text + "\n```\n"
        path = trace_dir / f"{trace_id}.md"
        path.write_text(markdown, encoding="utf-8")
        with lock:
            index = read_trace_index(index_path)
            index.insert(
                0,
                {
                    "id": trace_id,
                    "label": label,
                    "timestamp": now,
                    "model": model or "unknown",
                    "duration_ms": duration_ms,
                    "prompt_chars": prompt_metrics["chars"],
                    "prompt_bytes": prompt_metrics["bytes"],
                    "prompt_tokens_est": prompt_metrics["tokens_est"],
                    "output_chars": output_metrics["chars"],
                    "output_bytes": output_metrics["bytes"],
                    "output_tokens_est": output_metrics["tokens_est"],
                    "total_chars": total_metrics["chars"],
                    "total_bytes": total_metrics["bytes"],
                    "total_tokens_est": total_metrics["tokens_est"],
                    "status": "error" if error_text else "ok",
                    "file": path.name,
                },
            )
            index_path.write_text(
                json.dumps(index[:keep], indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        return trace_id
    except Exception:
        return None


def list_llm_traces(trace_dir: Path) -> dict:
    trace_dir.mkdir(parents=True, exist_ok=True)
    index_path = trace_dir / "index.json"
    return {"traces": read_trace_index(index_path)}


def read_llm_trace(trace_dir: Path, trace_id: str) -> dict:
    safe = trace_slug(trace_id)
    path = trace_dir / f"{safe}.md"
    if not path.is_file():
        return {"error": "trace not found"}
    markdown = path.read_text(encoding="utf-8")
    return {
        "id": safe,
        "filename": path.name,
        "bytes": path.stat().st_size,
        "markdown": markdown,
        "markdown_metrics": text_metrics(markdown),
    }
