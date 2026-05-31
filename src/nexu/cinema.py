from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path
from string import Template
from typing import Any

from .cinema_baseline_contracts import (
    ensure_capsule_intract_yaml,
    is_calculator_capsule,
    merge_calculator_baselines,
)
from .cinema_scripts import (
    CALCULATOR_RUNTIME_SCRIPT,
    SHIELD_SCRIPT,
    write_cinema_inject_files,
)
from .cinema_server import start_cinema_player_server
from .intract import IntentContract, format_intract_v1_line, read_manifest_contracts
from .models import read_yaml
from .paths import capsule_dir, nexu_dir


def _cinema_template_text(name: str) -> str:
    return files("nexu").joinpath("templates", "cinema", name).read_text(encoding="utf-8")


def _render_cinema_template(name: str, **values: str) -> str:
    template = Template(_cinema_template_text(name))
    return template.substitute({key.upper(): value for key, value in values.items()})


def write_cinema_nexu_hooks(cinema_dir: Path, root: Path, name: str) -> None:
    """Runtime helpers for generated server.py (manifest merge, verify)."""
    hooks = _cinema_template_text("nexu_hooks.py.tmpl")
    hooks = hooks.replace("__ROOT_PATH__", repr(str(root.resolve())))
    hooks = hooks.replace("__CAPSULE_NAME__", repr(name))
    (cinema_dir / "nexu_hooks.py").write_text(hooks, encoding="utf-8")


def _contract_to_public_dict(contract: IntentContract) -> dict[str, Any]:
    return {
        "id": contract.contract_id,
        "scope": contract.scope,
        "intent": contract.intent,
        "priority": contract.priority,
        "domain": contract.domain,
        "input": contract.input,
        "output": contract.output,
        "effect": contract.effect,
        "forbid": contract.forbid,
        "require": contract.require,
        "validate": contract.validate,
        "meaning": contract.meaning,
        "source": contract.source,
        "line": format_intract_v1_line(contract),
    }


def build_intract_policy_snapshot(root: Path, name: str) -> dict[str, Any]:
    base = capsule_dir(root, name)
    project_intract = root / "intract.yaml"
    capsule_intract = base / "intract.yaml"
    nexu_yaml = root / "nexu.yaml"
    nexu_data = read_yaml(nexu_yaml) if nexu_yaml.exists() else {}
    project_meta = nexu_data.get("project", {}) or {}

    project_contracts = (
        [_contract_to_public_dict(c) for c in read_manifest_contracts(project_intract)]
        if project_intract.exists()
        else []
    )
    ensure_capsule_intract_yaml(root, name)
    capsule_contracts = (
        [_contract_to_public_dict(c) for c in read_manifest_contracts(capsule_intract)]
        if capsule_intract.exists()
        else []
    )
    capsule_contracts = merge_calculator_baselines(capsule_contracts, root, name)

    return {
        "version": "intract.policy.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": {
            "root": str(root),
            "name": str(project_meta.get("name", root.name)),
            "has_nexu_yaml": nexu_yaml.exists(),
            "has_intract_yaml": project_intract.exists(),
            "has_nexu_dir": nexu_dir(root).exists(),
            "intract_path": str(project_intract) if project_intract.exists() else None,
            "nexu_path": str(nexu_yaml) if nexu_yaml.exists() else None,
        },
        "capsule": {
            "name": name,
            "exists": base.exists(),
            "path": str(base) if base.exists() else None,
            "has_intract_yaml": capsule_intract.exists(),
            "intract_path": str(capsule_intract) if capsule_intract.exists() else None,
            "is_calculator": is_calculator_capsule(root, name),
        },
        "baseline_contracts": {
            "project": project_contracts,
            "capsule": capsule_contracts,
        },
    }


def write_intract_policy_files(cinema_dir: Path, root: Path, name: str) -> None:
    snapshot = build_intract_policy_snapshot(root, name)
    (cinema_dir / "intract_policy.json").write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    ledger_path = cinema_dir / "intract_policy_ledger.json"
    if not ledger_path.exists():
        ledger_path.write_text("[]", encoding="utf-8")


def generate_cinema_player(root: Path, name: str) -> Path:
    """
    Generates the interactive Nexu editor UI for a capsule.
    Employs the gorgeous vertical stacked options layout:
    - Left part: Large Active Workspace (Window 1)
    - Middle part: Vertically stacked Options A, B, C (Windows 2-4) that dynamically expand on hover
    - Right part: Controls, logs, and prompt boxes
    """
    base = capsule_dir(root, name)
    cinema_dir = base / "cinema"
    cinema_dir.mkdir(parents=True, exist_ok=True)
    write_intract_policy_files(cinema_dir, root, name)
    write_cinema_nexu_hooks(cinema_dir, root, name)
    write_cinema_inject_files(cinema_dir)
    from .cinema_history import ensure_initial_checkpoint

    ensure_initial_checkpoint(cinema_dir)

    injected_scripts = SHIELD_SCRIPT + CALCULATOR_RUNTIME_SCRIPT

    stage0_html = _render_cinema_template(
        "stage0.html.tmpl",
        injected_scripts=injected_scripts,
    )
    alt_a_html = _render_cinema_template(
        "alt_a.html.tmpl",
        injected_scripts=injected_scripts,
    )
    alt_b_html = _render_cinema_template(
        "alt_b.html.tmpl",
        injected_scripts=injected_scripts,
    )
    alt_c_html = _render_cinema_template(
        "alt_c.html.tmpl",
        injected_scripts=injected_scripts,
    )

    (cinema_dir / "stage0.html").write_text(stage0_html, encoding="utf-8")
    (cinema_dir / "alt_a.html").write_text(alt_a_html, encoding="utf-8")
    (cinema_dir / "alt_b.html").write_text(alt_b_html, encoding="utf-8")
    (cinema_dir / "alt_c.html").write_text(alt_c_html, encoding="utf-8")
    (cinema_dir / "stage1.html").write_text(alt_b_html, encoding="utf-8")
    (cinema_dir / "stage2.html").write_text(alt_c_html, encoding="utf-8")

    if is_calculator_capsule(root, name):
        from .cinema_offline_options import write_goal_options_offline

        write_goal_options_offline(cinema_dir, keep_els=[], delete_els=[], hints=[])

    player_path = cinema_dir / "cinema_player.html"
    player_html = _cinema_template_text("cinema_player.html.tmpl")
    player_path.write_text(player_html, encoding="utf-8")

    _start_cinema_server(cinema_dir, root, name)

    return player_path


def _start_cinema_server(cinema_dir: Path, root: Path, name: str) -> None:
    try:
        start_cinema_player_server(
            cinema_dir,
            root,
            name,
            open_browser=not os.environ.get("NEXU_CINEMA_NO_OPEN"),
        )
    except Exception as exc:
        print(f"⚠️ Cinema HTTP server could not start: {exc}")
