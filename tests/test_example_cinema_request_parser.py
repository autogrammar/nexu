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


def _iterate_handler_class():
    tree = ast.parse(SERVER_PATH.read_text(encoding="utf-8"))
    helper_names = {
        "_request_list",
        "_normalized_string_list",
        "_request_hints",
        "_normalized_prompt_hints",
        "_scope_prompt_block",
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
    return namespace["_IterateHandler"]


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
