from nexu.cinema_llm_contracts import (
    build_llm_communication_contract_lines,
    build_llm_contract_block,
    build_llm_option_variants,
)


def test_calculator_llm_contract_protects_screen():
    lines = build_llm_communication_contract_lines(
        ui_type="calculator",
        focus_scope="functions",
        variant_label="Option A",
        keep_els=["7", "ln"],
        delete_els=["screen"],
    )

    joined = "\n".join(lines)
    assert "intent:generate:complete_html" in joined
    assert "intent:protect:calculator_display" in joined
    assert "forbid:title_inside_screen,goal_inside_screen,variant_inside_screen" in joined
    assert "validate:screen_output_only,no_title_in_screen" in joined


def test_llm_contract_block_tracks_scope_and_policy():
    block = build_llm_contract_block(
        ui_type="dashboard",
        focus_scope="colors",
        variant_label="Option B",
        keep_els=["kpi-card"],
        delete_els=["legacy-filter"],
        project_goal="analytics workspace for cohorts",
        current_state="dashboard has KPI cards",
        expected_version="change only colors",
        element_hints=["keep chart layout"],
    )

    assert "respect_scope:colors" in block
    assert "respect:user_expectation_contract" in block
    assert "analytics workspace for cohorts" in block
    assert "change only colors" in block
    assert "keep chart layout" in block
    assert "keep_elements_present" in block
    assert "kpi-card" in block
    assert "legacy-filter" in block


def test_llm_option_variants_are_scope_contracts_not_domain_templates():
    variants = build_llm_option_variants(
        focus_scope="colors",
        focus_text="Primary project goal: improve imported app.",
    )

    assert [v[0] for v in variants] == ["alt_a.html", "alt_b.html", "alt_c.html"]
    joined = "\n".join(v[2] for v in variants)
    assert "INTRACT-SCOPED VARIANT" in joined
    assert "#colors" in joined
    assert "current HTML" in joined
    assert "prebuilt domain templates" in joined
    assert "KPI" not in joined
    assert "chemical" not in joined.lower()
