"""Intract contracts for Nexu-to-LLM Cinema communication."""

from __future__ import annotations

import re

OPTION_FILES = ("alt_a.html", "alt_b.html", "alt_c.html")
OPTION_INTENSITIES = ("conservative", "balanced", "ambitious")


def _slug(value: str, *, fallback: str = "general") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug[:32] or fallback


def _line(
    contract_id: str,
    intent: str,
    meaning: str,
    *,
    domain: str = "llm.ui",
    require: list[str] | None = None,
    forbid: list[str] | None = None,
    validate: list[str] | None = None,
) -> str:
    input_fields = ["current_html", "goal", "ui_constraints", "scope_contract"]
    output_fields = ["complete_html", "contract_evidence"]
    effects = ["read", "generate"]
    forbids = list(forbid or ["script_tags", "secret_leak", "unrequested_regression"])
    requires = list(require or ["complete_html_document"])
    validators = list(
        validate
        or [
            "html_document",
            "no_script_tags",
            "keep_elements_present",
            "delete_elements_absent",
        ]
    )
    safe_meaning = meaning.replace('"', "'")
    return (
        f"@intract.v1 id:{contract_id} scope:llm_call intent:{intent} "
        f"priority:1 domain:{domain} input:{','.join(input_fields)} "
        f"output:{','.join(output_fields)} effect:{','.join(effects)} "
        f"forbid:{','.join(forbids)} require:{','.join(requires)} "
        f"validate:{','.join(validators)} meaning:\"{safe_meaning}\""
    )


def _compact(value: str, *, max_len: int = 180) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "..."


def build_llm_option_variants(
    *,
    focus_scope: str,
    focus_text: str = "",
) -> list[tuple[str, str, str]]:
    """
    Return A/B/C prompt contracts without project-domain templates.

    The LLM receives the current HTML, project context and Intract contracts; these
    variants only describe iteration intensity inside the selected scope.
    """
    scope = _slug(focus_scope or "functions")
    suffix = (" " + focus_text.strip()) if focus_text.strip() else ""
    variants: list[tuple[str, str, str]] = []
    for filename, intensity in zip(OPTION_FILES, OPTION_INTENSITIES, strict=True):
        label = f"Option {filename[4].upper()} ({scope}: {intensity})"
        note = (
            f"INTRACT-SCOPED VARIANT. Focus scope: #{scope}. "
            f"Variant intensity: {intensity}. "
            "Infer project-specific changes from the current HTML, active project metadata, "
            "user expectation contract, KEEP/DELETE policy, and baseline contracts. "
            "Do not use prebuilt domain templates; do not introduce unrelated scope changes."
            + suffix
        )
        variants.append((filename, label, note))
    return variants


def _format_contract_params(
    keep_els: list[str] | None,
    delete_els: list[str] | None,
    project_goal: str,
    current_state: str,
    expected_version: str,
    element_hints: list[str] | None,
) -> tuple[str, str, str, str, str, str]:
    keep = ", ".join(list(keep_els or [])[:16]) or "none"
    delete = ", ".join(list(delete_els or [])[:16]) or "none"
    goal = _compact(project_goal)
    current = _compact(current_state)
    expected = _compact(expected_version)
    hints = "; ".join(_compact(h, max_len=80) for h in list(element_hints or [])[:8])
    return keep, delete, goal, current, expected, hints


def build_llm_communication_contract_lines(
    *,
    ui_type: str,
    focus_scope: str,
    variant_label: str,
    keep_els: list[str] | None = None,
    delete_els: list[str] | None = None,
    project_goal: str = "",
    current_state: str = "",
    expected_version: str = "",
    element_hints: list[str] | None = None,
) -> list[str]:
    """Contracts the LLM must satisfy for one Cinema generation call."""
    ui = _slug(ui_type or "web")
    scope = _slug(focus_scope or "functions")
    variant = _slug(variant_label or "variant")
    keep, delete, goal, current, expected, hints = _format_contract_params(
        keep_els, delete_els, project_goal, current_state, expected_version, element_hints
    )

    lines = [
        _line(
            f"llm.cinema.{ui}.{scope}.{variant}.html",
            "generate:complete_html",
            "Return exactly one complete HTML document for the requested Cinema option. "
            "Do not return prose, markdown fences, partial snippets, or multiple files.",
            require=["current_html_context", "complete_html_document"],
        ),
        _line(
            f"llm.cinema.{ui}.{scope}.{variant}.scope",
            f"respect_scope:{scope}",
            "Apply only the selected focus scope for this iteration. Keep unrelated "
            "axes stable unless the user goal or KEEP/DELETE contracts require a change.",
            require=[f"focus_scope:{scope}"],
            validate=["scope_only_change", "no_unrequested_regression"],
        ),
        _line(
            f"llm.cinema.{ui}.{scope}.{variant}.dialog",
            "respect:user_expectation_contract",
            "Treat the latest user expectation as the canonical dialog contract. "
            f"Goal: {goal or 'none'}. Current slice: {current or 'not specified'}. "
            f"Expected/actions: {expected or 'not specified'}. "
            f"Element notes: {hints or 'none'}.",
            require=["latest_user_expectation", "dialog_contract_precedence"],
            validate=["goal_alignment", "expected_actions_applied"],
        ),
        _line(
            f"llm.cinema.{ui}.{scope}.{variant}.policy",
            "respect:ui_policy",
            f"Preserve KEEP elements ({keep}) and remove/redesign only DELETE elements "
            f"({delete}). Current KEEP wins over old DELETE.",
            require=["keep_elements_present"],
            validate=["keep_elements_present", "delete_elements_absent"],
        ),
    ]
    if ui == "calculator":
        lines.append(
            _line(
                f"llm.cinema.{ui}.{scope}.{variant}.display",
                "protect:calculator_display",
                "The #screen element is only the calculator output display. It may contain "
                "a number, formula, or current expression, but never the app title, goal, "
                "variant name, or explanatory text.",
                require=["calc.display.output_only"],
                forbid=["title_inside_screen", "goal_inside_screen", "variant_inside_screen"],
                validate=["screen_output_only", "no_title_in_screen"],
            )
        )
    return lines


def build_llm_contract_block(
    *,
    ui_type: str,
    focus_scope: str,
    variant_label: str,
    keep_els: list[str] | None = None,
    delete_els: list[str] | None = None,
    project_goal: str = "",
    current_state: str = "",
    expected_version: str = "",
    element_hints: list[str] | None = None,
) -> str:
    lines = build_llm_communication_contract_lines(
        ui_type=ui_type,
        focus_scope=focus_scope,
        variant_label=variant_label,
        keep_els=keep_els,
        delete_els=delete_els,
        project_goal=project_goal,
        current_state=current_state,
        expected_version=expected_version,
        element_hints=element_hints,
    )
    return "\n".join(f"- {line}" for line in lines)
