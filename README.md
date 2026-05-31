# Nexu


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.5.16-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$3.02-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-9.3h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $3.0240 (22 commits)
- 👤 **Human dev:** ~$926 (9.3h @ $100/h, 30min dedup)

Generated on 2026-05-31 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

**Nexu** — **Visual Intent Contract Orchestrator**.

Nexu is a Python package and CLI for creating small, isolated project capsules from a large codebase.
It helps you freeze a baseline, extract a slice of code/data/contracts, evolve that slice through multiple
LLM or human iterations, and verify the result against formal intent contracts before promoting it back.

The core workflow is:

```text
freeze → capsule create → plan → blueprint → iterate → runtime → export-prompt → verify → report → promote
```

Nexu is designed to work with **Intract**-style intent contracts, but it can run as a standalone prototype.
The goal is not to make an LLM magically correct. The goal is to keep the LLM inside a small, versioned,
contract-bound sandbox and detect when its output diverges from declared intent.

## Current status

The 0.5.x line includes capsule orchestration, MCP tools, live Cinema UI evolution and dynamic Intract validation:

- `capsule orchestrate` creates an offline or optional LLM-assisted step-by-step capsule evolution plan,
- orchestration writes `orchestration.yaml`, `orchestration.md`, `orchestration-prompt.md` and context YAML,
- `nexu mcp tools` lists tools available to IDE/agent clients,
- `nexu mcp serve` exposes Nexu operations through a conservative MCP-compatible stdio JSON-RPC service,
- MCP exposes both dry-run promotion planning and an explicit apply tool,
- Cinema assets are generated from package templates under `src/nexu/templates/cinema/`,
- LLM network calls remain disabled unless explicitly allowed in `nexu.yaml`.

## Why Nexu?

Long-running IDE prompting has a common failure mode:

```text
large repo + vague task + many steps = context drift and hallucinated implementation
```

Nexu changes the operating model:

```text
large repo
  ↓ freeze baseline
small capsule
  ↓ evolve only this capsule
verified result
  ↓ promote to the real project
```

