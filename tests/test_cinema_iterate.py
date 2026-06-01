from nexu.cinema_iterate import build_iterate_response_payload


def test_build_iterate_response_payload_offline_shape() -> None:
    payload = build_iterate_response_payload(
        status_msg="proposed_options_offline",
        iteration_mode="goal_options",
        focus_scope="colors",
        focus_scope_label="#colors",
        current_stage=0,
        keep_els=["btn-1"],
        delete_els=[],
        ledger_keep=[],
        ledger_delete=[],
        session_keep=[],
        session_delete=[],
        options_written=["Option A (colors)", "Option B (colors)", "Option C (colors)"],
        spatial_removed=[],
        llm_error=None,
        policy_entry=None,
        intract_validation=None,
        history_checkpoint=None,
        options_sync=None,
    )
    assert payload["status"] == "proposed_options_offline"
    assert payload["mode"] == "goal_options"
    assert payload["focus_scope"] == "colors"
    assert payload["focus_scope_label"] == "#colors"
    assert payload["keep_count"] == 1
    assert payload["delete_count"] == 0
    assert len(payload["options_written"]) == 3
    assert payload["options_stamp"] is not None
    assert payload["error"] is None
    assert payload["policy_updated"] is False


def test_build_iterate_response_payload_functions_llm_failed_hint() -> None:
    payload = build_iterate_response_payload(
        status_msg="llm_failed: network disabled",
        iteration_mode="goal_options",
        focus_scope="functions",
        focus_scope_label="#functions",
        current_stage=0,
        keep_els=[],
        delete_els=[],
        ledger_keep=[],
        ledger_delete=[],
        session_keep=[],
        session_delete=[],
        options_written=[],
        spatial_removed=[],
        llm_error=None,
        policy_entry=None,
        intract_validation=None,
        history_checkpoint=None,
        options_sync=None,
    )
    assert payload["status"].startswith("llm_failed")
    assert payload["focus_scope"] == "functions"
    assert payload["error"]
    assert "visual scope" in payload["error"].lower()
    assert payload["options_stamp"] is None


def test_build_iterate_response_payload_defaults_scope_label() -> None:
    payload = build_iterate_response_payload(
        status_msg="skipped",
        iteration_mode="goal_options",
        focus_scope="display",
        focus_scope_label="",
        current_stage=1,
        keep_els=[],
        delete_els=[],
        ledger_keep=[],
        ledger_delete=[],
        session_keep=[],
        session_delete=[],
        options_written=[],
        spatial_removed=[],
        llm_error="upstream error",
        policy_entry={"status": "goal_defined"},
        intract_validation=None,
        history_checkpoint=None,
        options_sync=None,
    )
    assert payload["focus_scope_label"] == "#display"
    assert payload["error"] == "upstream error"
    assert payload["policy_updated"] is True
