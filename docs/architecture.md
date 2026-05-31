# Architecture

nexu is organized around one main concept: the **capsule**.

```text
large project
  -> freeze baseline
  -> create capsule from selected files/routes/endpoints
  -> plan S1..S10
  -> iterate inside capsule
  -> build runtime/mock
  -> verify contracts and evidence
  -> report
  -> promote after review
```

## Layers

```text
CLI
  -> capsule orchestration
  -> blueprint / runtime / reports
  -> Intract-style contracts
  -> diff / drift / verification
  -> promotion plan
```

## Important modules

```text
src/nexu/freeze.py          baseline hash snapshots
src/nexu/capsule.py         capsule creation/load/save
src/nexu/plan.py            deterministic S1..Sn iteration planning
src/nexu/blueprint.py       UI/API/test blueprint generation
src/nexu/runtime.py         static HTML capsule runtime/mock
src/nexu/export_prompt.py   LLM-ready prompt export
src/nexu/verify.py          deterministic verification gates and evidence
src/nexu/intract_adapter.py dynamic adapter for sibling/installed Intract validation
src/nexu/report.py          Markdown/HTML/YAML reports
src/nexu/journal.py         capsule event history
src/nexu/promote.py         promotion plan
src/nexu/cinema.py          Cinema player assembly workflow
src/nexu/cinema_server.py   generated Cinema HTTP server launcher
src/nexu/templates/cinema/  generated Cinema HTML/Python templates
```

## Why this shape?

nexu should not let an LLM edit the full project blindly. The LLM should work inside a small, versioned, contract-bound capsule. The source project remains frozen until promotion review.

## Relationship with Intract

nexu uses Intract-style contracts as the formal language of intent. It includes a lightweight parser for `@intract.v1` lines and `intract.yaml`, and the verification step dynamically uses a sibling or installed `intract` package when available.