## Install locally

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
nexu --help
```

## First run

```bash
nexu init .
nexu freeze . --name baseline
nexu capsule create . --name menu-icons --domain menu --include "examples/frontend_view/src/**" --route /menu-icons
nexu capsule plan menu-icons --steps 10 --goal "Add preview, confidence and reason fields"
nexu capsule blueprint menu-icons --print
nexu capsule iterate menu-icons --steps 3 --goal "Add preview, confidence and reason fields"
nexu capsule runtime menu-icons
nexu capsule orchestrate menu-icons --steps 10 --goal "Add preview, confidence and reason fields"
nexu capsule export-prompt menu-icons
nexu capsule verify menu-icons
nexu capsule review menu-icons
nexu capsule report menu-icons
nexu capsule bundle menu-icons
nexu capsule diff menu-icons
nexu capsule drift menu-icons
nexu capsule promote menu-icons --dry-run
```

## Key Features Added Recently

- **Secure Workspace Promotion**: Support for applying capsule changes to the source workspace via the `nexu capsule promote --apply` command (and via the `nexu_capsule_promote_apply` MCP tool).
- **Dynamic Intract Policy Engine Integration**: Runs the actual sibling `intract` package validations (including AST verification and contract compliance) during the capsule `verify` step to guarantee correctness.
- **Web App Dashboard Evolution Example**: Fully details multi-stage sandbox visualization and evolution under `examples/web_app_dashboard`.
- **Web App Calculator Mock Example**: Compares a simple arithmetic layout (S0) and a scientific layout (S2) under `examples/web_app_calculator` (evolving the `calc` capsule).
- **Web App Database Analytics Example**: Showcases transition from raw SQL/NoSQL table logs to glassmorphic visual charts under `examples/web_app_analytics`.

## Important folders

```text
src/nexu/       Python package
docs/           documentation
examples/       runnable example projects
tests/          unit tests
```

## Documentation

Start here:

- [Docs index](docs/README.md)
- [New Project Web Integration Guide](examples/web_app_pactown_ecosystem/services/web/README.md)
- [Calculator UI & Shell Evolution Guide](examples/web_app_calculator/README.md)
- [Database Analytics Dashboard Evolution Guide](examples/web_app_analytics/)
- [OpenRouter Real-Time Integration Guide](examples/realtime_lane_nexu_sync.py)
- [Getting started](docs/getting-started.md)
- [Architecture](docs/architecture.md)
- [Commands](docs/commands.md)
- [Capsule format](docs/capsule-format.md)
- [Intent contracts](docs/intent-contracts.md)
- [Verification model](docs/verification.md)
- [Runtime and reports](docs/runtime-and-reports.md)
- [LLM review and handoff](docs/llm-review.md)
- [LLM orchestration](docs/llm-orchestration.md)
- [MCP service](docs/mcp-service.md)
- [Examples](docs/examples.md)
- [Roadmap](docs/roadmap.md)

## Main commands

```bash
nexu init .
nexu freeze . --name baseline
nexu capsule create . --name my-slice --include "src/my_module/**"
nexu capsule list
nexu capsule status my-slice
nexu capsule blueprint my-slice
nexu capsule iterate my-slice --steps 10 --goal "Evolve final screen"
nexu capsule orchestrate my-slice --steps 10 --goal "Evolve final screen"
nexu capsule export-prompt my-slice
nexu capsule diff my-slice
nexu capsule review my-slice
nexu capsule bundle my-slice
nexu capsule drift my-slice
nexu capsule verify my-slice
nexu capsule review my-slice
nexu capsule bundle my-slice
nexu capsule promote my-slice --dry-run
nexu mcp tools
nexu mcp serve --path .
```

## Verified examples

The local example smoke runner covers `frontend_view`, `backend_service`, `vertical_slice` and `mcp_service`:

```bash
python examples/run_examples.py
```

The calculator and dashboard examples can be run directly:

```bash
python examples/web_app_calculator/run.py
python examples/web_app_dashboard/run.py
```

The Pactown examples require `uv`, `pactown` and local ports to be free:

```bash
python examples/web_app_pactown_ecosystem/run.py
python examples/web_app_event_monitor/run.py
docker compose -f examples/web_app_event_monitor/docker/docker-compose.yml config --quiet
```

## Quality checks

Use the lightweight local quality profile before changing release-facing code:

```bash
make quality
```

It runs tests, local Markdown link validation, source-level Intract checks, duplication scanning and the lint subset that is currently clean. For a full backlog-oriented report, use:

```bash
make quality-strict
```

The same fast profile is described in `pyqual.yaml` for tools that prefer declarative pipelines.

## Cinema (LLM live mode)

To run Cinema with real LLM evolution:

1. Add API key to `.env` in repo root:

```bash
OPENROUTER_API_KEY=...
```

1. Enable network calls in workspace config (`examples/web_app_calculator/workspace/nexu.yaml`):

```yaml
llm:
  allow_network_calls: true
  api_key_env: OPENROUTER_API_KEY
```

1. Run Cinema iteration:

```bash
make cinema
```

Use the URL printed in the log (`Live HTTP Server started for Nexu: http://127.0.0.1:…`) — not a fixed port (8080 may be taken by another service).

Stop stale cinema servers before restarting:

```bash
make cinema-stop
make cinema
```

Useful helpers:

```bash
make cinema-open      # run and open current player URL
make cinema-restart   # stop old server and start fresh player
make cinema-repair    # re-inject runtime scripts into generated HTML files
NEXU_CINEMA_NO_OPEN=1 make cinema
```

**Simple iteration flow (3 steps):**

1. **Goal** — type what you want (e.g. chemical calculator) → **Add goal** → **Generate Options A–C**.
2. **Compare** — review Options A, B, C (workspace on the left stays unchanged).
3. **Promote & refine** — click an option to save it to the workspace → drag on buttons (left = keep, right = remove) → **Apply marks to workspace**.

**History & policy (bottom row, two columns):** left — **Change history** with **Restore UI + policy** (rewinds HTML, ledger, and merges contracts into manifests); right — **Policy contracts** (baseline + active ledger lines, manifest actions). Use the URL from `make cinema` output, not a fixed port.

1. Run tests:

```bash
make test
make ci-cinema-smoke   # nexu + sibling intract + cinema policy dry-run
```

You can override defaults from `Makefile` inline:

```bash
make cinema CINEMA_CAPSULE=scientific_calc CINEMA_PATH=examples/web_app_calculator/workspace
```

Model override (otherwise `LLM_MODEL` from workspace `.env`):

```bash
make cinema CINEMA_MODEL=openrouter/google/gemini-3.1-flash-lite-preview
```

## License

Licensed under Apache-2.0.
