"""Map Cinema project goals to Intract extension contracts (baseline stays frozen)."""

from __future__ import annotations

import re
from typing import Any

from .cinema_baseline_contracts import _contract
from .intract import IntentContract, format_intract_v1_line


def _hints_text(hints: list[str]) -> str:
    return " ".join(str(h).strip() for h in hints if str(h).strip()).lower()


def is_chemical_goal(hints: list[str]) -> bool:
    text = _hints_text(hints)
    return any(
        token in text
        for token in (
            "chem",
            "chemicz",
            "molar",
            "element",
            "formula",
            "periodic",
            "scientific",
            "naukow",
            "molow",
            "wzór",
            "wzor",
        )
    )


def _slug(text: str, *, max_len: int = 32) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return (slug[:max_len] if slug else "target").strip("_")


def _goal_contract_dict(
    contract_id: str,
    intent: str,
    meaning: str,
    *,
    capsule_name: str,
    stage: int,
    require: list[str] | None = None,
    based_on: str = "calc.app.kind",
) -> dict[str, Any]:
    req = list(require or ["freeze.baseline"])
    if based_on and based_on not in req:
        req.append(based_on)
    row = _contract(
        contract_id,
        intent,
        meaning,
        scope="capsule",
        priority=1,
        domain="ui",
        input_fields=["user_goal", "baseline_model"],
        output_fields=["target_traits", "evidence_map"],
    )
    row["require"] = req
    row["validate"] = ["input_presence", "no_forbidden_effect"]
    row["kind"] = "goal_extension"
    row["based_on"] = based_on
    line_model = IntentContract(
        raw="",
        contract_id=contract_id,
        scope=str(row["scope"]),
        intent=intent,
        priority=int(row["priority"]),
        domain=str(row["domain"]),
        input=list(row["input"]),
        output=list(row["output"]),
        effect=list(row.get("effect") or ["read"]),
        forbid=list(row.get("forbid") or []),
        require=req,
        validate=list(row["validate"]),
        meaning=meaning,
        source="nexu.cinema.goal",
    )
    row["line"] = format_intract_v1_line(line_model)
    row["delta_text"] = (
        f"Δ goal extension for {capsule_name} S{stage} based_on={based_on} "
        f"(require freeze.baseline — no regression)"
    )
    return row


