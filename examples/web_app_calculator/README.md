# Web App Calculator Nexu Capsule Example

This example demonstrates the visual difference between:

1. **Simple Calculator (Baseline S0)**: The simple arithmetic interface.
2. **Scientific Calculator (Target S2)**: The evolved scientific UI with trigonometric and log buttons.

## Structure

- `src/calculator.py`: Holds the rendering engine.
- `fixtures/inputs.json`: Calculator display states.
- `run.py`: Script compiling both mock sandboxes.

## Live Cinema (LLM evolution)

From the **nexu** repo root:

```bash
make cinema
```

Open the URL printed in the log (player is generated under `workspace/.nexu/capsules/scientific_calc/cinema/`).

The static `cinema/cinema_player.html` in this folder is only a **demo slideshow** — not the live evolution dashboard.

**Workflow:** goal → Generate Options A–C → promote one option → mark buttons in the workspace → Apply marks.

Bottom row panels in live Cinema:

- **Change history**: checkpoint timeline with `Restore UI + policy`.
- **Policy contracts**: baseline + active ledger contracts, plus manifest actions.

Useful commands from repo root:

```bash
make cinema-open
make cinema-stop
make cinema-repair
NEXU_CINEMA_NO_OPEN=1 make cinema
```
