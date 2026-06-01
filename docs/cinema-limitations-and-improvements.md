# Cinema: limitations and required improvements

Companion to [Cinema optimizations](cinema-optimizations.md). This document states **what Cinema cannot do reliably today**, **what was fixed recently** (so it is not mistaken for open work), and **what still needs improvement**, in priority order.

Audience: developers and operators working with HTTP imports, shared capsules, and the `/iterate` pipeline.

---

## Related documentation

| Document | Role |
|----------|------|
| [cinema-optimizations.md](cinema-optimizations.md) | Done items, scope routing, verification table |
| [roadmap.md](roadmap.md) | Broader Nexu 0.5.x–1.0.x plans (not Cinema-only) |
| Root [README](../README.md) | Cinema section: visual scopes vs `#functions` + LLM |

---

## Known limitations

These are **accepted constraints**, not bugs waiting for a one-line fix.

### HTTP / website import

| Limitation | Impact |
|------------|--------|
| **Single HTML snapshot** | Only the fetched page is stored; no full-site crawl, no deep SPA navigation history. |
| **Weak SPA / client JS** | Stripped or blocked scripts in preview; cookie banners, routers, and dynamic widgets may not behave like production. |
| **CDN / cross-origin assets** | Some stylesheets or images may fail in the iframe even with `<base href>`. Up to five same-origin stylesheets are mirrored locally; the rest depend on the live origin. |
| **Preview network isolation** | Head shim blocks cross-origin `fetch`/XHR from the cinema origin; reduces CORS noise but prevents live-site API calls from preview. |
| **No full-page LLM replace on imports** | Marked or `http-*` projects are routed to patch/offline paths; full-document regeneration is blocked when it would pollute the import snapshot. |
| **Re-fetch vs re-activate** | Re-activate rebuilds stages from stored `source/index.html` without network. A fresh live snapshot requires **re-import**. |

### Shared capsule workspace

