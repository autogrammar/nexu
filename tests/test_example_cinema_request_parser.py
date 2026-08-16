from __future__ import annotations

import ast
import json
from pathlib import Path


SERVER_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "web_app_calculator"
    / "cinema"
    / "server.py"
)


def _iterate_runtime():
    tree = ast.parse(SERVER_PATH.read_text(encoding="utf-8"))
    helper_names = {
        "_request_list",
        "_normalized_string_list",
        "_request_hints",
        "_normalized_prompt_hints",
        "_scope_prompt_block",
        "_iteration_mode_flags",
        "_annotation_ids",
    }
    selected = [
        node
        for node in tree.body
        if (
            isinstance(node, ast.FunctionDef)
            and node.name in helper_names
        )
        or (
            isinstance(node, ast.ClassDef)
            and node.name == "_IterateHandler"
        )
    ]
    namespace = {"json": json}
    exec(compile(ast.Module(body=selected, type_ignores=[]), SERVER_PATH, "exec"), namespace)
    return namespace


def _iterate_handler_class():
    return _iterate_runtime()["_IterateHandler"]


def test_request_parser_normalizes_explicit_goal_and_scope() -> None:
    handler_class = _iterate_handler_class()
    payload = {
        "prompt": "move button",
        "current_stage": 3,
        "annotations": "invalid",
        "selected_fragments": {"invalid": True},
        "user_goal": "  Improve checkout  ",
        "element_hints": [" button ", "", "footer"],
        "focus_scope": "checkout",
        "focus_scope_label": "Checkout form",
        "current_state": "v1",
        "expected_version": "v2",
    }

    handler = handler_class(None, json.dumps(payload).encode())
    handler._parse_request_data()

    assert handler.annotations == []
    assert handler.selected_fragments == []
    assert handler.normalized_hints == [
        "Improve checkout",
        "button",
        "footer",
        "Focus scope Checkout form",
    ]
    assert handler.scope_block == (
        "Checkout form\nCurrent slice: v1\nExpected version/actions: v2"
    )


def test_request_parser_preserves_legacy_hint_mapping() -> None:
    handler_class = _iterate_handler_class()
    payload = {"user_hints": ["Legacy goal", "header", "submit"]}

    handler = handler_class(None, json.dumps(payload).encode())
    handler._parse_request_data()

    assert handler.user_goal == "Legacy goal"
    assert handler.normalized_element_hints == ["header", "submit"]
    assert handler.normalized_hints == ["Legacy goal", "header", "submit"]
    assert handler.goal_block == "Legacy goal"
    assert handler.scope_block == "none selected"


def test_iteration_mode_respects_explicit_and_automatic_signals() -> None:
    handler_class = _iterate_handler_class()
    handler = handler_class(None, b"{}")

    handler.requested_mode = "goal_options"
    handler.user_goal = "Improve checkout"
    handler._determine_iteration_mode()
    assert (handler.apply_active, handler.apply_options) == (False, True)

    handler.requested_mode = "active_workspace"
    handler.user_goal = ""
    handler.session_delete = ["button"]
    handler._determine_iteration_mode()
    assert (handler.apply_active, handler.apply_options) == (True, False)

    handler.requested_mode = ""
    handler.session_delete = []
    handler.pending_goal = True
    handler._determine_iteration_mode()
    assert (handler.apply_active, handler.apply_options) == (False, True)

    handler.pending_goal = False
    handler._determine_iteration_mode()
    assert (handler.apply_active, handler.apply_options) == (False, False)


def test_annotation_ids_filter_type_and_blank_identifiers() -> None:
    annotation_ids = _iterate_runtime()["_annotation_ids"]
    annotations = [
        {"type": "KEEP", "id": " header "},
        {"type": "DELETE", "id": "submit"},
        {"type": "KEEP", "id": " "},
        "invalid",
    ]

    assert annotation_ids(annotations, "KEEP") == ["header"]
    assert annotation_ids(annotations, "DELETE") == ["submit"]
