# Examples

## Frontend view capsule

```bash
cd examples/frontend_view
python -m nexu init .
python -m nexu freeze . --name baseline
python -m nexu capsule create . --name menu-icons --domain menu --route /menu-icons --include "src/**"
python -m nexu capsule plan menu-icons --steps 10 --goal "Add icon preview table"
python -m nexu capsule blueprint menu-icons --print
python -m nexu capsule iterate menu-icons --steps 3 --goal "Add icon preview table"
python -m nexu capsule runtime menu-icons
python -m nexu capsule export-prompt menu-icons
python -m nexu capsule verify menu-icons
python -m nexu capsule report menu-icons
python -m nexu capsule status menu-icons
```

## Backend service capsule

```bash
cd examples/backend_service
python -m nexu init .
python -m nexu freeze . --name baseline
python -m nexu capsule create . --name users-api --domain users --endpoint GET:/api/users --include "app/**"
python -m nexu capsule plan users-api --steps 5
python -m nexu capsule blueprint users-api
python -m nexu capsule runtime users-api
python -m nexu capsule verify users-api
python -m nexu capsule report users-api
```

## Vertical slice capsule

```bash
cd examples/vertical_slice
python -m nexu init .
python -m nexu freeze . --name baseline
python -m nexu capsule create . --name flow --domain demo --route /flow --endpoint GET:/api/flow --include "src/**"
python -m nexu capsule plan flow --steps 10 --goal "Evolve a full UI + API flow"
python -m nexu capsule iterate flow --steps 10 --goal "Evolve a full UI + API flow"
python -m nexu capsule runtime flow
python -m nexu capsule export-prompt flow
python -m nexu capsule report flow
```

## Web App Dashboard Capsule (with visual evolution)

Folder: `examples/web_app_dashboard/`

This example demonstrates how to safely evolve a Web Application Dashboard (Baseline) into a target version featuring a live notification feed ($S_2$), automatically compiling visual mock sandboxes (`index.html`) using `nexu capsule runtime`.

Run the automated simulation:

```bash
cd examples/web_app_dashboard
uv run python run.py
```

## Web App Calculator Capsule (Simple vs. Scientific Mocks)

Folder: `examples/web_app_calculator/`

This example showcases how `nexu` handles visual comparison of two web application mocks side-by-side:

- **Simple Calculator (S0)**: Basic arithmetic interface.
- **Scientific Calculator (S2)**: High-fidelity visual mock layout including advanced trigonometry operations (`sin`, `cos`, `tan`, `log`).

Run the automated simulation:

```bash
cd examples/web_app_calculator
uv run python run.py
```

Run live Cinema from the repository root:

```bash
make cinema
```

Open the URL printed in logs (`Live HTTP Server started for Nexu: http://127.0.0.1:...`).

Live workflow:

1. Add a goal, then run iteration to generate **Options A-C**.
2. Compare options while the workspace stays unchanged.
3. Promote one option to workspace, then mark buttons (left drag = keep, right drag = remove) and apply marks.

When activating catalog projects, `goal_bootstrap.status` is `requires_llm`: goal contracts are
seeded immediately, while option generation happens in the next LLM iteration.

Bottom row panels:

- **Change history**: checkpoint list with `Restore UI + policy`.
- **Policy contracts**: baseline/active ledger lines and manifest actions.

Useful helpers:

```bash
make cinema-open
make cinema-stop
make cinema-repair
NEXU_CINEMA_NO_OPEN=1 make cinema
```

## Run all examples

```bash
python examples/run_examples.py
```

The smoke runner covers `frontend_view`, `backend_service`, `vertical_slice` and `mcp_service`.

The visual examples can also be run directly:

```bash
python examples/web_app_calculator/run.py
python examples/web_app_dashboard/run.py
```

The Pactown examples require `uv`, `pactown`, `requests` and free local ports:

```bash
python examples/web_app_pactown_ecosystem/run.py
python examples/web_app_event_monitor/run.py
```

The Docker Compose variant can be syntax-checked with:

```bash
docker compose -f examples/web_app_event_monitor/docker/docker-compose.yml config --quiet
```

## MCP service

Folder: `examples/mcp_service/`

Shows how to expose nexu tools to an MCP-capable IDE/agent through `nexu mcp serve --path .`. The MCP service exposes both dry-run promotion planning and the explicit write-capable `nexu_capsule_promote_apply` tool.

## Intract Policy Integration

Nexu dynamically integrates with a sibling or installed `intract` validation package through `src/nexu/intract_adapter.py`. When `verify_capsule` is executed, Intract policy validation is added to the deterministic nexu gates when available; integration failures are reported as warnings.
