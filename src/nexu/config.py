from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import read_yaml


@dataclass
class LLMConfig:
    provider: str = "offline"
    model: str = "openrouter/deepseek/deepseek-v4-pro"
    base_url: str = "https://openrouter.ai/api/v1"
    api_key_env: str = "OPENROUTER_API_KEY"
    temperature: float = 0.1
    timeout: int = 60
    allow_network_calls: bool = False


@dataclass
class ReviewConfig:
    require_human_approval: bool = True
    fail_on: list[str] = field(default_factory=lambda: ["fail"])
    warn_on: list[str] = field(default_factory=lambda: ["partial", "warn"])
    evidence_required: bool = True


@dataclass
class nexuConfig:
    version: str = "nexu.v1"
    project_name: str = "project"
    llm: LLMConfig = field(default_factory=LLMConfig)
    review: ReviewConfig = field(default_factory=ReviewConfig)


def _as_list(value: Any, default: list[str]) -> list[str]:
    if value is None:
        return default
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def load_config(root: Path) -> nexuConfig:
    path = root / "nexu.yaml"
    if not path.exists():
        return nexuConfig(project_name=root.name)

    data = read_yaml(path)
    project = data.get("project", {}) or {}
    llm_data = data.get("llm", {}) or {}
    review_data = data.get("review", {}) or {}
    verification_data = data.get("verification", {}) or {}

    llm = LLMConfig(
        provider=str(llm_data.get("provider", "offline")),
        model=str(
            llm_data.get(
                "model",
                os.getenv("LLM_MODEL") or os.getenv("NEXU_MODEL") or os.getenv("nexu_MODEL") or "openrouter/deepseek/deepseek-v4-pro"
            )
        ),
        base_url=str(llm_data.get("base_url", "https://openrouter.ai/api/v1")),
        api_key_env=str(llm_data.get("api_key_env", "OPENROUTER_API_KEY")),
        temperature=float(llm_data.get("temperature", 0.1)),
        timeout=int(llm_data.get("timeout", 60)),
        allow_network_calls=bool(llm_data.get("allow_network_calls", False)),
    )
    review = ReviewConfig(
        require_human_approval=bool(review_data.get("require_human_approval", True)),
        fail_on=_as_list(review_data.get("fail_on"), _as_list(verification_data.get("fail_on"), ["fail"])),
        warn_on=_as_list(review_data.get("warn_on"), _as_list(verification_data.get("warn_on"), ["partial", "warn"])),
        evidence_required=bool(review_data.get("evidence_required", True)),
    )
    return nexuConfig(
        version=str(data.get("version", "nexu.v1")),
        project_name=str(project.get("name", root.name)),
        llm=llm,
        review=review,
    )