def propose_goal_extension_contracts(
    goal: str,
    *,
    capsule_name: str,
    stage: int = 0,
    focus_scope: str = "",
    focus_scope_label: str = "",
    current_state: str = "",
    expected_version: str = "",
    project_context: str = "",
    project_kind: str = "",
) -> list[dict[str, Any]]:
    """
    Turn a natural-language project goal into Intract contracts that *extend*
    the frozen baseline model (calc.app.kind, layout contracts), not replace it.
    """
    text = (goal or "").strip()
    if not text:
        return []

    scope = _slug(focus_scope or focus_scope_label or "focus", max_len=24)
    scope_display = (
        focus_scope_label or (f"#{focus_scope}" if focus_scope else "#functions")
    ).strip()
    current = (current_state or "").strip()
    expected = (expected_version or "").strip()
    context = (project_context or "").strip()
    details = []
    if scope_display:
        details.append(f"focus scope {scope_display}")
    if context:
        details.append(f"project {context}")
    if current:
        details.append(f"current slice: {current}")
    if expected:
        details.append(f"expected/actions: {expected}")
    detail_text = "; ".join(details)
    slug = _slug(expected or text)
    kind = (project_kind or "").strip().lower()
    template_base = f"cinema.{capsule_name}.S{stage}.ui.template"
    if kind in ("imported", "web") or kind in {
        "dashboard",
        "monitor",
        "ecosystem",
        "api",
        "mcp",
        "frontend",
        "slice",
    }:
        baseline_anchor = template_base
    elif kind == "calculator" or not kind:
        baseline_anchor = "calc.app.kind"
    else:
        baseline_anchor = template_base
    proposals: list[dict[str, Any]] = [
        _goal_contract_dict(
            f"goal.{capsule_name}.S{stage}.target.{slug}",
            "define:target_solution",
            f"Project goal (user): {text}. Evolve UI toward this target without "
            "removing baseline structure unless explicitly marked DELETE."
            + (f" Context: {detail_text}." if detail_text else ""),
            capsule_name=capsule_name,
            stage=stage,
            require=["freeze.baseline", "verify.capsule"],
            based_on=baseline_anchor,
        ),
    ]

    if focus_scope or focus_scope_label:
        proposals.append(
            _goal_contract_dict(
                f"goal.{capsule_name}.S{stage}.scope.{scope}",
                f"focus:{scope}",
                f"Constrain the next Cinema iteration to {scope_display}: compare the "
                "current slice with the expected version/actions and keep unrelated "
                "project behavior stable.",
                capsule_name=capsule_name,
                stage=stage,
                require=["freeze.baseline"],
                based_on=f"cinema.{capsule_name}.S{stage}.ui.template",
            ),
        )

    if is_chemical_goal([text]):
        proposals.append(
            _goal_contract_dict(
                f"goal.{capsule_name}.S{stage}.trait.chemical",
                "evolve:chemical_calculator",
                "Extend toward chemical/scientific calculator: element keys, formulas, "
                "molar mass — preserve KEEP trig/sci controls from baseline and policy.",
                capsule_name=capsule_name,
                stage=stage,
                based_on="calc.ui.keypad.sci_row",
            ),
        )

    if kind == "calculator" and any(
        w in text.lower() for w in ("minimal", "prosty", "compact", "mniej")
    ):
        proposals.append(
            _goal_contract_dict(
                f"goal.{capsule_name}.S{stage}.trait.minimal",
                "evolve:minimal_ui",
                "Prefer fewer controls and cleaner layout (Option A direction) while "
                "honoring baseline display + KEEP list.",
                capsule_name=capsule_name,
                stage=stage,
                based_on="calc.options.variant_a",
            ),
        )

    if kind == "calculator" and any(
        w in text.lower() for w in ("expand", "rich", "więcej", "rozbudow")
    ):
        proposals.append(
            _goal_contract_dict(
                f"goal.{capsule_name}.S{stage}.trait.expanded",
                "evolve:expanded_ui",
                "Allow richer feature set (Option C direction) without breaking "
                "baseline grid classes and KEEP elements.",
                capsule_name=capsule_name,
                stage=stage,
                based_on="calc.options.variant_c",
            ),
        )

    lower = text.lower()
    if any(
        w in lower
        for w in (
            "api",
            "rest",
            "route",
            "routes",
            "endpoint",
            "openapi",
            "contract",
            "backend",
            "service",
            "grpc",
        )
    ):
        proposals.append(
            _goal_contract_dict(
                f"goal.{capsule_name}.S{stage}.trait.api",
                "evolve:api_surface",
                "Evolve API/backend service UI: route surface, health/metrics, "
                "contract docs — use project stage progression for Options A–C.",
                capsule_name=capsule_name,
                stage=stage,
                based_on=template_base,
            ),
        )

    if any(
        w in lower
        for w in (
            "dashboard",
            "analytics",
            "analityk",
            "kpi",
            "wykres",
            "chart",
            "panel",
            "metric",
            "funnel",
            "cohort",
            "experiment",
            "flag",
            "workspace",
        )
    ):
        proposals.append(
            _goal_contract_dict(
                f"goal.{capsule_name}.S{stage}.trait.dashboard",
                "evolve:analytics_dashboard",
                "Evolve dashboard/analytics UI: KPI cards, charts, filters — "
                "use project stage progression for Options A–C.",
                capsule_name=capsule_name,
                stage=stage,
                based_on=f"cinema.{capsule_name}.S{stage}.ui.template",
            ),
        )

    if any(
        w in lower
        for w in (
            "engineer",
            "engineers",
            "engineering",
            "inżynier",
            "inzynier",
            "space",
            "agency",
            "nasa",
            "aerospace",
        )
    ):
        proposals.append(
            _goal_contract_dict(
                f"goal.{capsule_name}.S{stage}.trait.engineering",
                "evolve:engineering_ui",
                "Target engineering/space-agency style: technical readouts, "
                "precision metrics, mission-control aesthetic in labels and layout.",
                capsule_name=capsule_name,
                stage=stage,
                based_on="calc.ui.display" if kind == "calculator" else template_base,
            ),
        )

    return proposals


def goal_traits_from_contract_lines(lines: list[str] | None) -> dict[str, bool]:
    """Parse Intract goal extension intents from ledger lines (offline + LLM hints)."""
    blob = " ".join(lines or []).lower()
    return {
        "chemical": "evolve:chemical_calculator" in blob,
        "minimal": "evolve:minimal_ui" in blob,
        "expanded": "evolve:expanded_ui" in blob,
        "dashboard": "evolve:analytics_dashboard" in blob,
        "api": "evolve:api_surface" in blob,
        "engineering": "evolve:engineering_ui" in blob,
    }
