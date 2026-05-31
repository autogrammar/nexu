# Roadmap

## 0.5.x — current line

Done:

- deterministic `capsule plan`,
- static HTML capsule runtime,
- Markdown/HTML/YAML capsule report,
- capsule journal,
- runtime data export with blueprint, fixtures, contracts and iteration timeline,
- LLM orchestration and review packet generation,
- MCP stdio tools and resources,
- Cinema live UI evolution with generated template assets,
- dynamic Intract adapter during `verify`.

## Near-term cleanup

Planned:

- split remaining large modules and CLIs by responsibility,
- make example generated workspaces disposable by default,
- tighten MCP apply safeguards and documentation,
- finish repository-wide ruff cleanup,
- mapping outputs to exact files/functions,
- TestQL runtime probes.

## 0.6.x — richer runtimes

Planned:

- optional FastAPI mock runtime,
- optional Vite/React preview shell,
- fixture editor,
- API response editor,
- simple visual diff between S0 and latest state,
- auto-generated follow-up tickets from verification failures.

## 1.0.0 — stable capsule protocol

Required:

- stable `nexu.yaml`,
- stable `capsule.yaml`,
- stable promotion plan format,
- robust verification reports,
- examples as integration tests.