| Limitation | Impact |
|------------|--------|
| **One cinema directory per capsule** | `stage0.html`, `alt_*.html`, and `intract_policy_ledger.json` are shared across all projects in that capsule (e.g. calculator + HTTP import in `scientific_calc`). |
| **Ledger / stage drift** | Without project-scoped filtering and HTTP stage restore, a prior session could leave calculator HTML or marks in an active import (see [Recovery](#operational-recovery) below). |
| **Checked-in example `server.py` may lag** | Runtime under `<workspace>/.nexu/capsules/<capsule>/cinema/` is refreshed on server start; `examples/*/cinema/server.py` is only aligned on intentional check-in. |

### Scope-isolated marks (KEEP / DELETE)

| Behavior | Detail |
|----------|--------|
| **Per `#scope` only** | Green/red marks apply to the active focus scope (`#colors`, `#functions`, …), not globally across scopes. |
| **Scope switch** | Switching to a scope with no prior marks shows an empty workspace overlay; returning to a scope restores marks from session cache or the policy ledger (`focus_scope` on each entry). |
| **Ledger** | Unscoped legacy ledger rows are ignored when a `focus_scope` filter is active (no global bleed). |
| **Interact contracts** | Marks are persisted via `append_policy_entry(..., focus_scope=…)` and reloaded through `GET /policy?focus_scope=…`. |

After template changes: `make cinema-restart`.

### Scope and LLM

| Limitation | Impact |
|------------|--------|
| **`#functions` needs LLM** | Layout/behavior changes on imported or dashboard projects require a configured LLM (`nexu.yaml` / workspace `.env`); offline fast path does not apply. |
| **Calculator `#keypad` layout** | Layout changes go through LLM only; visual `#keypad` palette/geometry can use offline/patch paths. |
| **`cinema.force_llm: true`** | Disables offline fast path for all scopes. |
| **Marked fragments without patch path** | Player may show: *"Marked fragments require patch/offline path; full-page LLM skipped"* — expected when marks exist on imports and full HTML generation is blocked. |

### Catalog and offline styling

| Limitation | Impact |
|------------|--------|
| **Generic offline shells** | Dashboard/calculator-style `inject_scope_style` shells; not bespoke per catalog project (monitor, api, mcp, slice). |
| **P3 seed assets** | Rich `stage0–2` per catalog project is deferred; activation uses generic or copied seeds unless product decides otherwise. |

### External integrations (deferred)

| Tool | Status |
|------|--------|
| `semcod/proxym`, `semcod/prellm`, `semcod/curllm` | Evaluated in [cinema-optimizations.md § fit check](cinema-optimizations.md#semcodwronai-fit-check); not wired into Cinema routing. |
| Repatch MCP / WebSocket demo | Standalone `repatch` package; not integrated into the main Cinema player loop. |
| **`.nexu` multi-project layout** | Imports and services are under capsule cinema paths; a full multi-artefact “services per project” layout is only partially stubbed (`project.json` `services` list). |

### Dependencies

| Limitation | Impact |
|------------|--------|
| **`repatch` path dependency** | Marked-context and UI patch primitives live in sibling repo `repatch`; CI and local tests need `uv sync` and import path (see `scripts/ci-cinema-smoke.sh`). |

---

## Fixed recently (not open P0/P1)

These issues **were** production problems; fixes are in tree but may still need **commit** and **manual browser verification**.

| Issue | Mitigation |
|-------|------------|
| Calculator HTML in HTTP project previews (`stage0` / `alt_*`) | `restore_http_import_stages_if_needed`, `http_stage_matches_import`, `reject_import_stage_replacement` |
| Policy ledger bleed across projects | Ledger entries filtered by `project_id` + `focus_scope`; new entries tagged |
| Shield false positive (`btn-sci` in injected JS) | Import validation regex matches CSS class tokens, not JS string literals |
| All buttons recolored on `#colors` | Narrow selector resolution in `repatch` marked context (KEEP/DELETE semantics) |
| Kadence heading inline `style="color: …"` ignored on `#colors` | `marked_scope_colors_css` adds `!important` text-color on marked node + descendants (`*`, `[style*='color']`); Kadence class resolved via text-label matching |
| Full-page LLM overwriting import snapshot | `should_block_full_html_iterate` + import stage guards on `/iterate` |
| `#orientation` DELETE stripped page layout on HTTP import | `inject_scope_style` uses `marked_scope_orientation_css` + column-goal page rules (not `restrict_scope_css_to_marks`) |
| `#display` / `#shapes` DELETE dropped h1/h2 and wrapper radii on HTTP import | Page-level `_web_display_scope_css` / `_web_shapes_scope_css` with marked-element extras |
| Promote applied all-scope DELETE spatial removes to alt previews | `/promote` passes `focus_scope`; ledger filtered per scope; visual scopes skip spatial delete on options |

Functional **P0/P1/P2** items in [cinema-optimizations.md](cinema-optimizations.md) tracking table are marked **done**. Remaining work is engineering debt, P3, operations, or repo-wide roadmap — not missing core Cinema features.

---

## Requires improvement

### Near-term (recommended before calling HTTP import “done”)

| Item | Action |
|------|--------|
| **Commit local changes** | Ledger scoping, HTTP restore, shield regex, template/example sync, tests — still uncommitted until you ask for a commit. |
| **Manual smoke on real import** | After `make cinema-restart`, re-activate `http-*` project; confirm iframe shows imported site (not calculator), `#colors` KEEP/DELETE affect only marked fragments, ledger has no calculator element IDs. |
| **Port / single instance** | Avoid two cinema servers (e.g. 8083 vs 8084) pointing at different workspace states. |

### Nice-to-have (engineering debt)

| Item | Notes |
|------|--------|
| **Extract `/iterate` orchestration** | `server.py.tmpl` ~2300 lines; move cache/LLM batch wiring into testable Python modules. |
| **Unify scope helpers** | `_effective_markpact_mode` vs `offline_fast_scopes_for_kind` duplication in template exception handler. |
| **Example `server.py` policy** | Align `examples/*/cinema/server.py` on check-in; document that runtime always regenerates from template. |
| **Type hints** | Broader annotations on generated-server helpers (low priority). |
| **planfile / code2llm tickets** | `project/planfile-tickets.yaml` — quality refactors (god functions, `do_GET`/`do_POST`), not Cinema UX blockers. |

### Deferred (P3 / product decisions)

| Item | Blocker |
|------|---------|
| **Rich seed HTML per catalog project** | Product choice: custom `stage0–2` vs generic dashboard seed for monitor, api, mcp, slice. |
| **Per-project offline CSS** | Beyond generic shells in `inject_scope_style`. |
| **Server template package split** | Stable import surface for generated `server.py` (incremental modules vs `cinema_server_runtime`). |

See also [roadmap.md](roadmap.md) for repository-wide cleanup (module splits, disposable example workspaces, MCP safeguards, TestQL).

---

## Operational recovery

Use when session export or preview shows **calculator DOM** (`#functions`, `calc-body`, Scientific Calculator) under an **active HTTP import** (`http-*`).

1. **`make cinema-restart`** — regenerates capsule `server.py` from template and restarts the player.
2. **Projects tab → re-activate** the HTTP import — rebuilds `stage0` and Options A–C from `imported_projects/<id>/source/index.html` without re-fetch; resets scoped ledger behavior for that project.
3. **Optional re-import** — only if you need a fresh snapshot from the live URL (new preprocess: `nexu-visual.css`, `nexu-outline.html`).
4. **Verify** — `activeProjectId` matches import id; `htmlPreviews` contain site markup (e.g. navigation labels from the target site), not calculator keypad markup.

If iteration still fails with patch/offline messages, check `focus_scope` (visual scopes vs `#functions`) and LLM configuration for function-level edits.

---

## Verification checklist

| Check | Command / location |
|-------|-------------------|
| Unit / integration tests | `uv run python -m pytest -q tests/test_cinema_*.py` (and related repatch tests if linked) |
| CI cinema smoke | `make ci-cinema-smoke` (`uv sync` + `uv run pytest`) |
| Visual offline scopes | `make cinema` → `#colors`, `#display`, … without LLM key |
| `#functions` on import | Requires LLM key in `.env` / `nexu.yaml` |
| Template sync | `make cinema-restart` after editing `src/nexu/templates/cinema/*.tmpl` |

---

## Summary matrix

| Category | Status |
|----------|--------|
| Core `/iterate` routing (offline / cache / LLM patch) | Implemented |
| HTTP import + preprocess + shield | Implemented |
| Ledger + stage isolation for shared capsule | Implemented (verify in browser) |
| HTTP / SPA / CDN limitations | **Documented constraints** |
| Template refactor + P3 seeds | **Open** (nice-to-have / deferred) |
| External proxym/prellm/curllm | **Deferred** |

When updating behavior, change code and tests first, then add a short note to [cinema-optimizations.md](cinema-optimizations.md) (done items) or this file (limitations / open improvements).
