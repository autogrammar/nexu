"""Default @intract.v1 baseline contracts for Cinema calculator capsules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .intract import IntentContract, format_intract_v1_line
from .paths import capsule_dir


def _contract(
    contract_id: str,
    intent: str,
    meaning: str,
    *,
    scope: str = "capsule",
    priority: int = 2,
    domain: str = "ui",
    input_fields: list[str] | None = None,
    output_fields: list[str] | None = None,
) -> dict[str, Any]:
    c = IntentContract(
        raw="",
        contract_id=contract_id,
        scope=scope,
        intent=intent,
        priority=priority,
        domain=domain,
        input=input_fields or [],
        output=output_fields or [],
        effect=["read"],
        forbid=["destructive_write", "secret_leak"],
        require=[],
        validate=["input_presence"],
        meaning=meaning,
    )
    return {
        "id": c.contract_id,
        "scope": c.scope,
        "intent": c.intent,
        "priority": c.priority,
        "domain": c.domain,
        "input": c.input,
        "output": c.output,
        "effect": c.effect,
        "forbid": c.forbid,
        "require": c.require,
        "validate": c.validate,
        "meaning": c.meaning,
        "source": "nexu.cinema.baseline",
        "line": format_intract_v1_line(c),
    }


def calculator_baseline_contracts() -> list[dict[str, Any]]:
    """What the calculator is and how display/keypad/variants are laid out by default."""
    return [
        _contract(
            "calc.app.kind",
            "define:scientific_calculator",
            "Capsule is a touch scientific calculator: calc-body card, display on top, "
            "keypad grid below.",
            output_fields=["html_surface", "operation_list"],
        ),
        _contract(
            "calc.ui.display",
            "layout:display",
            "Display (#screen) sits at the top inside .calc-body, right-aligned, "
            "min-height ~2.2em, accent green/blue.",
            input_fields=["calculator_state"],
            output_fields=["screen_text"],
        ),
        _contract(
            "calc.ui.keypad.grid",
            "layout:keypad",
            "Default keypad: 4 columns, grid-auto-rows 1fr, gap 6-8px; "
            "operators orange (#e67e22), equals green (#2ecc71).",
            output_fields=["button_grid"],
        ),
        _contract(
            "calc.ui.keypad.sci_row",
            "layout:sci_functions",
            "Scientific row (sin,cos,tan,log,ln) directly under the display, "
            "before digits; btn-sci styling.",
            output_fields=["sci_buttons"],
        ),
        _contract(
            "calc.options.variant_a",
            "layout:option_minimal",
            "Option A: compact 3-column grid, x2/sqrt/C utilities, partial numpad "
            "(no 0/./= row), aspect-ratio 3/4.",
        ),
        _contract(
            "calc.options.variant_b",
            "layout:option_standard",
            "Option B: 4-column square buttons, full trig row + C/(/) + complete numpad.",
        ),
        _contract(
            "calc.options.variant_c",
            "layout:option_expanded",
            "Option C: 5-column circular buttons, excess row (EXP,Mod,deg,rad,π), dark background.",
        ),
    ]


def is_calculator_capsule(root: Path, name: str) -> bool:
    base = capsule_dir(root, name)
    if (base / "src" / "calculator.py").exists():
        return True
    if "calc" in name.lower():
        return True
    stage0 = base / "cinema" / "stage0.html"
    if stage0.is_file():
        text = stage0.read_text(encoding="utf-8")
        return "calc-body" in text or "btn-eq" in text
    return False


def merge_calculator_baselines(
    capsule_contracts: list[dict[str, Any]],
    root: Path,
    name: str,
) -> list[dict[str, Any]]:
    if not is_calculator_capsule(root, name):
        return capsule_contracts
    existing = {c.get("id") for c in capsule_contracts}
    merged = list(capsule_contracts)
    for contract in calculator_baseline_contracts():
        if contract["id"] not in existing:
            merged.append(contract)
    return merged


def ensure_capsule_intract_yaml(root: Path, name: str) -> Path | None:
    """Create capsule intract.yaml with calculator baseline contracts when missing."""
    if not is_calculator_capsule(root, name):
        return None
    base = capsule_dir(root, name)
    path = base / "intract.yaml"
    if path.exists():
        return path
    lines = [
        "version: intract.v1",
        "capsule:",
        f"  name: {name}",
        "  intent: render:calculator",
        "contracts:",
    ]
    for contract in calculator_baseline_contracts():
        lines.append(f"  - id: {contract['id']}")
        lines.append(f"    scope: {contract['scope']}")
        lines.append(f"    intent: {contract['intent']}")
        lines.append(f"    priority: {contract['priority']}")
        lines.append(f"    domain: {contract['domain']}")
        if contract.get("meaning"):
            lines.append(f"    meaning: \"{contract['meaning']}\"")
        if contract.get("input"):
            lines.append("    input:")
            for item in contract["input"]:
                lines.append(f"      - {item}")
        if contract.get("output"):
            lines.append("    output:")
            for item in contract["output"]:
                lines.append(f"      - {item}")
        lines.append("    effect:")
        lines.append("      - read")
        lines.append("    forbid:")
        lines.append("      - destructive_write")
        lines.append("      - secret_leak")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
