# Ticket 004: Fix cinema llm status lazy litellm check

- **ID**: ticket-004
- **Owner**: tom
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-15

## Goal and scope

Fix synchronous `litellm` import in `_litellm_available()` inside
`src/nexu/templates/cinema/server.py.tmpl` so `GET /llm/status` checks
`importlib.util.find_spec("litellm")` (and `sys.modules`) lazily instead of
blocking for ~8s on cold `from litellm import completion`, and add a regression
test in `tests/test_cinema_server.py`.

## Acceptance criteria

- [x] AC-01: `_litellm_available()` in `src/nexu/templates/cinema/server.py.tmpl` avoids eager `from nexu.cinema_llm import _litellm_completion` import and responds within test timeouts.
- [x] AC-02: `tests/test_cinema_server.py` passes completely, including `/llm/status` startup polling tests.
- [x] AC-03: Full `pytest tests/` suite and `./project/governance-check.sh --no-cache` pass cleanly.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
