from __future__ import annotations

from pathlib import Path

from .models import write_yaml
from .paths import ensure_project_dirs


def init_project(root: Path) -> list[Path]:
    ensure_project_dirs(root)
    created: list[Path] = []

    nexu_yaml = root / "nexu.yaml"
    if not nexu_yaml.exists():
        write_yaml(
            nexu_yaml,
            {
                "version": "nexu.v1",
                "project": {
                    "name": root.name,
                    "source_of_truth": {
                        "intent": "intract.yaml",
                        "capsules": ".nexu/capsules",
                        "snapshots": ".nexu/snapshots",
                    },
                },
                "verification": {
                    "fail_on": ["forbidden_effect", "invalid_contract"],
                    "warn_on": ["missing_tests", "partial_output_match"],
                },
                "llm": {
                    "provider": "offline",
                    "model": "openrouter/deepseek/deepseek-v4-pro",
                    "base_url": "https://openrouter.ai/api/v1",
                    "api_key_env": "OPENROUTER_API_KEY",
                    "temperature": 0.1,
                    "allow_network_calls": False,
                },
                "orchestration": {
                    "default_steps": 10,
                    "llm_mode": "offline",
                    "require_verification_after_each_step": True,
                },
                "mcp": {
                    "enabled": True,
                    "transport": "stdio",
                    "allow_apply": False,
                },
                "review": {
                    "require_human_approval": True,
                    "evidence_required": True,
                    "fail_on": ["fail"],
                    "warn_on": ["partial", "warn"],
                },
                "preview": {"default_horizon": 10, "render": ["text_wireframe", "ui_blueprint"]},
            },
        )
        created.append(nexu_yaml)

    intract_yaml = root / "intract.yaml"
    if not intract_yaml.exists():
        write_yaml(
            intract_yaml,
            {
                "version": "intract.v1",
                "project": {"name": root.name, "intent": "orchestrate:project_capsules"},
                "contracts": [
                    {
                        "id": "project.capsules",
                        "scope": "project",
                        "intent": "orchestrate:project_capsules",
                        "priority": 2,
                        "domain": "architecture",
                        "input": ["project_state", "user_goal"],
                        "output": ["capsule", "evidence_map", "promotion_plan"],
                        "effect": ["read"],
                        "forbid": ["destructive_write", "secret_leak"],
                        "require": ["freeze.baseline", "verify.capsule", "promote.after_review"],
                        "validate": ["input_presence", "output_presence", "no_forbidden_effect"],
                    }
                ],
            },
        )
        created.append(intract_yaml)

    return created
