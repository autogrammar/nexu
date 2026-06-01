# Nexu

Visual Intent Contract Orchestrator: freeze project slices, evolve capsules, verify intent contracts.

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Makefile Targets](#makefile-targets)
- [Code Analysis](#code-analysis)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `nexu`
- **version**: `0.5.22`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Makefile, testql(1), app.doql.less, pyqual.yaml, goal.yaml, .env.example, project/(3 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: nexu;
  version: 0.5.22;
}

dependencies {
  runtime: "pyyaml>=6.0, typer>=0.12.0, rich>=13.0, litellm>=1.0";
  dev: "pytest>=7.0, ruff>=0.4, mypy>=1.8, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
}

interface[type="api"] {
  type: rest;
  framework: fastapi;
}

interface[type="cli"] {
  framework: argparse;
}
interface[type="cli"] page[name="nexu"] {

}

workflow[name="test"] {
  trigger: manual;
  step-1: run cmd=pytest -q;
}

workflow[name="examples"] {
  trigger: manual;
  step-1: run cmd=python examples/run_examples.py;
}

workflow[name="docs-links"] {
  trigger: manual;
  step-1: run cmd=python scripts/check-doc-links.py .;
}

workflow[name="quality-intract"] {
  trigger: manual;
  step-1: run cmd=intract check src --format text;
  step-2: run cmd=intract coverage src;
}

workflow[name="quality-redup"] {
  trigger: manual;
  step-1: run cmd=redup scan src --format toon --min-lines 8;
}

workflow[name="quality"] {
  trigger: manual;
  step-1: run cmd=ruff check \;
  step-2: run cmd=src/nexu/cinema.py \;
  step-3: run cmd=src/nexu/cinema_server.py \;
  step-4: run cmd=src/nexu/cinema_baseline_contracts.py \;
  step-5: run cmd=src/nexu/cinema_goal_contracts.py \;
  step-6: run cmd=src/nexu/cinema_html.py \;
  step-7: run cmd=src/nexu/cinema_html_validate.py \;
  step-8: run cmd=src/nexu/cinema_llm_contracts.py \;
  step-9: run cmd=src/nexu/cinema_markpact.py \;
  step-10: run cmd=src/nexu/cinema_dom_patch.py \;
  step-11: run cmd=src/nexu/cinema_project_ir.py \;
  step-12: run cmd=src/nexu/cinema_project_imports.py \;
  step-13: run cmd=src/nexu/cinema_projects.py \;
  step-14: run cmd=src/nexu/cinema_scripts.py \;
  step-15: run cmd=src/nexu/cinema_publish.py \;
  step-16: run cmd=src/nexu/cinema_offline_options.py \;
  step-17: run cmd=src/nexu/cinema_options_cache.py \;
  step-18: run cmd=src/nexu/cinema_ui_patch.py \;
  step-19: run cmd=src/nexu/fast_delivery/__init__.py \;
  step-20: run cmd=src/nexu/fast_delivery/context.py \;
  step-21: run cmd=src/nexu/fast_delivery/options.py \;
  step-22: run cmd=src/nexu/fast_delivery/router.py \;
  step-23: run cmd=src/nexu/intract.py \;
  step-24: run cmd=src/nexu/verify.py \;
  step-25: run cmd=src/nexu/intract_adapter.py \;
  step-26: run cmd=tests/test_cinema_server.py \;
  step-27: run cmd=tests/test_cinema_baseline_contracts.py \;
  step-28: run cmd=tests/test_cinema_goal_contracts.py \;
  step-29: run cmd=tests/test_cinema_markpact.py \;
  step-30: run cmd=tests/test_cinema_dom_patch.py \;
  step-31: run cmd=tests/test_cinema_project_ir.py \;
  step-32: run cmd=tests/test_cinema_project_imports.py \;
  step-33: run cmd=tests/test_cinema_projects.py \;
  step-34: run cmd=tests/test_cinema_scripts.py \;
  step-35: run cmd=tests/test_cinema_publish.py \;
  step-36: run cmd=tests/test_cinema_offline_options.py \;
  step-37: run cmd=tests/test_cinema_options_cache.py \;
  step-38: run cmd=tests/test_cinema_ui_patch.py \;
  step-39: run cmd=tests/test_fast_delivery.py;
}

workflow[name="quality-strict"] {
  trigger: manual;
  step-1: run cmd=pytest -q;
  step-2: run cmd=ruff check src tests --statistics;
  step-3: run cmd=intract check . --format text;
  step-4: run cmd=redup scan src --format toon;
}

workflow[name="cinema"] {
  trigger: manual;
  step-1: run cmd=uv sync --quiet;
  step-2: run cmd=$(CINEMA_MODEL_ARG) uv run nexu capsule iterate $(CINEMA_CAPSULE) --steps 1 --goal "$(CINEMA_GOAL)" --cinema --path $(CINEMA_PATH);
}

workflow[name="cinema-open"] {
  trigger: manual;
  step-1: run cmd=url="$$( uv sync --quiet; $(CINEMA_MODEL_ARG) uv run nexu capsule iterate $(CINEMA_CAPSULE) --steps 1 --goal "$(CINEMA_GOAL)" --cinema --path $(CINEMA_PATH) 2>&1 | tee /tmp/nexu-cinema-open.log | sed -n 's/.*Live HTTP Server started for Nexu: //p' | tail -1)"; \;
  step-2: run cmd=if [ -z "$$url" ]; then \;
  step-3: run cmd=echo "Could not detect Nexu URL. See /tmp/nexu-cinema-open.log"; \;
  step-4: run cmd=exit 1; \;
  step-5: run cmd=fi; \;
  step-6: run cmd=echo "Opening $$url"; \;
  step-7: run cmd=( xdg-open "$$url" >/dev/null 2>&1 || sensible-browser "$$url" >/dev/null 2>&1 || firefox "$$url" >/dev/null 2>&1 || google-chrome "$$url" >/dev/null 2>&1 || true );
}

workflow[name="cinema-test"] {
  trigger: manual;
  step-1: run cmd=pytest -q;
}

workflow[name="cinema-stop"] {
  trigger: manual;
  step-1: run cmd=pkill -f '[/]cinema/server.py' >/dev/null 2>&1 || true;
  step-2: run cmd=echo 'Stopped cinema server.py process(es) if any were running.';
}

workflow[name="cinema-restart"] {
  trigger: manual;
  step-1: run cmd=$(MAKE) cinema-stop;
  step-2: run cmd=$(MAKE) cinema;
}

workflow[name="cinema-repair"] {
  trigger: manual;
  step-1: run cmd=uv run python -c "from pathlib import Path; from nexu.cinema_scripts import repair_cinema_html_files; d=Path('$(CINEMA_PATH)')/'.nexu/capsules/$(CINEMA_CAPSULE)/cinema'; n=repair_cinema_html_files(d); print(f'Repaired {n} HTML file(s) in {d}')";
}

workflow[name="ci-cinema-smoke"] {
  trigger: manual;
  step-1: run cmd=./scripts/ci-cinema-smoke.sh;
}

deploy {
  target: docker;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  python_version: >=3.10;
}
```

## Interfaces

### CLI Entry Points

- `nexu`

### testql Scenarios

#### `testql-scenarios/generated-cli-tests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-cli-tests.testql.toon.yaml
# SCENARIO: CLI Command Tests
# TYPE: cli
# GENERATED: true

CONFIG[2]{key, value}:
  cli_command, python -m nexu
  timeout_ms, 10000

# Test 1: CLI help command
SHELL "python -m nexu --help" 5000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "usage"

# Test 2: CLI version command
SHELL "python -m nexu --version" 5000
ASSERT_EXIT_CODE 0

# Test 3: CLI main workflow (dry-run)
SHELL "python -m nexu --help" 10000
ASSERT_EXIT_CODE 0
```

## Workflows

## Quality Pipeline (`pyqual.yaml`)

```yaml markpact:pyqual path=pyqual.yaml
pipeline:
  name: nexu-quality

  stages:
    - name: tests
      run: pytest -q

    - name: docs-links
      run: python scripts/check-doc-links.py .

    - name: intent-contracts
      run: intract check src --format text

    - name: intent-coverage
      run: intract coverage src

    - name: duplication
      run: redup scan src --format toon --min-lines 8

    - name: touched-lint
      run: ruff check src/nexu/cinema.py src/nexu/cinema_server.py src/nexu/cinema_baseline_contracts.py src/nexu/cinema_goal_contracts.py src/nexu/cinema_llm_contracts.py src/nexu/cinema_markpact.py src/nexu/cinema_project_imports.py src/nexu/cinema_projects.py src/nexu/cinema_scripts.py src/nexu/cinema_publish.py src/nexu/cinema_offline_options.py src/nexu/intract.py src/nexu/verify.py src/nexu/intract_adapter.py tests/test_cinema_server.py tests/test_cinema_baseline_contracts.py tests/test_cinema_goal_contracts.py tests/test_cinema_llm_contracts.py tests/test_cinema_markpact.py tests/test_cinema_project_imports.py tests/test_cinema_projects.py tests/test_cinema_scripts.py tests/test_cinema_publish.py tests/test_cinema_offline_options.py

  loop:
    max_iterations: 1
    on_fail: report
```

## Configuration

```yaml
project:
  name: nexu
  version: 0.5.22
  env: local
```

## Dependencies

### Runtime

```text markpact:deps python
pyyaml>=6.0
typer>=0.12.0
rich>=13.0
litellm>=1.0
```

### Development

```text markpact:deps python scope=dev
pytest>=7.0
ruff>=0.4
mypy>=1.8
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

## Deployment

```bash markpact:run
pip install nexu

# development install
pip install -e .[dev]
```

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `*(not set)*` | Required: OpenRouter API key (https://openrouter.ai/keys) |
| `LLM_MODEL` | `openrouter/qwen/qwen3-coder-next` | Model (default: openrouter/qwen/qwen3-coder-next) |
| `PFIX_AUTO_APPLY` | `true` | true = apply fixes without asking |
| `PFIX_AUTO_INSTALL_DEPS` | `true` | true = auto pip/uv install |
| `PFIX_AUTO_RESTART` | `false` | true = os.execv restart after fix |
| `PFIX_MAX_RETRIES` | `3` |  |
| `PFIX_DRY_RUN` | `false` |  |
| `PFIX_ENABLED` | `true` |  |
| `PFIX_GIT_COMMIT` | `false` | true = auto-commit fixes |
| `PFIX_GIT_PREFIX` | `pfix:` | commit message prefix |
| `PFIX_CREATE_BACKUPS` | `false` | false = disable .pfix_backups/ directory |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`nexu`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `venv/lib/python3.13/site-packages/cryptography/__init__.py:__version__`

## Makefile Targets

- `test`
- `examples`
- `docs-links`
- `quality-intract`
- `quality-redup`
- `quality`
- `quality-strict`
- `cinema`
- `cinema-open`
- `cinema-test`
- `cinema-stop`
- `cinema-restart`
- `cinema-repair`
- `ci-cinema-smoke`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# nexu | 122f 23058L | python:118,shell:3,less:1 | 2026-06-01
# stats: 865 func | 21 cls | 122 mod | CC̄=4.8 | critical:91 | cycles:0
# alerts[5]: CC test_render_server_script_embeds_runtime_context=74; CC test_cinema_player_template_is_externalized=68; CC _bind_annotations_to_html=29; CC apply_ui_patch_options=25; CC test_import_http_project_fetches_and_migrates=23
# hotspots[5]: test_projects_import_zip_endpoint fan=33; test_iterate_dashboard_kinds_colors_prefers_offline_before_llm fan=32; test_iterate_colors_scope_uses_offline_path fan=31; test_iterate_colors_scope_uses_llm_patch_when_available fan=30; test_iterate_functions_scope_skips_offline_fast_path fan=29
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[122]:
  app.doql.less,155
  examples/backend_service/app/users.py,9
  examples/frontend_view/src/menu_icons.py,25
  examples/mcp_service/src/demo.py,11
  examples/nexu_markpact_exporter.py,96
  examples/realtime_lane_nexu_sync.py,63
  examples/run_examples.py,80
  examples/scientific_calculator_demo.py,62
  examples/scientific_calculator_demo2.py,87
  examples/vertical_slice/src/flow.py,10
  examples/web_app_calculator/cinema/nexu_hooks.py,281
  examples/web_app_calculator/cinema/server.py,2747
  examples/web_app_calculator/markpact_sandbox/sandbox/src/calculator.py,38
  examples/web_app_calculator/run.py,111
  examples/web_app_calculator/src/calculator.py,39
  examples/web_app_calculator/workspace/src/calculator.py,39
  examples/web_app_dashboard/run.py,119
  examples/web_app_dashboard/src/dashboard.py,11
  examples/web_app_dashboard/workspace/src/dashboard.py,25
  examples/web_app_event_monitor/run.py,91
  examples/web_app_pactown_ecosystem/run.py,98
  project.sh,50
  scripts/check-doc-links.py,115
  scripts/ci-cinema-smoke.sh,86
  src/nexu/__init__.py,6
  src/nexu/__main__.py,5
  src/nexu/blueprint.py,74
  src/nexu/bundle.py,56
  src/nexu/capsule.py,125
  src/nexu/cinema.py,195
  src/nexu/cinema_baseline_contracts.py,174
  src/nexu/cinema_dom_patch.py,203
  src/nexu/cinema_goal_contracts.py,346
  src/nexu/cinema_history.py,245
  src/nexu/cinema_html.py,17
  src/nexu/cinema_html_validate.py,230
  src/nexu/cinema_http_preprocess.py,624
  src/nexu/cinema_iterate.py,67
  src/nexu/cinema_llm.py,333
  src/nexu/cinema_llm_contracts.py,197
  src/nexu/cinema_marked_context.py,503
  src/nexu/cinema_markpact.py,216
  src/nexu/cinema_offline_options.py,898
  src/nexu/cinema_options_cache.py,129
  src/nexu/cinema_policy.py,862
  src/nexu/cinema_project_imports.py,1135
  src/nexu/cinema_project_ir.py,133
  src/nexu/cinema_projects.py,721
  src/nexu/cinema_publish.py,470
  src/nexu/cinema_scope.py,687
  src/nexu/cinema_scripts.py,773
  src/nexu/cinema_server.py,145
  src/nexu/cinema_traces.py,167
  src/nexu/cinema_ui_patch.py,269
  src/nexu/cli.py,380
  src/nexu/config.py,192
  src/nexu/diff.py,36
  src/nexu/drift.py,37
  src/nexu/export_prompt.py,161
  src/nexu/fast_delivery/__init__.py,25
  src/nexu/fast_delivery/context.py,67
  src/nexu/fast_delivery/options.py,129
  src/nexu/fast_delivery/router.py,69
  src/nexu/files.py,52
  src/nexu/freeze.py,27
  src/nexu/git.py,23
  src/nexu/hashing.py,17
  src/nexu/init_project.py,87
  src/nexu/intract.py,141
  src/nexu/intract_adapter.py,134
  src/nexu/iterate.py,45
  src/nexu/journal.py,44
  src/nexu/llm.py,166
  src/nexu/mcp_server.py,394
  src/nexu/models.py,155
  src/nexu/orchestrate.py,233
  src/nexu/paths.py,36
  src/nexu/plan.py,82
  src/nexu/promote.py,93
  src/nexu/report.py,95
  src/nexu/review.py,158
  src/nexu/runtime.py,132
  src/nexu/status.py,36
  src/nexu/verify.py,318
  tests/conftest.py,23
  tests/test_capsule_flow.py,26
  tests/test_capsule_next_stage.py,59
  tests/test_capsule_runtime_report.py,51
  tests/test_cinema_baseline_contracts.py,53
  tests/test_cinema_dom_patch.py,71
  tests/test_cinema_goal_contracts.py,128
  tests/test_cinema_history.py,50
  tests/test_cinema_html_validate.py,106
  tests/test_cinema_http_preprocess.py,279
  tests/test_cinema_iterate.py,89
  tests/test_cinema_llm.py,279
  tests/test_cinema_llm_contracts.py,61
  tests/test_cinema_marked_context.py,210
  tests/test_cinema_markpact.py,45
  tests/test_cinema_offline_options.py,318
  tests/test_cinema_options_cache.py,65
  tests/test_cinema_policy.py,187
  tests/test_cinema_project_imports.py,501
  tests/test_cinema_project_ir.py,23
  tests/test_cinema_projects.py,206
  tests/test_cinema_publish.py,99
  tests/test_cinema_scope.py,263
  tests/test_cinema_scripts.py,45
  tests/test_cinema_server.py,1004
  tests/test_cinema_spatial_patch.py,30
  tests/test_cinema_traces.py,112
  tests/test_cinema_ui_patch.py,157
  tests/test_export_prompt_ledger.py,42
  tests/test_fast_delivery.py,243
  tests/test_intract.py,12
  tests/test_models.py,15
  tests/test_nexu.py,12
  tests/test_orchestration_mcp.py,63
  tests/test_promote_apply.py,37
  tests/test_review_bundle.py,46
  tests/test_verify_intract.py,29
  tree.sh,2
D:
  examples/backend_service/app/users.py:
    e: list_users
    list_users(filters;users)
  examples/frontend_view/src/menu_icons.py:
    e: preview_menu_icons
    preview_menu_icons(menu_items)
  examples/mcp_service/src/demo.py:
    e: plan_demo
    plan_demo(user_goal)
  examples/nexu_markpact_exporter.py:
    e: main
    main()
  examples/realtime_lane_nexu_sync.py:
    e: simulate_realtime_sync
    simulate_realtime_sync()
  examples/run_examples.py:
    e: run_example,main
    run_example(example)
    main()
  examples/scientific_calculator_demo.py:
    e: main
    main()
  examples/scientific_calculator_demo2.py:
    e: print_code,main
    print_code(title;path)
    main()
  examples/vertical_slice/src/flow.py:
    e: run_flow
    run_flow(menu_items)
  examples/web_app_calculator/cinema/nexu_hooks.py:
    e: apply_manifest_from_ledger,verify_capsule,apply_spatial_patch,propose_llm,append_policy_entry,append_goal_policy_entry,goal_contract_lines,validate_artifact,save_history,list_history,restore_history,effective_ui_constraints,sync_option_previews,patch_option_previews,projects_catalog,activate_project,import_project_from_zip,import_project_from_git,import_project_from_http,delete_imported,imported_markpact,imported_llm_log,active_project,export_markpact_readme,services_catalog,publish_service,start_service,stop_service
    apply_manifest_from_ledger()
    verify_capsule()
    apply_spatial_patch(html;delete_ids)
    propose_llm(stage;goal;model)
    append_policy_entry(stage;keep;delete;status;model)
    append_goal_policy_entry(stage;goal)
    goal_contract_lines()
    validate_artifact(artifact;proposals;filename)
    save_history()
    list_history()
    restore_history(checkpoint_id)
    effective_ui_constraints(stage)
    sync_option_previews(stage;delete_ids)
    patch_option_previews(stage;session_keep;session_delete)
    projects_catalog()
    activate_project(project_id)
    import_project_from_zip(filename;content_base64)
    import_project_from_git(git_url;branch)
    import_project_from_http(site_url)
    delete_imported(project_id)
    imported_markpact(project_id)
    imported_llm_log(project_id)
    active_project()
    export_markpact_readme(stage;user_goal)
    services_catalog()
    publish_service()
    start_service(service_id)
    stop_service(service_id)
  examples/web_app_calculator/cinema/server.py:
    e: _load_cinema_ui_profile,_goal_entry_kwargs,_llm_prompt_intro,_llm_prompt_rules,_llm_communication_contract_block,_load_env_file,_load_all_env,_resolve_model,_llm_network_allowed,_litellm_available,_llm_status_payload,_trace_slug,_read_trace_index,_write_llm_trace,_list_llm_traces,_path_segments,_parse_imported_project_route,_delete_imported_project,_imported_markpact,_imported_llm_log,_read_llm_trace,_ensure_api_key_env,_strip_markdown_fences,_extract_html_document,_compact_html_for_llm,_effective_markpact_mode,_compact_markpact_for_llm,_try_read_options_cache,_store_options_cache,_extract_llm_content,_compact_llm_error,_load_policy_payload,_effective_ui_constraints_from_ledger,_merge_ui_constraints,_ensure_intract_on_path,_propose_cinema_contracts,_proposal_kind_and_element,_proposal_delta_text,_normalize_proposals_for_ledger,_append_policy_entry_legacy,_nexu_hooks_apply,_nexu_hooks_verify,_propose_llm_for_stage,_validate_intract_artifact,_append_policy_entry,_save_history_checkpoint,_list_history,_restore_history,_sync_option_previews,_patch_option_previews,_projects_catalog,_active_project,_activate_project,_import_project,_import_project_zip,_import_project_git,_import_project_http,_parse_multipart_zip,_export_markpact_markdown,_services_catalog,_publish_service,_start_service,_stop_service,CustomHTTPRequestHandler,ThreadingHTTPServer
    CustomHTTPRequestHandler: __init__(0),do_GET(0),do_POST(0),do_DELETE(0),do_OPTIONS(0)
    ThreadingHTTPServer:
    _load_cinema_ui_profile()
    _goal_entry_kwargs(data)
    _llm_prompt_intro(profile)
    _llm_prompt_rules(profile)
    _llm_communication_contract_block()
    _load_env_file(path;override_keys)
    _load_all_env()
    _resolve_model()
    _llm_network_allowed()
    _litellm_available()
    _llm_status_payload()
    _trace_slug(value)
    _read_trace_index()
    _write_llm_trace()
    _list_llm_traces(project_id)
    _path_segments(path)
    _parse_imported_project_route(path)
    _delete_imported_project(project_id)
    _imported_markpact(project_id)
    _imported_llm_log(project_id)
    _read_llm_trace(trace_id)
    _ensure_api_key_env()
    _strip_markdown_fences(text)
    _extract_html_document(text)
    _compact_html_for_llm(html)
    _effective_markpact_mode(focus_scope;project_kind)
    _compact_markpact_for_llm(markdown)
    _try_read_options_cache()
    _store_options_cache()
    _extract_llm_content(response)
    _compact_llm_error(err_text)
    _load_policy_payload()
    _effective_ui_constraints_from_ledger(ledger;stage)
    _merge_ui_constraints(ledger_keep;ledger_delete;session_keep;session_delete)
    _ensure_intract_on_path()
    _propose_cinema_contracts(stage;keep_els;delete_els)
    _proposal_kind_and_element(proposal)
    _proposal_delta_text(stage;proposal)
    _normalize_proposals_for_ledger(stage;proposals)
    _append_policy_entry_legacy(stage;keep_els;delete_els;status;model)
    _nexu_hooks_apply()
    _nexu_hooks_verify()
    _propose_llm_for_stage(stage;goal)
    _validate_intract_artifact(artifact;proposals;filename)
    _append_policy_entry(stage;keep_els;delete_els;status;model)
    _save_history_checkpoint()
    _list_history()
    _restore_history(checkpoint_id)
    _sync_option_previews(stage;delete_els)
    _patch_option_previews(stage;session_keep;session_delete)
    _projects_catalog()
    _active_project()
    _activate_project(project_id)
    _import_project(data)
    _import_project_zip(content;filename)
    _import_project_git(data)
    _import_project_http(data)
    _parse_multipart_zip(post_data;content_type)
    _export_markpact_markdown()
    _services_catalog()
    _publish_service()
    _start_service(service_id)
    _stop_service(service_id)
  examples/web_app_calculator/markpact_sandbox/sandbox/src/calculator.py:
    e: render_calculator
    render_calculator(calculator_state)
  examples/web_app_calculator/run.py:
    e: main
    main()
  examples/web_app_calculator/src/calculator.py:
    e: render_calculator
    render_calculator(calculator_state)
  examples/web_app_calculator/workspace/src/calculator.py:
    e: render_calculator
    render_calculator(calculator_state)
  examples/web_app_dashboard/run.py:
    e: main
    main()
  examples/web_app_dashboard/src/dashboard.py:
    e: render_dashboard
    render_dashboard(telemetry_data)
  examples/web_app_dashboard/workspace/src/dashboard.py:
    e: render_dashboard
    render_dashboard(telemetry_data)
  examples/web_app_event_monitor/run.py:
    e: main
    main()
  examples/web_app_pactown_ecosystem/run.py:
    e: main
    main()
  scripts/check-doc-links.py:
    e: _is_external,_slug,_anchors,_markdown_files,_targets,_resolve,check_links,main
    _is_external(target)
    _slug(text)
    _anchors(path)
    _markdown_files(root)
    _targets(text)
    _resolve(base;target)
    check_links(root)
    main()
  src/nexu/__init__.py:
  src/nexu/__main__.py:
  src/nexu/blueprint.py:
    e: build_blueprint
    build_blueprint(root;name)
  src/nexu/bundle.py:
    e: _should_include,build_capsule_bundle
    _should_include(path;base)
    build_capsule_bundle(root;name)
  src/nexu/capsule.py:
    e: default_contract_manifest,create_capsule,list_capsules,load_capsule,save_capsule
    default_contract_manifest(capsule)
    create_capsule(root;name)
    list_capsules(root)
    load_capsule(root;name)
    save_capsule(root;capsule)
  src/nexu/cinema.py:
    e: _cinema_template_text,_render_cinema_template,write_cinema_nexu_hooks,_contract_to_public_dict,build_intract_policy_snapshot,sync_cinema_templates,write_intract_policy_files,generate_cinema_player,_start_cinema_server
    _cinema_template_text(name)
    _render_cinema_template(name)
    write_cinema_nexu_hooks(cinema_dir;root;name)
    _contract_to_public_dict(contract)
    build_intract_policy_snapshot(root;name)
    sync_cinema_templates(cinema_dir;root;name)
    write_intract_policy_files(cinema_dir;root;name)
    generate_cinema_player(root;name)
    _start_cinema_server(cinema_dir;root;name)
  src/nexu/cinema_baseline_contracts.py:
    e: _contract,calculator_baseline_contracts,is_calculator_capsule,merge_calculator_baselines,ensure_capsule_intract_yaml
    _contract(contract_id;intent;meaning)
    calculator_baseline_contracts()
    is_calculator_capsule(root;name)
    merge_calculator_baselines(capsule_contracts;root;name)
    ensure_capsule_intract_yaml(root;name)
  src/nexu/cinema_dom_patch.py:
    e: supports_function_patch,build_function_patch_context,_strip_existing_patch,_goal_label,_variant_section,_patch_style,_inject_into_head,_inject_into_body,build_function_option_patches
    supports_function_patch(scope;project_kind)
    build_function_patch_context(html_text)
    _strip_existing_patch(text)
    _goal_label(user_goal)
    _variant_section(variant;user_goal;ir)
    _patch_style()
    _inject_into_head(text;style)
    _inject_into_body(text;section)
    build_function_option_patches(html_text)
  src/nexu/cinema_goal_contracts.py:
    e: _hints_text,is_chemical_goal,_slug,_goal_contract_dict,_resolve_baseline_anchor,_build_detail_text,_detect_chemical_trait,_detect_minimal_trait,_detect_expanded_trait,_detect_api_trait,_detect_dashboard_trait,_detect_engineering_trait,_collect_trait_proposals,propose_goal_extension_contracts,goal_traits_from_contract_lines
    _hints_text(hints)
    is_chemical_goal(hints)
    _slug(text)
    _goal_contract_dict(contract_id;intent;meaning)
    _resolve_baseline_anchor(kind;template_base)
    _build_detail_text(scope_display;context;current;expected)
    _detect_chemical_trait(text;capsule_name;stage)
    _detect_minimal_trait(text;kind;capsule_name;stage)
    _detect_expanded_trait(text;kind;capsule_name;stage)
    _detect_api_trait(lower;capsule_name;stage;template_base)
    _detect_dashboard_trait(lower;capsule_name;stage;template_base)
    _detect_engineering_trait(lower;kind;capsule_name;stage;template_base)
    _collect_trait_proposals(text;lower;kind;capsule_name;stage;template_base)
    propose_goal_extension_contracts(goal)
    goal_traits_from_contract_lines(lines)
  src/nexu/cinema_history.py:
    e: history_dir,history_index_path,_load_index,_write_index,_copy_checkpoint_files,_ledger_snapshot,_build_label,save_history_checkpoint,list_history_checkpoints,restore_history_checkpoint,_refresh_policy_snapshot,ensure_initial_checkpoint,ledger_archive_for_display
    history_dir(cinema_dir)
    history_index_path(cinema_dir)
    _load_index(cinema_dir)
    _write_index(cinema_dir;entries)
    _copy_checkpoint_files(cinema_dir;dest)
    _ledger_snapshot(cinema_dir)
    _build_label()
    save_history_checkpoint(cinema_dir)
    list_history_checkpoints(cinema_dir)
    restore_history_checkpoint(root;capsule_name;checkpoint_id)
    _refresh_policy_snapshot(cinema_dir;root;capsule_name)
    ensure_initial_checkpoint(cinema_dir)
    ledger_archive_for_display(cinema_dir)
  src/nexu/cinema_html.py:
    e: ensure_html_document_closure
    ensure_html_document_closure(html)
  src/nexu/cinema_html_validate.py:
    e: _strip_css_comments,_selector_is_runtime_only,validate_css_safety,_looks_like_html_document,_has_open_tag,_has_close_tag,relocate_style_tags_to_head,repair_html_structure,_validate_basic_tags,_validate_calculator_elements,validate_cinema_html_document,prepare_cinema_html_document,filter_valid_option_batch
    _strip_css_comments(css)
    _selector_is_runtime_only(selector)
    validate_css_safety(css)
    _looks_like_html_document(text)
    _has_open_tag(html;tag)
    _has_close_tag(html;tag)
    relocate_style_tags_to_head(html)
    repair_html_structure(html)
    _validate_basic_tags(text;errors)
    _validate_calculator_elements(text;errors)
    validate_cinema_html_document(html)
    prepare_cinema_html_document(html)
    filter_valid_option_batch(batch)
  src/nexu/cinema_http_preprocess.py:
    e: _safe_read_under,_extract_inline_css,_extract_stylesheet_hrefs,_normalize_linked_paths,_split_css_rules,_rule_is_visual,_filter_visual_css,extract_visual_css,_script_src_allowed_for_preview,_should_remove_preview_script,sanitize_http_preview_html,inject_http_preview_shim,prepare_http_preview_html,build_html_outline,_write_preprocess_artifacts,preprocess_cinema_seed,http_preprocess_artifacts_present,ensure_http_preprocess_artifacts,preprocess_http_import,_project_meta_path,load_cinema_seed_preprocess_artifacts,_load_project_meta,load_http_preprocess_artifacts,build_http_llm_context,http_patch_llm_rules,_OutlineParser
    _OutlineParser: __init__(0),_keep_attr(1),handle_starttag(2),handle_endtag(1),handle_data(1)
    _safe_read_under(base_dir;rel_path)
    _extract_inline_css(html)
    _extract_stylesheet_hrefs(html)
    _normalize_linked_paths(linked_css_paths;html)
    _split_css_rules(css)
    _rule_is_visual(rule)
    _filter_visual_css(css)
    extract_visual_css(html;linked_css_paths;source_dir)
    _script_src_allowed_for_preview(src)
    _should_remove_preview_script(tag)
    sanitize_http_preview_html(html)
    inject_http_preview_shim(html)
    prepare_http_preview_html(html)
    build_html_outline(html)
    _write_preprocess_artifacts(html)
    preprocess_cinema_seed(cinema_dir)
    http_preprocess_artifacts_present(source_dir;meta)
    ensure_http_preprocess_artifacts(source_dir)
    preprocess_http_import(source_dir)
    _project_meta_path(cinema_dir;project_id)
    load_cinema_seed_preprocess_artifacts(cinema_dir;active)
    _load_project_meta(meta_path)
    load_http_preprocess_artifacts(cinema_dir;active)
    build_http_llm_context(artifacts)
    http_patch_llm_rules()
  src/nexu/cinema_iterate.py:
    e: build_iterate_response_payload
    build_iterate_response_payload()
  src/nexu/cinema_llm.py:
    e: _cached_config,_litellm_completion,_strip_markdown_fences,_strip_rich_console_artifacts,has_terminal_artifacts,looks_like_html_document,normalize_html_document,extract_html_document,parse_batch_alt_options,_as_plain_data,_lookup,_response_shape,_extract_parts,_extract_content,compact_llm_error,_compact_response_preview,call_cinema_text_llm,call_cinema_html_llm
    _cached_config(root)
    _litellm_completion()
    _strip_markdown_fences(text)
    _strip_rich_console_artifacts(text)
    has_terminal_artifacts(text)
    looks_like_html_document(text)
    normalize_html_document(text)
    extract_html_document(text)
    parse_batch_alt_options(text)
    _as_plain_data(value)
    _lookup(obj;key;default)
    _response_shape(response)
    _extract_parts(content)
    _extract_content(response)
    compact_llm_error(err_text)
    _compact_response_preview(text)
    call_cinema_text_llm(prompt;root)
    call_cinema_html_llm(prompt;root)
  src/nexu/cinema_llm_contracts.py:
    e: _slug,_line,_compact,build_llm_option_variants,_format_contract_params,build_llm_communication_contract_lines,build_llm_contract_block
    _slug(value)
    _line(contract_id;intent;meaning)
    _compact(value)
    build_llm_option_variants()
    _format_contract_params(keep_els;delete_els;project_goal;current_state;expected_version;element_hints)
    build_llm_communication_contract_lines()
    build_llm_contract_block()
  src/nexu/cinema_marked_context.py:
    e: has_ui_marks,_css_id_selector,marked_css_selectors,resolve_marked_selectors,marked_scope_colors_css,restrict_scope_css_to_marks,_id_candidates,_parse_attrs,_logical_id,_extract_balanced_html,_collect_match_candidates,_collect_button_candidates,_extract_and_format_fragment,_find_marked_subtrees,_selector_tokens,_filter_css_for_tokens,_collect_css_sources,_scope_semantics,_cap_text,_client_fragment_html,_assemble_marked_subtrees,_get_relevant_css,_format_context_body,build_marked_element_context,resolve_marked_llm_context
    has_ui_marks(keep_els;delete_els)
    _css_id_selector(token)
    marked_css_selectors(element_ids)
    resolve_marked_selectors(html;element_ids)
    marked_scope_colors_css(selectors;variant)
    restrict_scope_css_to_marks(css;delete_ids)
    _id_candidates(element_id)
    _parse_attrs(attr_text)
    _logical_id(tag;attrs)
    _extract_balanced_html(html;start)
    _collect_match_candidates(tag;attrs)
    _collect_button_candidates(tag;attrs;match;raw_html)
    _extract_and_format_fragment(text;start)
    _find_marked_subtrees(html;marked_ids)
    _selector_tokens(subtrees)
    _filter_css_for_tokens(css;tokens)
    _collect_css_sources(html;ui_profile)
    _scope_semantics(scope)
    _cap_text(text;limit)
    _client_fragment_html(client_fragments;element_id)
    _assemble_marked_subtrees(html;marked_ids;client_fragments)
    _get_relevant_css(html;subtrees;ui_profile)
    _format_context_body(keep;delete;marked_ids;subtrees;css;scope;ui_profile)
    build_marked_element_context(html)
    resolve_marked_llm_context(html)
  src/nexu/cinema_markpact.py:
    e: _escape_markdown_fence,_language_for,_project_context_block,_get_app_title,_get_baseline_block,build_markpact_readme,markpact_download_filename
    _escape_markdown_fence(text;fence)
    _language_for(path)
    _project_context_block(workspace_root)
    _get_app_title(html;capsule_name;stage)
    _get_baseline_block(project_contracts;capsule_contracts)
    build_markpact_readme(cinema_dir)
    markpact_download_filename(capsule_name;stage)
  src/nexu/cinema_offline_options.py:
    e: _btn,_keep_ids_lower,_normal_id,_delete_without_keeps,_mandatory_trig,_trig_row,_policy_constrained,_numpad_token_btn,_numpad_rows,_numpad_from_policy,_short_goal_label,_policy_screen_text,_expanded_excess_row,_chemical_shell,_active_project_meta,_active_is_imported,_cinema_is_calculator,_project_option_label,_inject_goal_banner,_write_project_options_from_stages,_write_scoped_calculator_options,_option_shell,build_policy_scientific_option_html,build_chemical_option_html,_render_packaged_alt,_is_dashboard_kind,_detect_project_types,_get_option_mapping,_generate_option_html,_write_option_files,_sync_stages_from_options,write_goal_options_offline
    _btn(label;el_id)
    _keep_ids_lower(keep_els)
    _normal_id(value)
    _delete_without_keeps(delete_els;keep_els)
    _mandatory_trig(keep_els)
    _trig_row(keep_els)
    _policy_constrained(keep_els;delete_els)
    _numpad_token_btn(token)
    _numpad_rows(cols)
    _numpad_from_policy(keep_els)
    _short_goal_label(goal)
    _policy_screen_text(variant;keep_els)
    _expanded_excess_row(keep_els)
    _chemical_shell()
    _active_project_meta(cinema_dir)
    _active_is_imported(cinema_dir)
    _cinema_is_calculator(cinema_dir)
    _project_option_label(meta;variant)
    _inject_goal_banner(html;goal;variant)
    _write_project_options_from_stages(cinema_dir)
    _write_scoped_calculator_options(cinema_dir)
    _option_shell()
    build_policy_scientific_option_html(variant;keep_els)
    build_chemical_option_html(variant;keep_els)
    _render_packaged_alt(name)
    _is_dashboard_kind(active_kind;use_calculator;use_chemical;traits)
    _detect_project_types(cinema_dir;keep;delete;goal_text;hint_list;traits)
    _get_option_mapping(use_chemical;use_scientific)
    _generate_option_html(variant;keep;goal_text;use_chemical;use_scientific)
    _write_option_files(cinema_dir;mapping;keep;delete;goal_text;use_chemical;use_scientific)
    _sync_stages_from_options(cinema_dir;labels)
    write_goal_options_offline(cinema_dir)
  src/nexu/cinema_options_cache.py:
    e: goal_slug,_digest,options_cache_key,options_cache_dir,read_options_cache,write_options_cache,apply_options_cache,invalidate_options_cache
    goal_slug(goal)
    _digest(value)
    options_cache_key()
    options_cache_dir(cinema_dir)
    read_options_cache(cache_root;key)
    write_options_cache(cache_root;key)
    apply_options_cache(cinema_dir;cached)
    invalidate_options_cache(cache_root)
  src/nexu/cinema_policy.py:
    e: _process_ledger_entry,_process_keep_delete_entries,_process_proposed_contracts,_build_constraint_result,effective_ui_constraints_from_ledger,merge_ui_constraint_lists,_normalize_html_body,_html_files_distinct,option_previews_are_distinct,stage_files_are_distinct,ensure_option_previews_from_stages,ensure_http_option_previews_from_stage0,refresh_imported_policy_snapshot,_replace_html_title,sync_option_previews_from_workspace,enforce_deletes_on_option_previews,reset_cinema_policy_ledger,refresh_cinema_policy_snapshot,load_effective_ui_constraints,resolve_iteration_mode,normalize_manifest_target,cinema_model_label,cinema_dir_for,policy_snapshot_path,policy_ledger_path,load_policy_snapshot,manifest_paths_from_snapshot,apply_ledger_from_cinema,ensure_intract_on_path,propose_ui_delta_contract_dicts,_resolve_ledger_path,append_policy_ledger_entry,_proposal_kind_and_element,normalize_proposals_for_ledger,append_goal_ledger_entry,load_goal_contract_lines,append_iteration_ledger_entry,propose_llm_for_stage,validate_intract_artifact,verify_capsule_workspace
    _process_ledger_entry(entry;state;stage)
    _process_keep_delete_entries(entry;state)
    _process_proposed_contracts(entry;state)
    _build_constraint_result(state)
    effective_ui_constraints_from_ledger(ledger)
    merge_ui_constraint_lists()
    _normalize_html_body(html)
    _html_files_distinct(cinema_dir;names)
    option_previews_are_distinct(cinema_dir)
    stage_files_are_distinct(cinema_dir)
    ensure_option_previews_from_stages(cinema_dir)
    ensure_http_option_previews_from_stage0(cinema_dir)
    refresh_imported_policy_snapshot(cinema_dir;meta;active)
    _replace_html_title(html;title)
    sync_option_previews_from_workspace(cinema_dir)
    enforce_deletes_on_option_previews(cinema_dir;delete_ids)
    reset_cinema_policy_ledger(cinema_dir)
    refresh_cinema_policy_snapshot(cinema_dir;root;capsule_name)
    load_effective_ui_constraints(root;capsule_name)
    resolve_iteration_mode()
    normalize_manifest_target(target)
    cinema_model_label(root)
    cinema_dir_for(root;capsule_name)
    policy_snapshot_path(root;capsule_name)
    policy_ledger_path(root;capsule_name)
    load_policy_snapshot(root;capsule_name)
    manifest_paths_from_snapshot(snapshot;root;capsule_name;target)
    apply_ledger_from_cinema(root;capsule_name)
    ensure_intract_on_path(root)
    propose_ui_delta_contract_dicts()
    _resolve_ledger_path(root;capsule_name)
    append_policy_ledger_entry(root;capsule_name;entry)
    _proposal_kind_and_element(proposal)
    normalize_proposals_for_ledger(stage;capsule_name;proposals)
    append_goal_ledger_entry(root;capsule_name)
    load_goal_contract_lines(root;capsule_name)
    append_iteration_ledger_entry(root;capsule_name)
    propose_llm_for_stage(root;capsule_name;stage;goal)
    validate_intract_artifact(artifact;proposals)
    verify_capsule_workspace(root;capsule_name)
  src/nexu/cinema_project_imports.py:
    e: _slug,_imports_root,_project_dir,_validate_http_url,_validate_git_url,_safe_extract_zip,_charset_from_content_type,_decode_http_bytes,_document_base_href,_fetch_http_body,_same_origin,_extract_stylesheet_hrefs,_fetch_http_stylesheets,_rewrite_local_stylesheets,_inject_base_href,_find_http_index_path,_load_http_fetch_meta,_build_http_preview_stage0,_iter_project_files,_detect_run_notes,_read_text_for_markpact,_build_markpact_migration,_stage_html,_apply_http_preprocess_fields,_refresh_http_preprocess_if_needed,_activate_imported,import_git_project,import_http_project,import_zip_project,_import_kind_from_id,_project_title_from_id,_finish_import,_infer_workspace_context,_source_stats,_source_url_from_meta,normalize_imported_project_id,is_deletable_imported_id,_compile_meta_fields,_ensure_project_meta_fields,_catalog_entry_from_meta,_filter_traces_for_project,read_imported_markpact,imported_project_llm_log,_verify_delete_paths,_activate_delete_fallback,_clear_active_project,_delete_active_project_fallback,delete_imported_project,delete_project,list_imported_projects,merged_projects_catalog,activate_imported_project
    _slug(value)
    _imports_root(cinema_dir)
    _project_dir(cinema_dir;project_id)
    _validate_http_url(url)
    _validate_git_url(url)
    _safe_extract_zip(zip_path;target)
    _charset_from_content_type(content_type)
    _decode_http_bytes(body)
    _document_base_href(url)
    _fetch_http_body(url)
    _same_origin(url;base_url)
    _extract_stylesheet_hrefs(html)
    _fetch_http_stylesheets(html)
    _rewrite_local_stylesheets(html)
    _inject_base_href(html;base_href)
    _find_http_index_path(source_dir)
    _load_http_fetch_meta(source_dir)
    _build_http_preview_stage0(meta)
    _iter_project_files(root)
    _detect_run_notes(root)
    _read_text_for_markpact(path)
    _build_markpact_migration(root)
    _stage_html(meta)
    _apply_http_preprocess_fields(meta;preprocess_fields)
    _refresh_http_preprocess_if_needed(cinema_dir;meta)
    _activate_imported(cinema_dir;meta)
    import_git_project(cinema_dir;git_url)
    import_http_project(cinema_dir;site_url)
    import_zip_project(cinema_dir;filename;content_base64)
    _import_kind_from_id(project_id)
    _project_title_from_id(project_id)
    _finish_import(cinema_dir)
    _infer_workspace_context(cinema_dir)
    _source_stats(source_dir)
    _source_url_from_meta(meta)
    normalize_imported_project_id(project_id)
    is_deletable_imported_id(project_id)
    _compile_meta_fields(cinema_dir;meta)
    _ensure_project_meta_fields(cinema_dir;meta)
    _catalog_entry_from_meta(meta;cinema_dir)
    _filter_traces_for_project(traces)
    read_imported_markpact(cinema_dir;project_id)
    imported_project_llm_log(cinema_dir;project_id;trace_dir)
    _verify_delete_paths(project_dir;imports_root)
    _activate_delete_fallback(cinema_dir;fallback;workspace_root;capsule_name;repo_root)
    _clear_active_project(cinema_dir)
    _delete_active_project_fallback(cinema_dir;result;workspace_root;capsule_name;repo_root)
    delete_imported_project(cinema_dir;project_id)
    delete_project(cinema_dir;project_id)
    list_imported_projects(cinema_dir)
    merged_projects_catalog(cinema_dir)
    activate_imported_project(cinema_dir;project_id)
  src/nexu/cinema_project_ir.py:
    e: _clean_text,build_project_ir,summarize_project_ir,_ProjectIRParser
    _ProjectIRParser: __init__(0),handle_starttag(2),_classify_node(4),handle_endtag(1),handle_data(1)
    _clean_text(text)
    build_project_ir(html)
    summarize_project_ir(ir)
  src/nexu/cinema_projects.py:
    e: find_nexu_repo_root,deleted_project_ids,mark_project_deleted,is_example_project_id,_project_catalog_entry,_catalog_filters,list_project_catalog,delete_example_project,_resolve_source_cinema,_project_widgets,_seed_html_for_project,_copy_cinema_files,_write_seed_variants,_find_example_project,_active_project_meta,_write_active_project_meta,_resolve_root_for_project_source,_copy_or_seed_project_files,_sync_project_options,_apply_preprocess_meta,_bootstrap_goal_from_project,_init_project_activation,activate_example_project,load_active_project,ExampleProject
    ExampleProject: to_public_dict(0)
    find_nexu_repo_root(start)
    deleted_project_ids(cinema_dir)
    mark_project_deleted(cinema_dir;project_id)
    is_example_project_id(project_id)
    _project_catalog_entry(project;cinema_dir)
    _catalog_filters(projects)
    list_project_catalog(cinema_dir)
    delete_example_project(cinema_dir;project_id)
    _resolve_source_cinema(project;repo_root)
    _project_widgets(project)
    _seed_html_for_project(project;variant)
    _copy_cinema_files(source;cinema_dir)
    _write_seed_variants(cinema_dir;project)
    _find_example_project(project_id)
    _active_project_meta(project)
    _write_active_project_meta(cinema_dir;meta)
    _resolve_root_for_project_source(cinema_dir;repo_root;workspace_root)
    _copy_or_seed_project_files(cinema_dir;project;source)
    _sync_project_options(cinema_dir;project)
    _apply_preprocess_meta(cinema_dir;meta;source)
    _bootstrap_goal_from_project(cinema_dir;project;workspace_root;capsule_name)
    _init_project_activation(cinema_dir;project;workspace_root;capsule_name)
    activate_example_project(cinema_dir;project_id)
    load_active_project(cinema_dir)
  src/nexu/cinema_publish.py:
    e: services_root,_registry_path,_load_registry,_save_registry,_slug_service_id,_pick_port,_port_open,_http_ok,_service_alive,_refresh_service_status,list_published_services,_write_service_readme,_prepare_service_directory,_generate_markpact_export,_allocate_service_port,_create_service_entry,_register_service,_handle_existing_service,publish_project_service,_spawn_http_server,_wait_for_service_running,start_published_service,stop_published_service
    services_root(cinema_dir)
    _registry_path(cinema_dir)
    _load_registry(cinema_dir)
    _save_registry(cinema_dir;data)
    _slug_service_id(project_id;capsule_name;stage)
    _pick_port(used)
    _port_open(port)
    _http_ok(url)
    _service_alive(entry)
    _refresh_service_status(entry)
    list_published_services(cinema_dir)
    _write_service_readme(service_dir)
    _prepare_service_directory(cinema_dir;stage_file;service_id)
    _generate_markpact_export(service_dir;cinema_dir;root;capsule_name;stage;user_goal)
    _allocate_service_port(cinema_dir;service_id)
    _create_service_entry(service_id;capsule_name;project_id;project_title;stage;port)
    _register_service(cinema_dir;service_entry)
    _handle_existing_service(cinema_dir;service_id)
    publish_project_service(cinema_dir;root;capsule_name)
    _spawn_http_server(service_dir;port)
    _wait_for_service_running(entry;deadline)
    start_published_service(cinema_dir;service_id)
    stop_published_service(cinema_dir;service_id)
  src/nexu/cinema_scope.py:
    e: ui_type_for_kind,allowed_scope_ids,default_scope_for_kind,normalize_focus_scope,offline_fast_scopes_for_kind,scope_supports_offline_fast_path,cinema_has_offline_baseline,scope_option_variants,strip_scope_style,_scope_css,_calc_scope_css,_web_scope_css,_resolve_scope_kind,should_block_full_html_iterate,_bind_annotations_to_html,_get_scope_css,_inject_css_block,inject_scope_style,scoped_html_fragment,scope_meta_for_project,load_cinema_ui_profile,can_use_offline_fast_iterate
    ui_type_for_kind(kind)
    allowed_scope_ids(project_kind)
    default_scope_for_kind(project_kind)
    normalize_focus_scope(scope;project_kind)
    offline_fast_scopes_for_kind(project_kind)
    scope_supports_offline_fast_path(scope;project_kind)
    cinema_has_offline_baseline(cinema_dir)
    scope_option_variants(scope;ui_type;focus_text)
    strip_scope_style(html)
    _scope_css(scope;variant)
    _calc_scope_css(scope;variant)
    _web_scope_css(scope;variant)
    _resolve_scope_kind(project_kind;html)
    should_block_full_html_iterate(project_kind;keep_els;delete_els)
    _bind_annotations_to_html(html;keep_ids;delete_ids)
    _get_scope_css(inferred;html;scope;variant)
    _inject_css_block(html;css)
    inject_scope_style(html;scope;variant)
    scoped_html_fragment(html;focus_scope;project_kind)
    scope_meta_for_project(project_kind)
    load_cinema_ui_profile(active;cinema_dir)
    can_use_offline_fast_iterate(focus_scope;project_kind;cinema_dir)
  src/nexu/cinema_scripts.py:
    e: _delete_match_keys,_selectable_block_attrs,_element_delete_candidates,apply_spatial_deletes_to_html,inject_cinema_shield,finalize_cinema_html,write_cinema_inject_files,repair_cinema_html_files
    _delete_match_keys(element_id)
    _selectable_block_attrs(attrs)
    _element_delete_candidates(attrs;inner_text)
    apply_spatial_deletes_to_html(html;delete_ids)
    inject_cinema_shield(html)
    finalize_cinema_html(html)
    write_cinema_inject_files(cinema_dir)
    repair_cinema_html_files(cinema_dir)
  src/nexu/cinema_server.py:
    e: _template_text,_render_server_script,_litellm_available,_try_spawn_on_port,_available_port,start_persistent_http_server,_open_browser,start_cinema_player_server
    _template_text()
    _render_server_script(root;name;llm_config;cinema_config;python_executable)
    _litellm_available(python_executable)
    _try_spawn_on_port(directory;port;python_executable)
    _available_port(directory;python_executable)
    start_persistent_http_server(directory;root;name)
    _open_browser(url)
    start_cinema_player_server(cinema_dir;root;name)
  src/nexu/cinema_traces.py:
    e: redact_secrets,trace_slug,text_metrics,read_trace_index,write_llm_trace,list_llm_traces,read_llm_trace
    redact_secrets(text)
    trace_slug(value)
    text_metrics(text)
    read_trace_index(index_path)
    write_llm_trace(trace_dir;index_path;lock)
    list_llm_traces(trace_dir)
    read_llm_trace(trace_dir;trace_id)
  src/nexu/cinema_ui_patch.py:
    e: supports_llm_patch_scope,_compact_html,_patch_scope_rules,build_ui_patch_prompt,_strip_json_fence,parse_ui_patch_response,_safe_css,_label_for,_css_for,apply_ui_patch_options
    supports_llm_patch_scope(scope;project_kind)
    _compact_html(html)
    _patch_scope_rules(scope)
    build_ui_patch_prompt(html)
    _strip_json_fence(text)
    parse_ui_patch_response(text)
    _safe_css(css)
    _label_for(filename;item;fallback)
    _css_for(item)
    apply_ui_patch_options(html;patch)
  src/nexu/cli.py:
    e: _print_yaml,_relative_to_root,init,freeze,capsule_create,capsule_list,capsule_status_command,capsule_iterate,capsule_blueprint,capsule_export_prompt,capsule_diff,capsule_drift,capsule_verify,capsule_plan,capsule_runtime,capsule_report,capsule_journal,capsule_orchestrate,capsule_review,capsule_bundle,capsule_promote,mcp_tools,mcp_serve
    _print_yaml(data)
    _relative_to_root(root;path)
    init(path)
    freeze(path;name;include)
    capsule_create(path;name;domain;include;route;endpoint;snapshot)
    capsule_list(path)
    capsule_status_command(name;path)
    capsule_iterate(name;path;steps;goal;cinema)
    capsule_blueprint(name;path;print_yaml)
    capsule_export_prompt(name;path;iteration)
    capsule_diff(name;path)
    capsule_drift(name;path)
    capsule_verify(name;path)
    capsule_plan(name;path;steps;goal;print_yaml)
    capsule_runtime(name;path)
    capsule_report(name;path)
    capsule_journal(name;path;limit)
    capsule_orchestrate(name;path;steps;goal;call_llm;model)
    capsule_review(name;path;iteration;call_llm;model)
    capsule_bundle(name;path;include_src)
    capsule_promote(name;path;dry_run)
    mcp_tools()
    mcp_serve(path;transport)
  src/nexu/config.py:
    e: _as_list,_load_env_file,load_env_files,_resolved_model_from_env,_cinema_mode,load_config,LLMConfig,ReviewConfig,CinemaConfig,nexuConfig
    LLMConfig:
    ReviewConfig:
    CinemaConfig:  # Cinema live iteration tuning (also overridable via CINEMA_* 
    nexuConfig:
    _as_list(value;default)
    _load_env_file(path)
    load_env_files(root)
    _resolved_model_from_env(yaml_model)
    _cinema_mode(value;default)
    load_config(root)
  src/nexu/diff.py:
    e: diff_capsule
    diff_capsule(root;name)
  src/nexu/drift.py:
    e: check_source_drift
    check_source_drift(root;name)
  src/nexu/export_prompt.py:
    e: _cinema_policy_ledger_block,_latest_iteration,export_iteration_prompt
    _cinema_policy_ledger_block(base)
    _latest_iteration(capsule)
    export_iteration_prompt(root;name)
  src/nexu/fast_delivery/__init__.py:
  src/nexu/fast_delivery/context.py:
    e: compact_html_for_llm,effective_markpact_mode,compact_markpact_for_llm
    compact_html_for_llm(html)
    effective_markpact_mode(focus_scope;project_kind)
    compact_markpact_for_llm(markdown)
  src/nexu/fast_delivery/options.py:
    e: _looks_like_calculator,_compatible_with_stage,read_cached_options,store_options_cache,read_option_files
    _looks_like_calculator(html)
    _compatible_with_stage(stage_html;files)
    read_cached_options()
    store_options_cache()
    read_option_files(cinema_dir)
  src/nexu/fast_delivery/router.py:
    e: choose_options_route,is_options_ready_status,options_source_label,DeliveryRoute
    DeliveryRoute:  # Selected route for one improvement-loop step.
    choose_options_route()
    is_options_ready_status(status)
    options_source_label(status)
  src/nexu/files.py:
    e: rel,matches_any,is_text_file,collect_files
    rel(path;root)
    matches_any(value;patterns)
    is_text_file(path)
    collect_files(root;include;exclude)
  src/nexu/freeze.py:
    e: freeze_project
    freeze_project(root;name;include)
  src/nexu/git.py:
    e: current_git_sha
    current_git_sha(root)
  src/nexu/hashing.py:
    e: sha256_file,sha256_text
    sha256_file(path)
    sha256_text(text)
  src/nexu/init_project.py:
    e: init_project
    init_project(root)
  src/nexu/intract.py:
    e: format_intract_v1_line,_split_csv,_tokenize_contract,parse_intract_line,scan_contracts_in_text,scan_contracts_in_file,read_manifest_contracts,IntentContract
    IntentContract: key(0)
    format_intract_v1_line(contract)
    _split_csv(value)
    _tokenize_contract(line)
    parse_intract_line(line)
    scan_contracts_in_text(text)
    scan_contracts_in_file(path;root)
    read_manifest_contracts(path)
  src/nexu/intract_adapter.py:
    e: _sibling_intract_src,_ensure_intract_on_path,_result_status,_finding_for_result,_policy_findings,check_intract_policy
    _sibling_intract_src(root)
    _ensure_intract_on_path(root)
    _result_status(result)
    _finding_for_result(result)
    _policy_findings(policy)
    check_intract_policy(root;base;manifest_path;source_files)
  src/nexu/iterate.py:
    e: iterate_capsule
    iterate_capsule(root;name)
  src/nexu/journal.py:
    e: journal_path,read_journal,append_journal
    journal_path(root;name)
    read_journal(root;name)
    append_journal(root;name;event;message)
  src/nexu/llm.py:
    e: _extract_content,_strip_fences,call_litellm_json,offline_review_from_status,call_litellm_review
    _extract_content(response)
    _strip_fences(content)
    call_litellm_json(prompt)
    offline_review_from_status(status;score)
    call_litellm_review(prompt)
  src/nexu/mcp_server.py:
    e: _schema,_apply_promotion_from_mcp,_tool_map,call_tool,_result_content,_resource_list,_read_resource,_prompts_list,_prompt_get,_rpc_initialize,_rpc_handlers,handle_mcp_message,run_mcp_stdio
    _schema(properties;required)
    _apply_promotion_from_mcp(root;name)
    _tool_map(root)
    call_tool(root;tool_name;arguments)
    _result_content(data)
    _resource_list(root)
    _read_resource(root;uri)
    _prompts_list()
    _prompt_get(name;arguments)
    _rpc_initialize(params)
    _rpc_handlers(root)
    handle_mcp_message(root;message)
    run_mcp_stdio(root)
  src/nexu/models.py:
    e: utc_now,write_yaml,read_yaml,FrozenFile,FrozenSnapshot,CapsuleSelection,CapsuleRuntime,Capsule,VerificationFinding,VerificationReport,CapsuleDiff,PromptExport
    FrozenFile:
    FrozenSnapshot: to_dict(0),from_dict(2)
    CapsuleSelection:
    CapsuleRuntime:
    Capsule: to_dict(0),from_dict(2)
    VerificationFinding:
    VerificationReport: to_dict(0)
    CapsuleDiff: to_dict(0)
    PromptExport: to_dict(0)
    utc_now()
    write_yaml(path;data)
    read_yaml(path)
  src/nexu/orchestrate.py:
    e: _contract_dicts,build_orchestration_context,build_orchestration_prompt,offline_orchestration_from_context,build_capsule_orchestration,_render_orchestration_markdown
    _contract_dicts(contracts)
    build_orchestration_context(root;name)
    build_orchestration_prompt(context)
    offline_orchestration_from_context(context)
    build_capsule_orchestration(root;name)
    _render_orchestration_markdown(orchestration)
  src/nexu/paths.py:
    e: project_root,nexu_dir,snapshots_dir,capsules_dir,capsule_dir,ensure_project_dirs
    project_root(path)
    nexu_dir(root)
    snapshots_dir(root)
    capsules_dir(root)
    capsule_dir(root;name)
    ensure_project_dirs(root)
  src/nexu/plan.py:
    e: _contract_summary,build_iteration_plan
    _contract_summary(contracts)
    build_iteration_plan(root;name)
  src/nexu/promote.py:
    e: _promotion_map,build_promotion_plan,apply_promotion_plan
    _promotion_map(base;root;files)
    build_promotion_plan(root;name)
    apply_promotion_plan(root;plan)
  src/nexu/report.py:
    e: _finding_table,_html_from_markdownish,build_capsule_report
    _finding_table(findings)
    _html_from_markdownish(title;markdown)
    build_capsule_report(root;name)
  src/nexu/review.py:
    e: _markdown_review_prompt,build_review_packet
    _markdown_review_prompt(packet)
    build_review_packet(root;name)
  src/nexu/runtime.py:
    e: _read_fixture,_collect_fixtures,_html_page,build_capsule_runtime
    _read_fixture(path)
    _collect_fixtures(base)
    _html_page(name;data)
    build_capsule_runtime(root;name)
  src/nexu/status.py:
    e: capsule_status
    capsule_status(root;name)
  src/nexu/verify.py:
    e: _scan_capsule_contracts,_text,_contains_patterns,_find_term_evidence,_check_contracts_presence,_check_source_files_presence,_check_baseline_lock,_check_forbidden_write,_check_forbidden_secret,_check_output_presence,_check_required_intents,_check_iteration_count,_summary_status,verify_capsule
    _scan_capsule_contracts(base;manifest_name)
    _text(path)
    _contains_patterns(path;patterns)
    _find_term_evidence(source_files;base;terms)
    _check_contracts_presence(contracts)
    _check_source_files_presence(source_files;base)
    _check_baseline_lock(root;name;baseline_files)
    _check_forbidden_write(contracts;source_files)
    _check_forbidden_secret(contracts;source_files)
    _check_output_presence(contracts;source_files;base)
    _check_required_intents(contracts)
    _check_iteration_count(iterations)
    _summary_status(findings)
    verify_capsule(root;name)
  tests/conftest.py:
    e: _prepend_intract_src
    _prepend_intract_src()
  tests/test_capsule_flow.py:
    e: test_capsule_flow
    test_capsule_flow(tmp_path)
  tests/test_capsule_next_stage.py:
    e: test_capsule_blueprint_prompt_diff_status_and_drift
    test_capsule_blueprint_prompt_diff_status_and_drift(tmp_path)
  tests/test_capsule_runtime_report.py:
    e: test_plan_runtime_report_and_journal
    test_plan_runtime_report_and_journal(tmp_path)
  tests/test_cinema_baseline_contracts.py:
    e: test_calculator_baseline_contracts_count,test_is_calculator_capsule_by_name,test_ensure_capsule_intract_yaml_writes,test_snapshot_includes_calculator_baselines,test_merge_does_not_duplicate
    test_calculator_baseline_contracts_count()
    test_is_calculator_capsule_by_name(tmp_path)
    test_ensure_capsule_intract_yaml_writes(tmp_path)
    test_snapshot_includes_calculator_baselines(tmp_path)
    test_merge_does_not_duplicate(tmp_path)
  tests/test_cinema_dom_patch.py:
    e: test_build_function_option_patches_returns_valid_abc,test_build_function_option_patches_applies_delete_marks,test_function_patch_context_is_compact_ir,test_supports_function_patch_only_for_web_like_projects
    test_build_function_option_patches_returns_valid_abc()
    test_build_function_option_patches_applies_delete_marks()
    test_function_patch_context_is_compact_ir()
    test_supports_function_patch_only_for_web_like_projects()
  tests/test_cinema_goal_contracts.py:
    e: test_propose_goal_extension_has_baseline_require,test_goal_ledger_roundtrip,test_goal_ledger_stores_scope_contract_context,test_goal_traits_from_contract_lines,test_funnels_cohorts_goal_gets_dashboard_trait,test_api_routes_goal_gets_api_trait_and_template_anchor,test_offline_project_options_show_goal_banner
    test_propose_goal_extension_has_baseline_require()
    test_goal_ledger_roundtrip(tmp_path)
    test_goal_ledger_stores_scope_contract_context(tmp_path)
    test_goal_traits_from_contract_lines()
    test_funnels_cohorts_goal_gets_dashboard_trait()
    test_api_routes_goal_gets_api_trait_and_template_anchor()
    test_offline_project_options_show_goal_banner(tmp_path)
  tests/test_cinema_history.py:
    e: test_save_list_and_restore_files
    test_save_list_and_restore_files(tmp_path;monkeypatch)
  tests/test_cinema_html_validate.py:
    e: test_repair_adds_missing_head_and_doctype,test_relocate_style_tags_to_head,test_validate_calculator_requires_screen_and_buttons,test_prepare_rejects_non_html,test_filter_valid_option_batch_requires_all_three,test_validate_css_safety_rejects_flow_breaking_layout_css,test_validate_css_safety_allows_runtime_overlay_css,test_html_validation_rejects_generated_absolute_layout
    test_repair_adds_missing_head_and_doctype()
    test_relocate_style_tags_to_head()
    test_validate_calculator_requires_screen_and_buttons()
    test_prepare_rejects_non_html()
    test_filter_valid_option_batch_requires_all_three()
    test_validate_css_safety_rejects_flow_breaking_layout_css()
    test_validate_css_safety_allows_runtime_overlay_css()
    test_html_validation_rejects_generated_absolute_layout()
  tests/test_cinema_http_preprocess.py:
    e: test_extract_visual_css_keeps_color_and_shape_rules,test_build_html_outline_smaller_than_source_and_strips_scripts,test_preprocess_cinema_seed_writes_artifacts_beside_stage0,test_load_cinema_ui_profile_includes_seed_preprocess,test_load_cinema_seed_preprocess_artifacts_reads_active_metadata,test_preprocess_http_import_writes_artifacts,test_http_preprocess_artifacts_present_requires_files_and_patch_mode,test_ensure_http_preprocess_artifacts_skips_when_present,test_ensure_http_preprocess_artifacts_regenerates_when_missing,test_build_http_llm_context_combines_css_and_outline,test_load_cinema_ui_profile_includes_http_preprocess,test_extract_visual_css_rejects_paths_outside_source_dir,test_sanitize_http_preview_strips_external_and_fetch_scripts,test_prepare_http_preview_injects_network_shim,test_prepare_http_preview_with_shield_keeps_network_shim
    test_extract_visual_css_keeps_color_and_shape_rules(tmp_path)
    test_build_html_outline_smaller_than_source_and_strips_scripts()
    test_preprocess_cinema_seed_writes_artifacts_beside_stage0(tmp_path)
    test_load_cinema_ui_profile_includes_seed_preprocess(tmp_path)
    test_load_cinema_seed_preprocess_artifacts_reads_active_metadata(tmp_path)
    test_preprocess_http_import_writes_artifacts(tmp_path)
    test_http_preprocess_artifacts_present_requires_files_and_patch_mode(tmp_path)
    test_ensure_http_preprocess_artifacts_skips_when_present(tmp_path)
    test_ensure_http_preprocess_artifacts_regenerates_when_missing(tmp_path)
    test_build_http_llm_context_combines_css_and_outline()
    test_load_cinema_ui_profile_includes_http_preprocess(tmp_path)
    test_extract_visual_css_rejects_paths_outside_source_dir(tmp_path)
    test_sanitize_http_preview_strips_external_and_fetch_scripts()
    test_prepare_http_preview_injects_network_shim()
    test_prepare_http_preview_with_shield_keeps_network_shim()
  tests/test_cinema_iterate.py:
    e: test_build_iterate_response_payload_offline_shape,test_build_iterate_response_payload_functions_llm_failed_hint,test_build_iterate_response_payload_defaults_scope_label
    test_build_iterate_response_payload_offline_shape()
    test_build_iterate_response_payload_functions_llm_failed_hint()
    test_build_iterate_response_payload_defaults_scope_label()
  tests/test_cinema_llm.py:
    e: test_extract_html_document_from_fences,test_extract_html_document_strips_rich_terminal_frame,test_normalize_html_document_without_doctype,test_normalize_html_document_closes_partial_html,test_call_cinema_html_llm_rejects_invalid_structure,test_parse_batch_alt_options_skips_invalid_calculator_html,test_parse_batch_alt_options_repairs_missing_head,test_parse_batch_alt_options_flexible_markers_web,test_call_cinema_html_llm_accepts_html_without_doctype,test_has_terminal_artifacts_detects_box_drawing,test_extract_content_supports_choice_text_fallback,test_extract_content_error_includes_response_shape,test_compact_llm_error_openrouter_payload,test_call_cinema_html_llm_blocks_when_network_disabled,test_call_cinema_html_llm_requires_api_key,test_call_cinema_html_llm_uses_litellm,test_call_cinema_html_llm_uses_nexu_yaml_default_model,test_call_cinema_text_llm_returns_raw_content,test_call_cinema_html_llm_error_includes_non_html_preview
    test_extract_html_document_from_fences()
    test_extract_html_document_strips_rich_terminal_frame()
    test_normalize_html_document_without_doctype()
    test_normalize_html_document_closes_partial_html()
    test_call_cinema_html_llm_rejects_invalid_structure(monkeypatch;tmp_path)
    test_parse_batch_alt_options_skips_invalid_calculator_html()
    test_parse_batch_alt_options_repairs_missing_head()
    test_parse_batch_alt_options_flexible_markers_web()
    test_call_cinema_html_llm_accepts_html_without_doctype(monkeypatch;tmp_path)
    test_has_terminal_artifacts_detects_box_drawing()
    test_extract_content_supports_choice_text_fallback()
    test_extract_content_error_includes_response_shape()
    test_compact_llm_error_openrouter_payload()
    test_call_cinema_html_llm_blocks_when_network_disabled(tmp_path)
    test_call_cinema_html_llm_requires_api_key(tmp_path;monkeypatch)
    test_call_cinema_html_llm_uses_litellm(monkeypatch;tmp_path)
    test_call_cinema_html_llm_uses_nexu_yaml_default_model(monkeypatch;tmp_path)
    test_call_cinema_text_llm_returns_raw_content(monkeypatch;tmp_path)
    test_call_cinema_html_llm_error_includes_non_html_preview(monkeypatch;tmp_path)
  tests/test_cinema_llm_contracts.py:
    e: test_calculator_llm_contract_protects_screen,test_llm_contract_block_tracks_scope_and_policy,test_llm_option_variants_are_scope_contracts_not_domain_templates
    test_calculator_llm_contract_protects_screen()
    test_llm_contract_block_tracks_scope_and_policy()
    test_llm_option_variants_are_scope_contracts_not_domain_templates()
  tests/test_cinema_marked_context.py:
    e: test_build_marked_element_context_extracts_subtree_and_css,test_build_marked_element_context_uses_client_fragment_fallback,test_build_marked_element_context_returns_none_without_marks,test_build_marked_element_context_patch_mode_note,test_ui_patch_prompt_uses_marked_context_fragment,test_has_ui_marks,test_restrict_scope_css_to_marks_targets_delete_only,test_inject_scope_style_skips_global_css_for_keep_only_marks,test_inject_scope_style_scopes_css_to_delete_marks,test_resolve_marked_selectors_includes_classes,test_marked_scope_colors_css_differs_by_variant,test_should_block_full_html_for_imported_marks,test_marked_css_selectors_includes_btn_prefix
    test_build_marked_element_context_extracts_subtree_and_css()
    test_build_marked_element_context_uses_client_fragment_fallback()
    test_build_marked_element_context_returns_none_without_marks()
    test_build_marked_element_context_patch_mode_note()
    test_ui_patch_prompt_uses_marked_context_fragment()
    test_has_ui_marks()
    test_restrict_scope_css_to_marks_targets_delete_only()
    test_inject_scope_style_skips_global_css_for_keep_only_marks()
    test_inject_scope_style_scopes_css_to_delete_marks()
    test_resolve_marked_selectors_includes_classes()
    test_marked_scope_colors_css_differs_by_variant()
    test_should_block_full_html_for_imported_marks()
    test_marked_css_selectors_includes_btn_prefix()
  tests/test_cinema_markpact.py:
    e: test_build_markpact_readme,test_markpact_download_filename
    test_build_markpact_readme(tmp_path)
    test_markpact_download_filename()
  tests/test_cinema_offline_options.py:
    e: test_is_chemical_goal,test_write_chemical_options,test_calculator_chemical_goal_respects_colors_scope,test_chemical_html_has_elements,test_policy_scientific_includes_mandatory_trig,test_policy_options_a_and_b_differ,test_calculator_cinema_uses_scientific_offline,test_dashboard_project_does_not_reuse_stale_calculator_options,test_offline_chemical_from_goal_contract_lines,test_offline_scientific_screen_shows_goal,test_dashboard_seed_with_calc_body_class_stays_project_options,test_enforce_deletes_respects_session_rekeep,test_write_policy_options_without_chemical_hints,test_policy_options_restore_digit_after_delete,test_minimal_policy_keeps_all_marked_keys_even_when_compact,test_chemical_minimal_respects_keep_science_and_keep_wins_delete,test_chemical_goal_title_is_not_inside_calculator_screen,test_write_chemical_options_respects_deletes
    test_is_chemical_goal()
    test_write_chemical_options(tmp_path)
    test_calculator_chemical_goal_respects_colors_scope(tmp_path)
    test_chemical_html_has_elements()
    test_policy_scientific_includes_mandatory_trig()
    test_policy_options_a_and_b_differ()
    test_calculator_cinema_uses_scientific_offline(tmp_path)
    test_dashboard_project_does_not_reuse_stale_calculator_options(tmp_path)
    test_offline_chemical_from_goal_contract_lines(tmp_path)
    test_offline_scientific_screen_shows_goal(tmp_path)
    test_dashboard_seed_with_calc_body_class_stays_project_options(tmp_path)
    test_enforce_deletes_respects_session_rekeep(tmp_path)
    test_write_policy_options_without_chemical_hints(tmp_path)
    test_policy_options_restore_digit_after_delete(tmp_path)
    test_minimal_policy_keeps_all_marked_keys_even_when_compact(tmp_path)
    test_chemical_minimal_respects_keep_science_and_keep_wins_delete(tmp_path)
    test_chemical_goal_title_is_not_inside_calculator_screen()
    test_write_chemical_options_respects_deletes(tmp_path)
  tests/test_cinema_options_cache.py:
    e: test_options_cache_key_changes_with_stage_or_ledger,test_write_read_and_apply_options_cache
    test_options_cache_key_changes_with_stage_or_ledger()
    test_write_read_and_apply_options_cache(tmp_path)
  tests/test_cinema_policy.py:
    e: test_resolve_iteration_mode,test_normalize_manifest_target_defaults_invalid,test_apply_ledger_from_cinema_project_only,test_effective_ui_constraints_from_ledger_last_wins,test_merge_ui_constraint_lists_session_overrides_ledger,test_sync_option_previews_empty_delete_ids_mirrors_workspace,test_sync_option_previews_from_workspace,test_enforce_deletes_on_option_previews,test_ensure_option_previews_from_stages,test_propose_ui_delta_and_validate
    test_resolve_iteration_mode()
    test_normalize_manifest_target_defaults_invalid()
    test_apply_ledger_from_cinema_project_only(tmp_path)
    test_effective_ui_constraints_from_ledger_last_wins()
    test_merge_ui_constraint_lists_session_overrides_ledger()
    test_sync_option_previews_empty_delete_ids_mirrors_workspace(tmp_path)
    test_sync_option_previews_from_workspace(tmp_path)
    test_enforce_deletes_on_option_previews(tmp_path)
    test_ensure_option_previews_from_stages(tmp_path)
    test_propose_ui_delta_and_validate(tmp_path)
  tests/test_cinema_project_imports.py:
    e: test_import_zip_project_creates_markpact_migration_and_options,test_merged_projects_catalog_includes_imported,test_delete_project_hides_demo_from_workspace_catalog,test_activate_imported_project_reloads_stages,test_validate_urls_reject_file_scheme,test_safe_extract_zip_rejects_unsafe_paths,test_import_http_project_fetches_and_migrates,test_activate_http_import_regenerates_preview_stage0,test_activate_http_import_regenerates_preprocess_when_missing,test_activate_http_import_empty_subtitle_not_goal,test_activate_zip_import_does_not_require_user_goal,test_activate_imported_project_resets_calculator_ledger,test_import_http_project_requires_network_flag,test_import_git_project_requires_network_flag,test_is_deletable_imported_id,test_delete_imported_http_domain_id_with_dot,test_delete_imported_project_removes_directory,test_read_imported_markpact_returns_markdown
    test_import_zip_project_creates_markpact_migration_and_options(tmp_path)
    test_merged_projects_catalog_includes_imported(tmp_path)
    test_delete_project_hides_demo_from_workspace_catalog(tmp_path)
    test_activate_imported_project_reloads_stages(tmp_path)
    test_validate_urls_reject_file_scheme()
    test_safe_extract_zip_rejects_unsafe_paths(tmp_path)
    test_import_http_project_fetches_and_migrates(tmp_path)
    test_activate_http_import_regenerates_preview_stage0(tmp_path)
    test_activate_http_import_regenerates_preprocess_when_missing(tmp_path)
    test_activate_http_import_empty_subtitle_not_goal(tmp_path)
    test_activate_zip_import_does_not_require_user_goal(tmp_path)
    test_activate_imported_project_resets_calculator_ledger(tmp_path)
    test_import_http_project_requires_network_flag(tmp_path)
    test_import_git_project_requires_network_flag(tmp_path)
    test_is_deletable_imported_id()
    test_delete_imported_http_domain_id_with_dot(tmp_path)
    test_delete_imported_project_removes_directory(tmp_path)
    test_read_imported_markpact_returns_markdown(tmp_path)
  tests/test_cinema_project_ir.py:
    e: test_build_project_ir_extracts_functional_outline
    test_build_project_ir_extracts_functional_outline()
  tests/test_cinema_projects.py:
    e: test_list_project_catalog_has_nine_examples,test_workspace_catalog_can_hide_demo_project,test_activate_example_project_seeds_when_no_source,test_activate_frontend_view_seeds_selectable_web_gui,test_activate_analytics_copies_cinema_when_repo_available,test_activate_copies_dashboard_cinema_when_repo_available,test_activate_backend_service_resets_ledger_and_distinct_options,test_activate_dashboard_replaces_stale_calculator_options,test_activate_calculator_preserves_distinct_option_previews
    test_list_project_catalog_has_nine_examples()
    test_workspace_catalog_can_hide_demo_project(tmp_path)
    test_activate_example_project_seeds_when_no_source(tmp_path)
    test_activate_frontend_view_seeds_selectable_web_gui(tmp_path)
    test_activate_analytics_copies_cinema_when_repo_available()
    test_activate_copies_dashboard_cinema_when_repo_available()
    test_activate_backend_service_resets_ledger_and_distinct_options(tmp_path)
    test_activate_dashboard_replaces_stale_calculator_options(tmp_path)
    test_activate_calculator_preserves_distinct_option_previews()
  tests/test_cinema_publish.py:
    e: cinema_setup,test_publish_creates_service_files,test_list_and_start_stop_service,test_publish_missing_stage_returns_error
    cinema_setup(tmp_path)
    test_publish_creates_service_files(cinema_setup)
    test_list_and_start_stop_service(cinema_setup)
    test_publish_missing_stage_returns_error(cinema_setup)
  tests/test_cinema_scope.py:
    e: test_dashboard_disallows_keypad_scope,test_calculator_allows_keypad_scope,test_offline_fast_scopes_per_kind,test_dashboard_colors_offline_labels,test_scope_option_variants_dashboard_functions,test_strip_and_inject_scope_style,test_scoped_html_fragment_for_calculator_colors,test_cinema_has_offline_baseline,test_inject_scope_style_calculator_colors,test_load_cinema_ui_profile_from_active_and_stage,test_ui_profile_ignores_runtime_script_tokens,test_can_use_offline_fast_iterate,test_imported_kind_uses_web_scopes,test_http_import_offline_colors_keeps_site_markers,test_http_import_offline_colors_recolors_marked_buttons
    test_dashboard_disallows_keypad_scope()
    test_calculator_allows_keypad_scope()
    test_offline_fast_scopes_per_kind()
    test_dashboard_colors_offline_labels(tmp_path)
    test_scope_option_variants_dashboard_functions()
    test_strip_and_inject_scope_style()
    test_scoped_html_fragment_for_calculator_colors()
    test_cinema_has_offline_baseline(tmp_path)
    test_inject_scope_style_calculator_colors()
    test_load_cinema_ui_profile_from_active_and_stage(tmp_path)
    test_ui_profile_ignores_runtime_script_tokens(tmp_path)
    test_can_use_offline_fast_iterate(tmp_path)
    test_imported_kind_uses_web_scopes()
    test_http_import_offline_colors_keeps_site_markers(tmp_path;monkeypatch)
    test_http_import_offline_colors_recolors_marked_buttons(tmp_path)
  tests/test_cinema_scripts.py:
    e: test_finalize_strips_truncated_llm_script_and_injects_canonical,test_finalize_marks_web_gui_components_as_selectable_targets,test_inject_cinema_shield_preserves_existing_scripts,test_inject_cinema_shield_posts_compact_marked_fragment
    test_finalize_strips_truncated_llm_script_and_injects_canonical()
    test_finalize_marks_web_gui_components_as_selectable_targets()
    test_inject_cinema_shield_preserves_existing_scripts()
    test_inject_cinema_shield_posts_compact_marked_fragment()
  tests/test_cinema_server.py:
    e: test_render_server_script_embeds_runtime_context,test_render_server_script_embeds_openrouter_model,test_write_cinema_nexu_hooks_uses_template,test_render_stage_template_injects_runtime_scripts,test_cinema_player_template_is_externalized,test_render_server_script_embeds_project_import_routes,test_write_cinema_nexu_hooks_includes_import_helpers,_free_port,test_iterate_colors_scope_uses_offline_path,test_iterate_dashboard_kinds_colors_prefers_offline_before_llm,test_iterate_colors_scope_uses_llm_patch_when_available,test_effective_markpact_mode_off_for_visual_scope,test_iterate_functions_scope_skips_offline_fast_path,test_iterate_colors_without_stage0_skips_offline,test_start_cinema_player_server_returns_url_without_opening,test_projects_import_zip_endpoint,test_delete_imported_http_domain_id_via_api,_LLMConfig
    _LLMConfig:
    test_render_server_script_embeds_runtime_context()
    test_render_server_script_embeds_openrouter_model()
    test_write_cinema_nexu_hooks_uses_template(tmp_path)
    test_render_stage_template_injects_runtime_scripts()
    test_cinema_player_template_is_externalized()
    test_render_server_script_embeds_project_import_routes()
    test_write_cinema_nexu_hooks_includes_import_helpers(tmp_path)
    _free_port()
    test_iterate_colors_scope_uses_offline_path(tmp_path)
    test_iterate_dashboard_kinds_colors_prefers_offline_before_llm(tmp_path)
    test_iterate_colors_scope_uses_llm_patch_when_available(tmp_path)
    test_effective_markpact_mode_off_for_visual_scope()
    test_iterate_functions_scope_skips_offline_fast_path(tmp_path)
    test_iterate_colors_without_stage0_skips_offline(tmp_path)
    test_start_cinema_player_server_returns_url_without_opening(monkeypatch;tmp_path)
    test_projects_import_zip_endpoint(tmp_path)
    test_delete_imported_http_domain_id_via_api(tmp_path)
  tests/test_cinema_spatial_patch.py:
    e: test_apply_spatial_deletes_removes_dashboard_kpi_card,test_apply_spatial_deletes_removes_only_marked_buttons
    test_apply_spatial_deletes_removes_dashboard_kpi_card()
    test_apply_spatial_deletes_removes_only_marked_buttons()
  tests/test_cinema_traces.py:
    e: test_load_config_llm_model_default,test_load_config_llm_model_from_yaml,test_llm_model_env_overrides_yaml,test_redact_secrets_masks_api_keys,test_text_metrics_counts_utf8_bytes_and_estimated_tokens,test_write_and_read_llm_trace,test_load_config_reads_cinema_section
    test_load_config_llm_model_default(tmp_path)
    test_load_config_llm_model_from_yaml(tmp_path)
    test_llm_model_env_overrides_yaml(tmp_path;monkeypatch)
    test_redact_secrets_masks_api_keys()
    test_text_metrics_counts_utf8_bytes_and_estimated_tokens()
    test_write_and_read_llm_trace(tmp_path)
    test_load_config_reads_cinema_section(tmp_path)
  tests/test_cinema_ui_patch.py:
    e: test_build_ui_patch_prompt_is_json_contract,test_parse_and_apply_ui_patch_response,test_apply_ui_patch_restricts_visual_scope_to_red_marks,test_apply_ui_patch_noops_visual_scope_with_keep_only_marks,test_apply_ui_patch_rejects_unsafe_css,test_apply_ui_patch_rejects_flow_breaking_css,test_supports_llm_patch_scope
    test_build_ui_patch_prompt_is_json_contract()
    test_parse_and_apply_ui_patch_response()
    test_apply_ui_patch_restricts_visual_scope_to_red_marks()
    test_apply_ui_patch_noops_visual_scope_with_keep_only_marks()
    test_apply_ui_patch_rejects_unsafe_css()
    test_apply_ui_patch_rejects_flow_breaking_css()
    test_supports_llm_patch_scope()
  tests/test_export_prompt_ledger.py:
    e: test_export_prompt_includes_cinema_ledger_block
    test_export_prompt_includes_cinema_ledger_block(tmp_path)
  tests/test_fast_delivery.py:
    e: test_choose_options_route_prefers_cache,test_choose_options_route_uses_llm_patch_before_offline,test_choose_options_route_falls_back_to_offline,test_choose_options_route_falls_back_to_parallel_llm,test_options_status_helpers,test_compact_html_for_llm_removes_scripts_and_limits,test_markpact_context_helpers,test_fast_delivery_options_cache_roundtrip,test_fast_delivery_options_cache_rejects_invalid_cached_html,test_fast_delivery_options_cache_rejects_calculator_for_web_stage
    test_choose_options_route_prefers_cache()
    test_choose_options_route_uses_llm_patch_before_offline()
    test_choose_options_route_falls_back_to_offline()
    test_choose_options_route_falls_back_to_parallel_llm()
    test_options_status_helpers()
    test_compact_html_for_llm_removes_scripts_and_limits()
    test_markpact_context_helpers()
    test_fast_delivery_options_cache_roundtrip(tmp_path)
    test_fast_delivery_options_cache_rejects_invalid_cached_html(tmp_path)
    test_fast_delivery_options_cache_rejects_calculator_for_web_stage(tmp_path)
  tests/test_intract.py:
    e: test_parse_intract_line
    test_parse_intract_line()
  tests/test_models.py:
    e: test_capsule_roundtrip,test_snapshot_roundtrip
    test_capsule_roundtrip()
    test_snapshot_roundtrip()
  tests/test_nexu.py:
    e: test_placeholder,test_import
    test_placeholder()
    test_import()
  tests/test_orchestration_mcp.py:
    e: _make_project,test_orchestration_offline,test_mcp_tool_dispatch_and_protocol
    _make_project(tmp_path)
    test_orchestration_offline(tmp_path)
    test_mcp_tool_dispatch_and_protocol(tmp_path)
  tests/test_promote_apply.py:
    e: test_apply_promotion_plan
    test_apply_promotion_plan(tmp_path)
  tests/test_review_bundle.py:
    e: test_review_bundle_and_promotion_prechecks
    test_review_bundle_and_promotion_prechecks(tmp_path)
  tests/test_verify_intract.py:
    e: test_verify_treats_manifest_intract_fail_as_warn
    test_verify_treats_manifest_intract_fail_as_warn(tmp_path)
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('nexu', '0.5.22', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.less', 155, 'less').
project_file('examples/backend_service/app/users.py', 9, 'python').
project_file('examples/frontend_view/src/menu_icons.py', 25, 'python').
project_file('examples/mcp_service/src/demo.py', 11, 'python').
project_file('examples/nexu_markpact_exporter.py', 96, 'python').
project_file('examples/realtime_lane_nexu_sync.py', 63, 'python').
project_file('examples/run_examples.py', 80, 'python').
project_file('examples/scientific_calculator_demo.py', 62, 'python').
project_file('examples/scientific_calculator_demo2.py', 87, 'python').
project_file('examples/vertical_slice/src/flow.py', 10, 'python').
project_file('examples/web_app_calculator/cinema/nexu_hooks.py', 281, 'python').
project_file('examples/web_app_calculator/cinema/server.py', 2747, 'python').
project_file('examples/web_app_calculator/markpact_sandbox/sandbox/src/calculator.py', 38, 'python').
project_file('examples/web_app_calculator/run.py', 111, 'python').
project_file('examples/web_app_calculator/src/calculator.py', 39, 'python').
project_file('examples/web_app_calculator/workspace/src/calculator.py', 39, 'python').
project_file('examples/web_app_dashboard/run.py', 119, 'python').
project_file('examples/web_app_dashboard/src/dashboard.py', 11, 'python').
project_file('examples/web_app_dashboard/workspace/src/dashboard.py', 25, 'python').
project_file('examples/web_app_event_monitor/run.py', 91, 'python').
project_file('examples/web_app_pactown_ecosystem/run.py', 98, 'python').
project_file('project.sh', 50, 'shell').
project_file('scripts/check-doc-links.py', 115, 'python').
project_file('scripts/ci-cinema-smoke.sh', 86, 'shell').
project_file('src/nexu/__init__.py', 6, 'python').
project_file('src/nexu/__main__.py', 5, 'python').
project_file('src/nexu/blueprint.py', 74, 'python').
project_file('src/nexu/bundle.py', 56, 'python').
project_file('src/nexu/capsule.py', 125, 'python').
project_file('src/nexu/cinema.py', 195, 'python').
project_file('src/nexu/cinema_baseline_contracts.py', 174, 'python').
project_file('src/nexu/cinema_dom_patch.py', 203, 'python').
project_file('src/nexu/cinema_goal_contracts.py', 346, 'python').
project_file('src/nexu/cinema_history.py', 245, 'python').
project_file('src/nexu/cinema_html.py', 17, 'python').
project_file('src/nexu/cinema_html_validate.py', 230, 'python').
project_file('src/nexu/cinema_http_preprocess.py', 624, 'python').
project_file('src/nexu/cinema_iterate.py', 67, 'python').
project_file('src/nexu/cinema_llm.py', 333, 'python').
project_file('src/nexu/cinema_llm_contracts.py', 197, 'python').
project_file('src/nexu/cinema_marked_context.py', 503, 'python').
project_file('src/nexu/cinema_markpact.py', 216, 'python').
project_file('src/nexu/cinema_offline_options.py', 898, 'python').
project_file('src/nexu/cinema_options_cache.py', 129, 'python').
project_file('src/nexu/cinema_policy.py', 862, 'python').
project_file('src/nexu/cinema_project_imports.py', 1135, 'python').
project_file('src/nexu/cinema_project_ir.py', 133, 'python').
project_file('src/nexu/cinema_projects.py', 721, 'python').
project_file('src/nexu/cinema_publish.py', 470, 'python').
project_file('src/nexu/cinema_scope.py', 687, 'python').
project_file('src/nexu/cinema_scripts.py', 773, 'python').
project_file('src/nexu/cinema_server.py', 145, 'python').
project_file('src/nexu/cinema_traces.py', 167, 'python').
project_file('src/nexu/cinema_ui_patch.py', 269, 'python').
project_file('src/nexu/cli.py', 380, 'python').
project_file('src/nexu/config.py', 192, 'python').
project_file('src/nexu/diff.py', 36, 'python').
project_file('src/nexu/drift.py', 37, 'python').
project_file('src/nexu/export_prompt.py', 161, 'python').
project_file('src/nexu/fast_delivery/__init__.py', 25, 'python').
project_file('src/nexu/fast_delivery/context.py', 67, 'python').
project_file('src/nexu/fast_delivery/options.py', 129, 'python').
project_file('src/nexu/fast_delivery/router.py', 69, 'python').
project_file('src/nexu/files.py', 52, 'python').
project_file('src/nexu/freeze.py', 27, 'python').
project_file('src/nexu/git.py', 23, 'python').
project_file('src/nexu/hashing.py', 17, 'python').
project_file('src/nexu/init_project.py', 87, 'python').
project_file('src/nexu/intract.py', 141, 'python').
project_file('src/nexu/intract_adapter.py', 134, 'python').
project_file('src/nexu/iterate.py', 45, 'python').
project_file('src/nexu/journal.py', 44, 'python').
project_file('src/nexu/llm.py', 166, 'python').
project_file('src/nexu/mcp_server.py', 394, 'python').
project_file('src/nexu/models.py', 155, 'python').
project_file('src/nexu/orchestrate.py', 233, 'python').
project_file('src/nexu/paths.py', 36, 'python').
project_file('src/nexu/plan.py', 82, 'python').
project_file('src/nexu/promote.py', 93, 'python').
project_file('src/nexu/report.py', 95, 'python').
project_file('src/nexu/review.py', 158, 'python').
project_file('src/nexu/runtime.py', 132, 'python').
project_file('src/nexu/status.py', 36, 'python').
project_file('src/nexu/verify.py', 318, 'python').
project_file('tests/conftest.py', 23, 'python').
project_file('tests/test_capsule_flow.py', 26, 'python').
project_file('tests/test_capsule_next_stage.py', 59, 'python').
project_file('tests/test_capsule_runtime_report.py', 51, 'python').
project_file('tests/test_cinema_baseline_contracts.py', 53, 'python').
project_file('tests/test_cinema_dom_patch.py', 71, 'python').
project_file('tests/test_cinema_goal_contracts.py', 128, 'python').
project_file('tests/test_cinema_history.py', 50, 'python').
project_file('tests/test_cinema_html_validate.py', 106, 'python').
project_file('tests/test_cinema_http_preprocess.py', 279, 'python').
project_file('tests/test_cinema_iterate.py', 89, 'python').
project_file('tests/test_cinema_llm.py', 279, 'python').
project_file('tests/test_cinema_llm_contracts.py', 61, 'python').
project_file('tests/test_cinema_marked_context.py', 210, 'python').
project_file('tests/test_cinema_markpact.py', 45, 'python').
project_file('tests/test_cinema_offline_options.py', 318, 'python').
project_file('tests/test_cinema_options_cache.py', 65, 'python').
project_file('tests/test_cinema_policy.py', 187, 'python').
project_file('tests/test_cinema_project_imports.py', 501, 'python').
project_file('tests/test_cinema_project_ir.py', 23, 'python').
project_file('tests/test_cinema_projects.py', 206, 'python').
project_file('tests/test_cinema_publish.py', 99, 'python').
project_file('tests/test_cinema_scope.py', 263, 'python').
project_file('tests/test_cinema_scripts.py', 45, 'python').
project_file('tests/test_cinema_server.py', 1004, 'python').
project_file('tests/test_cinema_spatial_patch.py', 30, 'python').
project_file('tests/test_cinema_traces.py', 112, 'python').
project_file('tests/test_cinema_ui_patch.py', 157, 'python').
project_file('tests/test_export_prompt_ledger.py', 42, 'python').
project_file('tests/test_fast_delivery.py', 243, 'python').
project_file('tests/test_intract.py', 12, 'python').
project_file('tests/test_models.py', 15, 'python').
project_file('tests/test_nexu.py', 12, 'python').
project_file('tests/test_orchestration_mcp.py', 63, 'python').
project_file('tests/test_promote_apply.py', 37, 'python').
project_file('tests/test_review_bundle.py', 46, 'python').
project_file('tests/test_verify_intract.py', 29, 'python').
project_file('tree.sh', 2, 'shell').

% ── Python Functions ─────────────────────────────────────
python_function('examples/backend_service/app/users.py', 'list_users', 2, 4, 1).
python_function('examples/frontend_view/src/menu_icons.py', 'preview_menu_icons', 1, 3, 2).
python_function('examples/mcp_service/src/demo.py', 'plan_demo', 1, 1, 0).
python_function('examples/nexu_markpact_exporter.py', 'main', 0, 3, 10).
python_function('examples/realtime_lane_nexu_sync.py', 'simulate_realtime_sync', 0, 2, 2).
python_function('examples/run_examples.py', 'run_example', 1, 2, 23).
python_function('examples/run_examples.py', 'main', 0, 2, 1).
python_function('examples/scientific_calculator_demo.py', 'main', 0, 2, 14).
python_function('examples/scientific_calculator_demo2.py', 'print_code', 2, 1, 4).
python_function('examples/scientific_calculator_demo2.py', 'main', 0, 2, 11).
python_function('examples/vertical_slice/src/flow.py', 'run_flow', 1, 1, 0).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'apply_manifest_from_ledger', 0, 1, 1).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'verify_capsule', 0, 1, 1).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'apply_spatial_patch', 2, 2, 2).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'propose_llm', 3, 1, 1).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'append_policy_entry', 5, 1, 1).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'append_goal_policy_entry', 2, 11, 8).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'goal_contract_lines', 0, 1, 1).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'validate_artifact', 3, 1, 1).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'save_history', 0, 1, 3).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'list_history', 0, 1, 4).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'restore_history', 1, 1, 1).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'effective_ui_constraints', 1, 1, 1).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'sync_option_previews', 2, 1, 3).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'patch_option_previews', 3, 10, 7).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'projects_catalog', 0, 1, 3).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'activate_project', 1, 2, 6).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'import_project_from_zip', 2, 1, 3).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'import_project_from_git', 2, 2, 3).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'import_project_from_http', 1, 1, 3).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'delete_imported', 1, 1, 4).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'imported_markpact', 1, 1, 3).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'imported_llm_log', 1, 1, 3).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'active_project', 0, 1, 3).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'export_markpact_readme', 2, 2, 5).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'services_catalog', 0, 1, 3).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'publish_service', 0, 1, 3).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'start_service', 1, 1, 3).
python_function('examples/web_app_calculator/cinema/nexu_hooks.py', 'stop_service', 1, 1, 3).
python_function('examples/web_app_calculator/cinema/server.py', '_load_cinema_ui_profile', 0, 7, 7).
python_function('examples/web_app_calculator/cinema/server.py', '_goal_entry_kwargs', 1, 4, 3).
python_function('examples/web_app_calculator/cinema/server.py', '_llm_prompt_intro', 1, 6, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_llm_prompt_rules', 1, 4, 3).
python_function('examples/web_app_calculator/cinema/server.py', '_llm_communication_contract_block', 0, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_load_env_file', 2, 11, 7).
python_function('examples/web_app_calculator/cinema/server.py', '_load_all_env', 0, 3, 3).
python_function('examples/web_app_calculator/cinema/server.py', '_resolve_model', 0, 4, 2).
python_function('examples/web_app_calculator/cinema/server.py', '_llm_network_allowed', 0, 2, 2).
python_function('examples/web_app_calculator/cinema/server.py', '_litellm_available', 0, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_llm_status_payload', 0, 3, 9).
python_function('examples/web_app_calculator/cinema/server.py', '_trace_slug', 1, 1, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_read_trace_index', 0, 1, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_write_llm_trace', 0, 3, 5).
python_function('examples/web_app_calculator/cinema/server.py', '_list_llm_traces', 1, 6, 5).
python_function('examples/web_app_calculator/cinema/server.py', '_path_segments', 1, 3, 4).
python_function('examples/web_app_calculator/cinema/server.py', '_parse_imported_project_route', 1, 5, 2).
python_function('examples/web_app_calculator/cinema/server.py', '_delete_imported_project', 1, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_imported_markpact', 1, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_imported_llm_log', 1, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_read_llm_trace', 1, 1, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_ensure_api_key_env', 0, 3, 2).
python_function('examples/web_app_calculator/cinema/server.py', '_strip_markdown_fences', 1, 6, 5).
python_function('examples/web_app_calculator/cinema/server.py', '_extract_html_document', 1, 3, 4).
python_function('examples/web_app_calculator/cinema/server.py', '_compact_html_for_llm', 1, 1, 4).
python_function('examples/web_app_calculator/cinema/server.py', '_effective_markpact_mode', 2, 1, 4).
python_function('examples/web_app_calculator/cinema/server.py', '_compact_markpact_for_llm', 1, 3, 6).
python_function('examples/web_app_calculator/cinema/server.py', '_try_read_options_cache', 0, 2, 3).
python_function('examples/web_app_calculator/cinema/server.py', '_store_options_cache', 0, 1, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_extract_llm_content', 1, 9, 6).
python_function('examples/web_app_calculator/cinema/server.py', '_compact_llm_error', 1, 2, 4).
python_function('examples/web_app_calculator/cinema/server.py', '_load_policy_payload', 0, 4, 5).
python_function('examples/web_app_calculator/cinema/server.py', '_effective_ui_constraints_from_ledger', 2, 17, 8).
python_function('examples/web_app_calculator/cinema/server.py', '_merge_ui_constraints', 4, 17, 4).
python_function('examples/web_app_calculator/cinema/server.py', '_ensure_intract_on_path', 0, 5, 5).
python_function('examples/web_app_calculator/cinema/server.py', '_propose_cinema_contracts', 3, 5, 3).
python_function('examples/web_app_calculator/cinema/server.py', '_proposal_kind_and_element', 1, 12, 3).
python_function('examples/web_app_calculator/cinema/server.py', '_proposal_delta_text', 2, 5, 3).
python_function('examples/web_app_calculator/cinema/server.py', '_normalize_proposals_for_ledger', 2, 3, 6).
python_function('examples/web_app_calculator/cinema/server.py', '_append_policy_entry_legacy', 5, 3, 12).
python_function('examples/web_app_calculator/cinema/server.py', '_nexu_hooks_apply', 0, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_nexu_hooks_verify', 0, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_propose_llm_for_stage', 2, 2, 2).
python_function('examples/web_app_calculator/cinema/server.py', '_validate_intract_artifact', 3, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_append_policy_entry', 5, 2, 2).
python_function('examples/web_app_calculator/cinema/server.py', '_save_history_checkpoint', 0, 3, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_list_history', 0, 4, 2).
python_function('examples/web_app_calculator/cinema/server.py', '_restore_history', 1, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_sync_option_previews', 2, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_patch_option_previews', 3, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_projects_catalog', 0, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_active_project', 0, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_activate_project', 1, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_import_project', 1, 12, 7).
python_function('examples/web_app_calculator/cinema/server.py', '_import_project_zip', 2, 3, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_import_project_git', 1, 5, 4).
python_function('examples/web_app_calculator/cinema/server.py', '_import_project_http', 1, 3, 4).
python_function('examples/web_app_calculator/cinema/server.py', '_parse_multipart_zip', 2, 7, 7).
python_function('examples/web_app_calculator/cinema/server.py', '_export_markpact_markdown', 0, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_services_catalog', 0, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_publish_service', 0, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_start_service', 1, 2, 1).
python_function('examples/web_app_calculator/cinema/server.py', '_stop_service', 1, 2, 1).
python_function('examples/web_app_calculator/markpact_sandbox/sandbox/src/calculator.py', 'render_calculator', 1, 1, 0).
python_function('examples/web_app_calculator/run.py', 'main', 0, 2, 13).
python_function('examples/web_app_calculator/src/calculator.py', 'render_calculator', 1, 1, 0).
python_function('examples/web_app_calculator/workspace/src/calculator.py', 'render_calculator', 1, 1, 0).
python_function('examples/web_app_dashboard/run.py', 'main', 0, 2, 17).
python_function('examples/web_app_dashboard/src/dashboard.py', 'render_dashboard', 1, 1, 1).
python_function('examples/web_app_dashboard/workspace/src/dashboard.py', 'render_dashboard', 1, 2, 2).
python_function('examples/web_app_event_monitor/run.py', 'main', 0, 13, 14).
python_function('examples/web_app_pactown_ecosystem/run.py', 'main', 0, 8, 16).
python_function('scripts/check-doc-links.py', '_is_external', 1, 3, 3).
python_function('scripts/check-doc-links.py', '_slug', 1, 1, 3).
python_function('scripts/check-doc-links.py', '_anchors', 1, 3, 5).
python_function('scripts/check-doc-links.py', '_markdown_files', 1, 4, 4).
python_function('scripts/check-doc-links.py', '_targets', 1, 1, 1).
python_function('scripts/check-doc-links.py', '_resolve', 2, 1, 4).
python_function('scripts/check-doc-links.py', 'check_links', 1, 12, 15).
python_function('scripts/check-doc-links.py', 'main', 0, 3, 5).
python_function('src/nexu/blueprint.py', 'build_blueprint', 2, 7, 7).
python_function('src/nexu/bundle.py', '_should_include', 2, 5, 3).
python_function('src/nexu/bundle.py', 'build_capsule_bundle', 2, 3, 14).
python_function('src/nexu/capsule.py', 'default_contract_manifest', 1, 1, 1).
python_function('src/nexu/capsule.py', 'create_capsule', 2, 8, 20).
python_function('src/nexu/capsule.py', 'list_capsules', 1, 4, 5).
python_function('src/nexu/capsule.py', 'load_capsule', 2, 1, 3).
python_function('src/nexu/capsule.py', 'save_capsule', 2, 1, 3).
python_function('src/nexu/cinema.py', '_cinema_template_text', 1, 1, 3).
python_function('src/nexu/cinema.py', '_render_cinema_template', 1, 2, 5).
python_function('src/nexu/cinema.py', 'write_cinema_nexu_hooks', 3, 1, 6).
python_function('src/nexu/cinema.py', '_contract_to_public_dict', 1, 1, 1).
python_function('src/nexu/cinema.py', 'build_intract_policy_snapshot', 2, 11, 13).
python_function('src/nexu/cinema.py', 'sync_cinema_templates', 3, 1, 4).
python_function('src/nexu/cinema.py', 'write_intract_policy_files', 3, 2, 4).
python_function('src/nexu/cinema.py', 'generate_cinema_player', 2, 1, 10).
python_function('src/nexu/cinema.py', '_start_cinema_server', 3, 2, 3).
python_function('src/nexu/cinema_baseline_contracts.py', '_contract', 3, 3, 2).
python_function('src/nexu/cinema_baseline_contracts.py', 'calculator_baseline_contracts', 0, 1, 1).
python_function('src/nexu/cinema_baseline_contracts.py', 'is_calculator_capsule', 2, 5, 5).
python_function('src/nexu/cinema_baseline_contracts.py', 'merge_calculator_baselines', 3, 5, 5).
python_function('src/nexu/cinema_baseline_contracts.py', 'ensure_capsule_intract_yaml', 2, 9, 9).
python_function('src/nexu/cinema_dom_patch.py', 'supports_function_patch', 2, 4, 2).
python_function('src/nexu/cinema_dom_patch.py', 'build_function_patch_context', 1, 2, 3).
python_function('src/nexu/cinema_dom_patch.py', '_strip_existing_patch', 1, 2, 2).
python_function('src/nexu/cinema_dom_patch.py', '_goal_label', 1, 3, 2).
python_function('src/nexu/cinema_dom_patch.py', '_variant_section', 3, 3, 5).
python_function('src/nexu/cinema_dom_patch.py', '_patch_style', 0, 1, 0).
python_function('src/nexu/cinema_dom_patch.py', '_inject_into_head', 2, 4, 4).
python_function('src/nexu/cinema_dom_patch.py', '_inject_into_body', 2, 2, 2).
python_function('src/nexu/cinema_dom_patch.py', 'build_function_option_patches', 1, 8, 13).
python_function('src/nexu/cinema_goal_contracts.py', '_hints_text', 1, 3, 4).
python_function('src/nexu/cinema_goal_contracts.py', 'is_chemical_goal', 1, 2, 2).
python_function('src/nexu/cinema_goal_contracts.py', '_slug', 1, 2, 3).
python_function('src/nexu/cinema_goal_contracts.py', '_goal_contract_dict', 3, 6, 8).
python_function('src/nexu/cinema_goal_contracts.py', '_resolve_baseline_anchor', 2, 5, 0).
python_function('src/nexu/cinema_goal_contracts.py', '_build_detail_text', 4, 5, 2).
python_function('src/nexu/cinema_goal_contracts.py', '_detect_chemical_trait', 3, 2, 2).
python_function('src/nexu/cinema_goal_contracts.py', '_detect_minimal_trait', 4, 4, 3).
python_function('src/nexu/cinema_goal_contracts.py', '_detect_expanded_trait', 4, 4, 3).
python_function('src/nexu/cinema_goal_contracts.py', '_detect_api_trait', 4, 3, 3).
python_function('src/nexu/cinema_goal_contracts.py', '_detect_dashboard_trait', 4, 3, 3).
python_function('src/nexu/cinema_goal_contracts.py', '_detect_engineering_trait', 5, 4, 3).
python_function('src/nexu/cinema_goal_contracts.py', '_collect_trait_proposals', 6, 3, 6).
python_function('src/nexu/cinema_goal_contracts.py', 'propose_goal_extension_contracts', 1, 15, 9).
python_function('src/nexu/cinema_goal_contracts.py', 'goal_traits_from_contract_lines', 1, 2, 2).
python_function('src/nexu/cinema_history.py', 'history_dir', 1, 1, 0).
python_function('src/nexu/cinema_history.py', 'history_index_path', 1, 1, 1).
python_function('src/nexu/cinema_history.py', '_load_index', 1, 3, 5).
python_function('src/nexu/cinema_history.py', '_write_index', 2, 1, 5).
python_function('src/nexu/cinema_history.py', '_copy_checkpoint_files', 2, 3, 3).
python_function('src/nexu/cinema_history.py', '_ledger_snapshot', 1, 3, 4).
python_function('src/nexu/cinema_history.py', '_build_label', 0, 4, 3).
python_function('src/nexu/cinema_history.py', 'save_history_checkpoint', 1, 4, 15).
python_function('src/nexu/cinema_history.py', 'list_history_checkpoints', 1, 1, 3).
python_function('src/nexu/cinema_history.py', 'restore_history_checkpoint', 3, 8, 13).
python_function('src/nexu/cinema_history.py', '_refresh_policy_snapshot', 3, 1, 1).
python_function('src/nexu/cinema_history.py', 'ensure_initial_checkpoint', 1, 3, 4).
python_function('src/nexu/cinema_history.py', 'ledger_archive_for_display', 1, 5, 11).
python_function('src/nexu/cinema_html.py', 'ensure_html_document_closure', 1, 5, 3).
python_function('src/nexu/cinema_html_validate.py', '_strip_css_comments', 1, 2, 2).
python_function('src/nexu/cinema_html_validate.py', '_selector_is_runtime_only', 1, 2, 2).
python_function('src/nexu/cinema_html_validate.py', 'validate_css_safety', 1, 14, 15).
python_function('src/nexu/cinema_html_validate.py', '_looks_like_html_document', 1, 3, 3).
python_function('src/nexu/cinema_html_validate.py', '_has_open_tag', 2, 1, 1).
python_function('src/nexu/cinema_html_validate.py', '_has_close_tag', 2, 1, 1).
python_function('src/nexu/cinema_html_validate.py', 'relocate_style_tags_to_head', 1, 9, 10).
python_function('src/nexu/cinema_html_validate.py', 'repair_html_structure', 1, 12, 13).
python_function('src/nexu/cinema_html_validate.py', '_validate_basic_tags', 2, 7, 5).
python_function('src/nexu/cinema_html_validate.py', '_validate_calculator_elements', 2, 3, 2).
python_function('src/nexu/cinema_html_validate.py', 'validate_cinema_html_document', 1, 8, 14).
python_function('src/nexu/cinema_html_validate.py', 'prepare_cinema_html_document', 1, 2, 2).
python_function('src/nexu/cinema_html_validate.py', 'filter_valid_option_batch', 1, 9, 6).
python_function('src/nexu/cinema_http_preprocess.py', '_safe_read_under', 2, 5, 5).
python_function('src/nexu/cinema_http_preprocess.py', '_extract_inline_css', 1, 4, 3).
python_function('src/nexu/cinema_http_preprocess.py', '_extract_stylesheet_hrefs', 1, 7, 4).
python_function('src/nexu/cinema_http_preprocess.py', '_normalize_linked_paths', 2, 9, 6).
python_function('src/nexu/cinema_http_preprocess.py', '_split_css_rules', 1, 9, 4).
python_function('src/nexu/cinema_http_preprocess.py', '_rule_is_visual', 1, 7, 4).
python_function('src/nexu/cinema_http_preprocess.py', '_filter_visual_css', 1, 3, 4).
python_function('src/nexu/cinema_http_preprocess.py', 'extract_visual_css', 3, 8, 12).
python_function('src/nexu/cinema_http_preprocess.py', '_script_src_allowed_for_preview', 1, 4, 4).
python_function('src/nexu/cinema_http_preprocess.py', '_should_remove_preview_script', 1, 2, 3).
python_function('src/nexu/cinema_http_preprocess.py', 'sanitize_http_preview_html', 1, 2, 4).
python_function('src/nexu/cinema_http_preprocess.py', 'inject_http_preview_shim', 1, 4, 2).
python_function('src/nexu/cinema_http_preprocess.py', 'prepare_http_preview_html', 1, 1, 2).
python_function('src/nexu/cinema_http_preprocess.py', 'build_html_outline', 1, 3, 11).
python_function('src/nexu/cinema_http_preprocess.py', '_write_preprocess_artifacts', 1, 4, 6).
python_function('src/nexu/cinema_http_preprocess.py', 'preprocess_cinema_seed', 1, 3, 3).
python_function('src/nexu/cinema_http_preprocess.py', 'http_preprocess_artifacts_present', 2, 9, 6).
python_function('src/nexu/cinema_http_preprocess.py', 'ensure_http_preprocess_artifacts', 1, 4, 3).
python_function('src/nexu/cinema_http_preprocess.py', 'preprocess_http_import', 1, 12, 8).
python_function('src/nexu/cinema_http_preprocess.py', '_project_meta_path', 2, 1, 0).
python_function('src/nexu/cinema_http_preprocess.py', 'load_cinema_seed_preprocess_artifacts', 2, 12, 9).
python_function('src/nexu/cinema_http_preprocess.py', '_load_project_meta', 1, 4, 4).
python_function('src/nexu/cinema_http_preprocess.py', 'load_http_preprocess_artifacts', 2, 16, 12).
python_function('src/nexu/cinema_http_preprocess.py', 'build_http_llm_context', 1, 7, 5).
python_function('src/nexu/cinema_http_preprocess.py', 'http_patch_llm_rules', 0, 1, 1).
python_function('src/nexu/cinema_iterate.py', 'build_iterate_response_payload', 0, 11, 6).
python_function('src/nexu/cinema_llm.py', '_cached_config', 1, 4, 4).
python_function('src/nexu/cinema_llm.py', '_litellm_completion', 0, 2, 0).
python_function('src/nexu/cinema_llm.py', '_strip_markdown_fences', 1, 8, 7).
python_function('src/nexu/cinema_llm.py', '_strip_rich_console_artifacts', 1, 7, 9).
python_function('src/nexu/cinema_llm.py', 'has_terminal_artifacts', 1, 3, 4).
python_function('src/nexu/cinema_llm.py', 'looks_like_html_document', 1, 3, 3).
python_function('src/nexu/cinema_llm.py', 'normalize_html_document', 1, 5, 9).
python_function('src/nexu/cinema_llm.py', 'extract_html_document', 1, 1, 1).
python_function('src/nexu/cinema_llm.py', 'parse_batch_alt_options', 1, 9, 11).
python_function('src/nexu/cinema_llm.py', '_as_plain_data', 1, 5, 4).
python_function('src/nexu/cinema_llm.py', '_lookup', 3, 2, 4).
python_function('src/nexu/cinema_llm.py', '_response_shape', 1, 2, 3).
python_function('src/nexu/cinema_llm.py', '_extract_parts', 1, 6, 5).
python_function('src/nexu/cinema_llm.py', '_extract_content', 1, 12, 7).
python_function('src/nexu/cinema_llm.py', 'compact_llm_error', 1, 5, 7).
python_function('src/nexu/cinema_llm.py', '_compact_response_preview', 1, 2, 3).
python_function('src/nexu/cinema_llm.py', 'call_cinema_text_llm', 2, 9, 7).
python_function('src/nexu/cinema_llm.py', 'call_cinema_html_llm', 2, 12, 7).
python_function('src/nexu/cinema_llm_contracts.py', '_slug', 1, 2, 3).
python_function('src/nexu/cinema_llm_contracts.py', '_line', 3, 4, 3).
python_function('src/nexu/cinema_llm_contracts.py', '_compact', 1, 3, 5).
python_function('src/nexu/cinema_llm_contracts.py', 'build_llm_option_variants', 0, 4, 5).
python_function('src/nexu/cinema_llm_contracts.py', '_format_contract_params', 6, 7, 3).
python_function('src/nexu/cinema_llm_contracts.py', 'build_llm_communication_contract_lines', 0, 9, 4).
python_function('src/nexu/cinema_llm_contracts.py', 'build_llm_contract_block', 0, 2, 2).
python_function('src/nexu/cinema_marked_context.py', 'has_ui_marks', 2, 8, 3).
python_function('src/nexu/cinema_marked_context.py', '_css_id_selector', 1, 4, 3).
python_function('src/nexu/cinema_marked_context.py', 'marked_css_selectors', 1, 6, 5).
python_function('src/nexu/cinema_marked_context.py', 'resolve_marked_selectors', 2, 14, 13).
python_function('src/nexu/cinema_marked_context.py', 'marked_scope_colors_css', 2, 4, 2).
python_function('src/nexu/cinema_marked_context.py', 'restrict_scope_css_to_marks', 2, 14, 11).
python_function('src/nexu/cinema_marked_context.py', '_id_candidates', 1, 4, 6).
python_function('src/nexu/cinema_marked_context.py', '_parse_attrs', 1, 3, 5).
python_function('src/nexu/cinema_marked_context.py', '_logical_id', 2, 8, 6).
python_function('src/nexu/cinema_marked_context.py', '_extract_balanced_html', 2, 10, 11).
python_function('src/nexu/cinema_marked_context.py', '_collect_match_candidates', 2, 6, 6).
python_function('src/nexu/cinema_marked_context.py', '_collect_button_candidates', 4, 3, 8).
python_function('src/nexu/cinema_marked_context.py', '_extract_and_format_fragment', 2, 3, 6).
python_function('src/nexu/cinema_marked_context.py', '_find_marked_subtrees', 2, 17, 13).
python_function('src/nexu/cinema_marked_context.py', '_selector_tokens', 1, 9, 9).
python_function('src/nexu/cinema_marked_context.py', '_filter_css_for_tokens', 2, 6, 6).
python_function('src/nexu/cinema_marked_context.py', '_collect_css_sources', 2, 7, 8).
python_function('src/nexu/cinema_marked_context.py', '_scope_semantics', 1, 4, 2).
python_function('src/nexu/cinema_marked_context.py', '_cap_text', 2, 2, 4).
python_function('src/nexu/cinema_marked_context.py', '_client_fragment_html', 2, 9, 5).
python_function('src/nexu/cinema_marked_context.py', '_assemble_marked_subtrees', 3, 4, 3).
python_function('src/nexu/cinema_marked_context.py', '_get_relevant_css', 3, 2, 6).
python_function('src/nexu/cinema_marked_context.py', '_format_context_body', 7, 14, 7).
python_function('src/nexu/cinema_marked_context.py', 'build_marked_element_context', 1, 11, 7).
python_function('src/nexu/cinema_marked_context.py', 'resolve_marked_llm_context', 1, 5, 2).
python_function('src/nexu/cinema_markpact.py', '_escape_markdown_fence', 2, 2, 1).
python_function('src/nexu/cinema_markpact.py', '_language_for', 1, 1, 2).
python_function('src/nexu/cinema_markpact.py', '_project_context_block', 1, 14, 15).
python_function('src/nexu/cinema_markpact.py', '_get_app_title', 3, 3, 3).
python_function('src/nexu/cinema_markpact.py', '_get_baseline_block', 2, 6, 3).
python_function('src/nexu/cinema_markpact.py', 'build_markpact_readme', 1, 11, 14).
python_function('src/nexu/cinema_markpact.py', 'markpact_download_filename', 2, 2, 2).
python_function('src/nexu/cinema_offline_options.py', '_btn', 2, 3, 1).
python_function('src/nexu/cinema_offline_options.py', '_keep_ids_lower', 1, 3, 1).
python_function('src/nexu/cinema_offline_options.py', '_normal_id', 1, 5, 4).
python_function('src/nexu/cinema_offline_options.py', '_delete_without_keeps', 2, 3, 2).
python_function('src/nexu/cinema_offline_options.py', '_mandatory_trig', 1, 3, 1).
python_function('src/nexu/cinema_offline_options.py', '_trig_row', 1, 7, 4).
python_function('src/nexu/cinema_offline_options.py', '_policy_constrained', 2, 2, 1).
python_function('src/nexu/cinema_offline_options.py', '_numpad_token_btn', 1, 4, 3).
python_function('src/nexu/cinema_offline_options.py', '_numpad_rows', 1, 5, 4).
python_function('src/nexu/cinema_offline_options.py', '_numpad_from_policy', 1, 12, 13).
python_function('src/nexu/cinema_offline_options.py', '_short_goal_label', 1, 3, 3).
python_function('src/nexu/cinema_offline_options.py', '_policy_screen_text', 2, 6, 5).
python_function('src/nexu/cinema_offline_options.py', '_expanded_excess_row', 1, 8, 6).
python_function('src/nexu/cinema_offline_options.py', '_chemical_shell', 0, 2, 2).
python_function('src/nexu/cinema_offline_options.py', '_active_project_meta', 1, 4, 4).
python_function('src/nexu/cinema_offline_options.py', '_active_is_imported', 1, 5, 5).
python_function('src/nexu/cinema_offline_options.py', '_cinema_is_calculator', 1, 12, 9).
python_function('src/nexu/cinema_offline_options.py', '_project_option_label', 2, 1, 2).
python_function('src/nexu/cinema_offline_options.py', '_inject_goal_banner', 3, 4, 5).
python_function('src/nexu/cinema_offline_options.py', '_write_project_options_from_stages', 1, 13, 19).
python_function('src/nexu/cinema_offline_options.py', '_write_scoped_calculator_options', 1, 11, 18).
python_function('src/nexu/cinema_offline_options.py', '_option_shell', 0, 3, 1).
python_function('src/nexu/cinema_offline_options.py', 'build_policy_scientific_option_html', 2, 3, 6).
python_function('src/nexu/cinema_offline_options.py', 'build_chemical_option_html', 2, 10, 7).
python_function('src/nexu/cinema_offline_options.py', '_render_packaged_alt', 1, 1, 5).
python_function('src/nexu/cinema_offline_options.py', '_is_dashboard_kind', 4, 5, 1).
python_function('src/nexu/cinema_offline_options.py', '_detect_project_types', 6, 11, 10).
python_function('src/nexu/cinema_offline_options.py', '_get_option_mapping', 2, 3, 0).
python_function('src/nexu/cinema_offline_options.py', '_generate_option_html', 5, 3, 3).
python_function('src/nexu/cinema_offline_options.py', '_write_option_files', 7, 3, 6).
python_function('src/nexu/cinema_offline_options.py', '_sync_stages_from_options', 2, 5, 3).
python_function('src/nexu/cinema_offline_options.py', 'write_goal_options_offline', 1, 13, 12).
python_function('src/nexu/cinema_options_cache.py', 'goal_slug', 1, 4, 4).
python_function('src/nexu/cinema_options_cache.py', '_digest', 1, 2, 4).
python_function('src/nexu/cinema_options_cache.py', 'options_cache_key', 0, 7, 11).
python_function('src/nexu/cinema_options_cache.py', 'options_cache_dir', 1, 1, 1).
python_function('src/nexu/cinema_options_cache.py', 'read_options_cache', 2, 9, 8).
python_function('src/nexu/cinema_options_cache.py', 'write_options_cache', 2, 5, 13).
python_function('src/nexu/cinema_options_cache.py', 'apply_options_cache', 2, 7, 8).
python_function('src/nexu/cinema_options_cache.py', 'invalidate_options_cache', 1, 2, 2).
python_function('src/nexu/cinema_policy.py', '_process_ledger_entry', 3, 4, 4).
python_function('src/nexu/cinema_policy.py', '_process_keep_delete_entries', 2, 7, 3).
python_function('src/nexu/cinema_policy.py', '_process_proposed_contracts', 2, 8, 3).
python_function('src/nexu/cinema_policy.py', '_build_constraint_result', 1, 5, 2).
python_function('src/nexu/cinema_policy.py', 'effective_ui_constraints_from_ledger', 1, 4, 3).
python_function('src/nexu/cinema_policy.py', 'merge_ui_constraint_lists', 0, 13, 4).
python_function('src/nexu/cinema_policy.py', '_normalize_html_body', 1, 1, 2).
python_function('src/nexu/cinema_policy.py', '_html_files_distinct', 2, 3, 6).
python_function('src/nexu/cinema_policy.py', 'option_previews_are_distinct', 1, 1, 1).
python_function('src/nexu/cinema_policy.py', 'stage_files_are_distinct', 1, 1, 1).
python_function('src/nexu/cinema_policy.py', 'ensure_option_previews_from_stages', 1, 3, 5).
python_function('src/nexu/cinema_policy.py', 'ensure_http_option_previews_from_stage0', 1, 3, 5).
python_function('src/nexu/cinema_policy.py', 'refresh_imported_policy_snapshot', 3, 5, 8).
python_function('src/nexu/cinema_policy.py', '_replace_html_title', 2, 2, 2).
python_function('src/nexu/cinema_policy.py', 'sync_option_previews_from_workspace', 1, 10, 10).
python_function('src/nexu/cinema_policy.py', 'enforce_deletes_on_option_previews', 2, 7, 11).
python_function('src/nexu/cinema_policy.py', 'reset_cinema_policy_ledger', 1, 1, 2).
python_function('src/nexu/cinema_policy.py', 'refresh_cinema_policy_snapshot', 3, 2, 4).
python_function('src/nexu/cinema_policy.py', 'load_effective_ui_constraints', 2, 3, 6).
python_function('src/nexu/cinema_policy.py', 'resolve_iteration_mode', 0, 8, 0).
python_function('src/nexu/cinema_policy.py', 'normalize_manifest_target', 1, 3, 2).
python_function('src/nexu/cinema_policy.py', 'cinema_model_label', 1, 2, 3).
python_function('src/nexu/cinema_policy.py', 'cinema_dir_for', 2, 1, 2).
python_function('src/nexu/cinema_policy.py', 'policy_snapshot_path', 2, 1, 1).
python_function('src/nexu/cinema_policy.py', 'policy_ledger_path', 2, 1, 1).
python_function('src/nexu/cinema_policy.py', 'load_policy_snapshot', 2, 2, 4).
python_function('src/nexu/cinema_policy.py', 'manifest_paths_from_snapshot', 4, 5, 5).
python_function('src/nexu/cinema_policy.py', 'apply_ledger_from_cinema', 2, 8, 11).
python_function('src/nexu/cinema_policy.py', 'ensure_intract_on_path', 1, 5, 5).
python_function('src/nexu/cinema_policy.py', 'propose_ui_delta_contract_dicts', 0, 5, 4).
python_function('src/nexu/cinema_policy.py', '_resolve_ledger_path', 2, 2, 2).
python_function('src/nexu/cinema_policy.py', 'append_policy_ledger_entry', 3, 3, 9).
python_function('src/nexu/cinema_policy.py', '_proposal_kind_and_element', 1, 12, 3).
python_function('src/nexu/cinema_policy.py', 'normalize_proposals_for_ledger', 3, 6, 7).
python_function('src/nexu/cinema_policy.py', 'append_goal_ledger_entry', 2, 7, 8).
python_function('src/nexu/cinema_policy.py', 'load_goal_contract_lines', 2, 12, 9).
python_function('src/nexu/cinema_policy.py', 'append_iteration_ledger_entry', 2, 1, 7).
python_function('src/nexu/cinema_policy.py', 'propose_llm_for_stage', 4, 8, 12).
python_function('src/nexu/cinema_policy.py', 'validate_intract_artifact', 2, 8, 4).
python_function('src/nexu/cinema_policy.py', 'verify_capsule_workspace', 2, 2, 4).
python_function('src/nexu/cinema_project_imports.py', '_slug', 1, 2, 3).
python_function('src/nexu/cinema_project_imports.py', '_imports_root', 1, 1, 1).
python_function('src/nexu/cinema_project_imports.py', '_project_dir', 2, 1, 1).
python_function('src/nexu/cinema_project_imports.py', '_validate_http_url', 1, 3, 2).
python_function('src/nexu/cinema_project_imports.py', '_validate_git_url', 1, 5, 4).
python_function('src/nexu/cinema_project_imports.py', '_safe_extract_zip', 2, 6, 10).
python_function('src/nexu/cinema_project_imports.py', '_charset_from_content_type', 1, 3, 4).
python_function('src/nexu/cinema_project_imports.py', '_decode_http_bytes', 1, 4, 2).
python_function('src/nexu/cinema_project_imports.py', '_document_base_href', 1, 4, 4).
python_function('src/nexu/cinema_project_imports.py', '_fetch_http_body', 1, 7, 13).
python_function('src/nexu/cinema_project_imports.py', '_same_origin', 2, 2, 1).
python_function('src/nexu/cinema_project_imports.py', '_extract_stylesheet_hrefs', 1, 5, 6).
python_function('src/nexu/cinema_project_imports.py', '_fetch_http_stylesheets', 1, 6, 9).
python_function('src/nexu/cinema_project_imports.py', '_rewrite_local_stylesheets', 1, 3, 6).
python_function('src/nexu/cinema_project_imports.py', '_inject_base_href', 2, 4, 2).
python_function('src/nexu/cinema_project_imports.py', '_find_http_index_path', 1, 6, 4).
python_function('src/nexu/cinema_project_imports.py', '_load_http_fetch_meta', 1, 4, 4).
python_function('src/nexu/cinema_project_imports.py', '_build_http_preview_stage0', 1, 14, 16).
python_function('src/nexu/cinema_project_imports.py', '_iter_project_files', 1, 5, 6).
python_function('src/nexu/cinema_project_imports.py', '_detect_run_notes', 1, 5, 2).
python_function('src/nexu/cinema_project_imports.py', '_read_text_for_markpact', 1, 3, 2).
python_function('src/nexu/cinema_project_imports.py', '_build_markpact_migration', 1, 8, 11).
python_function('src/nexu/cinema_project_imports.py', '_stage_html', 1, 5, 3).
python_function('src/nexu/cinema_project_imports.py', '_apply_http_preprocess_fields', 2, 9, 6).
python_function('src/nexu/cinema_project_imports.py', '_refresh_http_preprocess_if_needed', 2, 6, 10).
python_function('src/nexu/cinema_project_imports.py', '_activate_imported', 2, 11, 19).
python_function('src/nexu/cinema_project_imports.py', 'import_git_project', 2, 11, 13).
python_function('src/nexu/cinema_project_imports.py', 'import_http_project', 2, 7, 17).
python_function('src/nexu/cinema_project_imports.py', 'import_zip_project', 3, 5, 11).
python_function('src/nexu/cinema_project_imports.py', '_import_kind_from_id', 1, 4, 1).
python_function('src/nexu/cinema_project_imports.py', '_project_title_from_id', 1, 3, 4).
python_function('src/nexu/cinema_project_imports.py', '_finish_import', 1, 8, 20).
python_function('src/nexu/cinema_project_imports.py', '_infer_workspace_context', 1, 4, 5).
python_function('src/nexu/cinema_project_imports.py', '_source_stats', 1, 4, 3).
python_function('src/nexu/cinema_project_imports.py', '_source_url_from_meta', 1, 6, 4).
python_function('src/nexu/cinema_project_imports.py', 'normalize_imported_project_id', 1, 2, 3).
python_function('src/nexu/cinema_project_imports.py', 'is_deletable_imported_id', 1, 2, 4).
python_function('src/nexu/cinema_project_imports.py', '_compile_meta_fields', 2, 17, 9).
python_function('src/nexu/cinema_project_imports.py', '_ensure_project_meta_fields', 2, 5, 6).
python_function('src/nexu/cinema_project_imports.py', '_catalog_entry_from_meta', 2, 7, 6).
python_function('src/nexu/cinema_project_imports.py', '_filter_traces_for_project', 1, 11, 3).
python_function('src/nexu/cinema_project_imports.py', 'read_imported_markpact', 2, 9, 11).
python_function('src/nexu/cinema_project_imports.py', 'imported_project_llm_log', 3, 8, 12).
python_function('src/nexu/cinema_project_imports.py', '_verify_delete_paths', 2, 5, 4).
python_function('src/nexu/cinema_project_imports.py', '_activate_delete_fallback', 5, 3, 5).
python_function('src/nexu/cinema_project_imports.py', '_clear_active_project', 1, 2, 2).
python_function('src/nexu/cinema_project_imports.py', '_delete_active_project_fallback', 5, 5, 2).
python_function('src/nexu/cinema_project_imports.py', 'delete_imported_project', 2, 7, 12).
python_function('src/nexu/cinema_project_imports.py', 'delete_project', 2, 3, 6).
python_function('src/nexu/cinema_project_imports.py', 'list_imported_projects', 1, 6, 10).
python_function('src/nexu/cinema_project_imports.py', 'merged_projects_catalog', 1, 10, 6).
python_function('src/nexu/cinema_project_imports.py', 'activate_imported_project', 2, 4, 6).
python_function('src/nexu/cinema_project_ir.py', '_clean_text', 1, 2, 3).
python_function('src/nexu/cinema_project_ir.py', 'build_project_ir', 1, 2, 5).
python_function('src/nexu/cinema_project_ir.py', 'summarize_project_ir', 1, 12, 7).
python_function('src/nexu/cinema_projects.py', 'find_nexu_repo_root', 1, 5, 3).
python_function('src/nexu/cinema_projects.py', 'deleted_project_ids', 1, 7, 8).
python_function('src/nexu/cinema_projects.py', 'mark_project_deleted', 2, 1, 6).
python_function('src/nexu/cinema_projects.py', 'is_example_project_id', 1, 2, 1).
python_function('src/nexu/cinema_projects.py', '_project_catalog_entry', 2, 2, 2).
python_function('src/nexu/cinema_projects.py', '_catalog_filters', 1, 14, 3).
python_function('src/nexu/cinema_projects.py', 'list_project_catalog', 1, 3, 3).
python_function('src/nexu/cinema_projects.py', 'delete_example_project', 2, 14, 11).
python_function('src/nexu/cinema_projects.py', '_resolve_source_cinema', 2, 5, 2).
python_function('src/nexu/cinema_projects.py', '_project_widgets', 1, 1, 1).
python_function('src/nexu/cinema_projects.py', '_seed_html_for_project', 2, 9, 8).
python_function('src/nexu/cinema_projects.py', '_copy_cinema_files', 2, 4, 4).
python_function('src/nexu/cinema_projects.py', '_write_seed_variants', 2, 2, 4).
python_function('src/nexu/cinema_projects.py', '_find_example_project', 1, 3, 1).
python_function('src/nexu/cinema_projects.py', '_active_project_meta', 1, 1, 2).
python_function('src/nexu/cinema_projects.py', '_write_active_project_meta', 2, 1, 2).
python_function('src/nexu/cinema_projects.py', '_resolve_root_for_project_source', 3, 3, 1).
python_function('src/nexu/cinema_projects.py', '_copy_or_seed_project_files', 3, 3, 2).
python_function('src/nexu/cinema_projects.py', '_sync_project_options', 2, 5, 3).
python_function('src/nexu/cinema_projects.py', '_apply_preprocess_meta', 3, 3, 5).
python_function('src/nexu/cinema_projects.py', '_bootstrap_goal_from_project', 4, 4, 4).
python_function('src/nexu/cinema_projects.py', '_init_project_activation', 4, 3, 4).
python_function('src/nexu/cinema_projects.py', 'activate_example_project', 2, 2, 13).
python_function('src/nexu/cinema_projects.py', 'load_active_project', 1, 4, 4).
python_function('src/nexu/cinema_publish.py', 'services_root', 1, 1, 0).
python_function('src/nexu/cinema_publish.py', '_registry_path', 1, 1, 1).
python_function('src/nexu/cinema_publish.py', '_load_registry', 1, 3, 6).
python_function('src/nexu/cinema_publish.py', '_save_registry', 2, 1, 5).
python_function('src/nexu/cinema_publish.py', '_slug_service_id', 3, 4, 2).
python_function('src/nexu/cinema_publish.py', '_pick_port', 1, 4, 2).
python_function('src/nexu/cinema_publish.py', '_port_open', 1, 2, 1).
python_function('src/nexu/cinema_publish.py', '_http_ok', 1, 2, 1).
python_function('src/nexu/cinema_publish.py', '_service_alive', 1, 6, 5).
python_function('src/nexu/cinema_publish.py', '_refresh_service_status', 1, 3, 1).
python_function('src/nexu/cinema_publish.py', 'list_published_services', 1, 3, 6).
python_function('src/nexu/cinema_publish.py', '_write_service_readme', 1, 14, 13).
python_function('src/nexu/cinema_publish.py', '_prepare_service_directory', 3, 1, 4).
python_function('src/nexu/cinema_publish.py', '_generate_markpact_export', 6, 1, 5).
python_function('src/nexu/cinema_publish.py', '_allocate_service_port', 2, 11, 6).
python_function('src/nexu/cinema_publish.py', '_create_service_entry', 6, 3, 2).
python_function('src/nexu/cinema_publish.py', '_register_service', 2, 4, 5).
python_function('src/nexu/cinema_publish.py', '_handle_existing_service', 2, 7, 6).
python_function('src/nexu/cinema_publish.py', 'publish_project_service', 3, 6, 15).
python_function('src/nexu/cinema_publish.py', '_spawn_http_server', 2, 1, 4).
python_function('src/nexu/cinema_publish.py', '_wait_for_service_running', 2, 3, 5).
python_function('src/nexu/cinema_publish.py', 'start_published_service', 2, 15, 14).
python_function('src/nexu/cinema_publish.py', 'stop_published_service', 2, 9, 8).
python_function('src/nexu/cinema_scope.py', 'ui_type_for_kind', 1, 11, 3).
python_function('src/nexu/cinema_scope.py', 'allowed_scope_ids', 1, 2, 3).
python_function('src/nexu/cinema_scope.py', 'default_scope_for_kind', 1, 3, 4).
python_function('src/nexu/cinema_scope.py', 'normalize_focus_scope', 2, 3, 5).
python_function('src/nexu/cinema_scope.py', 'offline_fast_scopes_for_kind', 1, 5, 2).
python_function('src/nexu/cinema_scope.py', 'scope_supports_offline_fast_path', 2, 1, 2).
python_function('src/nexu/cinema_scope.py', 'cinema_has_offline_baseline', 1, 4, 6).
python_function('src/nexu/cinema_scope.py', 'scope_option_variants', 3, 11, 1).
python_function('src/nexu/cinema_scope.py', 'strip_scope_style', 1, 2, 1).
python_function('src/nexu/cinema_scope.py', '_scope_css', 2, 6, 0).
python_function('src/nexu/cinema_scope.py', '_calc_scope_css', 2, 7, 0).
python_function('src/nexu/cinema_scope.py', '_web_scope_css', 2, 6, 0).
python_function('src/nexu/cinema_scope.py', '_resolve_scope_kind', 2, 10, 2).
python_function('src/nexu/cinema_scope.py', 'should_block_full_html_iterate', 3, 3, 3).
python_function('src/nexu/cinema_scope.py', '_bind_annotations_to_html', 3, 29, 18).
python_function('src/nexu/cinema_scope.py', '_get_scope_css', 4, 7, 5).
python_function('src/nexu/cinema_scope.py', '_inject_css_block', 2, 5, 4).
python_function('src/nexu/cinema_scope.py', 'inject_scope_style', 3, 14, 11).
python_function('src/nexu/cinema_scope.py', 'scoped_html_fragment', 3, 6, 6).
python_function('src/nexu/cinema_scope.py', 'scope_meta_for_project', 1, 1, 3).
python_function('src/nexu/cinema_scope.py', 'load_cinema_ui_profile', 2, 10, 12).
python_function('src/nexu/cinema_scope.py', 'can_use_offline_fast_iterate', 3, 4, 2).
python_function('src/nexu/cinema_scripts.py', '_delete_match_keys', 1, 4, 5).
python_function('src/nexu/cinema_scripts.py', '_selectable_block_attrs', 1, 4, 3).
python_function('src/nexu/cinema_scripts.py', '_element_delete_candidates', 2, 6, 6).
python_function('src/nexu/cinema_scripts.py', 'apply_spatial_deletes_to_html', 2, 4, 11).
python_function('src/nexu/cinema_scripts.py', 'inject_cinema_shield', 1, 6, 3).
python_function('src/nexu/cinema_scripts.py', 'finalize_cinema_html', 1, 6, 5).
python_function('src/nexu/cinema_scripts.py', 'write_cinema_inject_files', 1, 1, 2).
python_function('src/nexu/cinema_scripts.py', 'repair_cinema_html_files', 1, 5, 8).
python_function('src/nexu/cinema_server.py', '_template_text', 0, 1, 3).
python_function('src/nexu/cinema_server.py', '_render_server_script', 5, 1, 8).
python_function('src/nexu/cinema_server.py', '_litellm_available', 1, 1, 1).
python_function('src/nexu/cinema_server.py', '_try_spawn_on_port', 3, 2, 4).
python_function('src/nexu/cinema_server.py', '_available_port', 2, 4, 7).
python_function('src/nexu/cinema_server.py', 'start_persistent_http_server', 3, 2, 7).
python_function('src/nexu/cinema_server.py', '_open_browser', 1, 3, 2).
python_function('src/nexu/cinema_server.py', 'start_cinema_player_server', 3, 2, 4).
python_function('src/nexu/cinema_traces.py', 'redact_secrets', 1, 9, 5).
python_function('src/nexu/cinema_traces.py', 'trace_slug', 1, 3, 3).
python_function('src/nexu/cinema_traces.py', 'text_metrics', 1, 3, 4).
python_function('src/nexu/cinema_traces.py', 'read_trace_index', 1, 3, 3).
python_function('src/nexu/cinema_traces.py', 'write_llm_trace', 3, 8, 13).
python_function('src/nexu/cinema_traces.py', 'list_llm_traces', 1, 1, 2).
python_function('src/nexu/cinema_traces.py', 'read_llm_trace', 2, 2, 5).
python_function('src/nexu/cinema_ui_patch.py', 'supports_llm_patch_scope', 2, 3, 1).
python_function('src/nexu/cinema_ui_patch.py', '_compact_html', 1, 3, 4).
python_function('src/nexu/cinema_ui_patch.py', '_patch_scope_rules', 1, 7, 4).
python_function('src/nexu/cinema_ui_patch.py', 'build_ui_patch_prompt', 1, 9, 5).
python_function('src/nexu/cinema_ui_patch.py', '_strip_json_fence', 1, 3, 4).
python_function('src/nexu/cinema_ui_patch.py', 'parse_ui_patch_response', 1, 6, 7).
python_function('src/nexu/cinema_ui_patch.py', '_safe_css', 1, 9, 7).
python_function('src/nexu/cinema_ui_patch.py', '_label_for', 3, 4, 4).
python_function('src/nexu/cinema_ui_patch.py', '_css_for', 1, 2, 3).
python_function('src/nexu/cinema_ui_patch.py', 'apply_ui_patch_options', 2, 25, 19).
python_function('src/nexu/cli.py', '_print_yaml', 1, 1, 3).
python_function('src/nexu/cli.py', '_relative_to_root', 2, 1, 2).
python_function('src/nexu/cli.py', 'init', 1, 3, 6).
python_function('src/nexu/cli.py', 'freeze', 3, 2, 7).
python_function('src/nexu/cli.py', 'capsule_create', 7, 1, 8).
python_function('src/nexu/cli.py', 'capsule_list', 1, 3, 7).
python_function('src/nexu/cli.py', 'capsule_status_command', 2, 3, 11).
python_function('src/nexu/cli.py', 'capsule_iterate', 5, 2, 10).
python_function('src/nexu/cli.py', 'capsule_blueprint', 3, 2, 7).
python_function('src/nexu/cli.py', 'capsule_export_prompt', 3, 1, 7).
python_function('src/nexu/cli.py', 'capsule_diff', 2, 1, 10).
python_function('src/nexu/cli.py', 'capsule_drift', 2, 2, 7).
python_function('src/nexu/cli.py', 'capsule_verify', 2, 4, 8).
python_function('src/nexu/cli.py', 'capsule_plan', 5, 2, 8).
python_function('src/nexu/cli.py', 'capsule_runtime', 2, 1, 7).
python_function('src/nexu/cli.py', 'capsule_report', 2, 1, 7).
python_function('src/nexu/cli.py', 'capsule_journal', 3, 2, 10).
python_function('src/nexu/cli.py', 'capsule_orchestrate', 6, 1, 7).
python_function('src/nexu/cli.py', 'capsule_review', 5, 1, 7).
python_function('src/nexu/cli.py', 'capsule_bundle', 3, 1, 7).
python_function('src/nexu/cli.py', 'capsule_promote', 3, 3, 10).
python_function('src/nexu/cli.py', 'mcp_tools', 0, 2, 6).
python_function('src/nexu/cli.py', 'mcp_serve', 2, 2, 5).
python_function('src/nexu/config.py', '_as_list', 2, 4, 2).
python_function('src/nexu/config.py', '_load_env_file', 1, 10, 7).
python_function('src/nexu/config.py', 'load_env_files', 1, 3, 3).
python_function('src/nexu/config.py', '_resolved_model_from_env', 1, 5, 1).
python_function('src/nexu/config.py', '_cinema_mode', 2, 4, 2).
python_function('src/nexu/config.py', 'load_config', 1, 14, 18).
python_function('src/nexu/diff.py', 'diff_capsule', 2, 12, 10).
python_function('src/nexu/drift.py', 'check_source_drift', 2, 7, 9).
python_function('src/nexu/export_prompt.py', '_cinema_policy_ledger_block', 1, 12, 7).
python_function('src/nexu/export_prompt.py', '_latest_iteration', 1, 2, 0).
python_function('src/nexu/export_prompt.py', 'export_iteration_prompt', 2, 3, 15).
python_function('src/nexu/fast_delivery/context.py', 'compact_html_for_llm', 1, 3, 5).
python_function('src/nexu/fast_delivery/context.py', 'effective_markpact_mode', 2, 8, 3).
python_function('src/nexu/fast_delivery/context.py', 'compact_markpact_for_llm', 1, 9, 11).
python_function('src/nexu/fast_delivery/options.py', '_looks_like_calculator', 1, 4, 2).
python_function('src/nexu/fast_delivery/options.py', '_compatible_with_stage', 2, 5, 3).
python_function('src/nexu/fast_delivery/options.py', 'read_cached_options', 0, 11, 13).
python_function('src/nexu/fast_delivery/options.py', 'store_options_cache', 0, 3, 3).
python_function('src/nexu/fast_delivery/options.py', 'read_option_files', 1, 3, 3).
python_function('src/nexu/fast_delivery/router.py', 'choose_options_route', 0, 9, 3).
python_function('src/nexu/fast_delivery/router.py', 'is_options_ready_status', 1, 2, 1).
python_function('src/nexu/fast_delivery/router.py', 'options_source_label', 1, 5, 1).
python_function('src/nexu/files.py', 'rel', 2, 1, 2).
python_function('src/nexu/files.py', 'matches_any', 2, 3, 3).
python_function('src/nexu/files.py', 'is_text_file', 1, 2, 1).
python_function('src/nexu/files.py', 'collect_files', 3, 8, 7).
python_function('src/nexu/freeze.py', 'freeze_project', 3, 2, 12).
python_function('src/nexu/git.py', 'current_git_sha', 1, 4, 3).
python_function('src/nexu/hashing.py', 'sha256_file', 1, 2, 6).
python_function('src/nexu/hashing.py', 'sha256_text', 1, 1, 3).
python_function('src/nexu/init_project.py', 'init_project', 1, 3, 4).
python_function('src/nexu/intract.py', 'format_intract_v1_line', 1, 3, 1).
python_function('src/nexu/intract.py', '_split_csv', 1, 4, 3).
python_function('src/nexu/intract.py', '_tokenize_contract', 1, 5, 6).
python_function('src/nexu/intract.py', 'parse_intract_line', 1, 3, 6).
python_function('src/nexu/intract.py', 'scan_contracts_in_text', 1, 3, 4).
python_function('src/nexu/intract.py', 'scan_contracts_in_file', 2, 3, 4).
python_function('src/nexu/intract.py', 'read_manifest_contracts', 1, 12, 9).
python_function('src/nexu/intract_adapter.py', '_sibling_intract_src', 1, 4, 3).
python_function('src/nexu/intract_adapter.py', '_ensure_intract_on_path', 1, 3, 3).
python_function('src/nexu/intract_adapter.py', '_result_status', 1, 1, 2).
python_function('src/nexu/intract_adapter.py', '_finding_for_result', 1, 9, 8).
python_function('src/nexu/intract_adapter.py', '_policy_findings', 1, 3, 2).
python_function('src/nexu/intract_adapter.py', 'check_intract_policy', 4, 7, 10).
python_function('src/nexu/iterate.py', 'iterate_capsule', 2, 7, 13).
python_function('src/nexu/journal.py', 'journal_path', 2, 1, 1).
python_function('src/nexu/journal.py', 'read_journal', 2, 5, 5).
python_function('src/nexu/journal.py', 'append_journal', 4, 2, 6).
python_function('src/nexu/llm.py', '_extract_content', 1, 4, 3).
python_function('src/nexu/llm.py', '_strip_fences', 1, 7, 4).
python_function('src/nexu/llm.py', 'call_litellm_json', 1, 8, 8).
python_function('src/nexu/llm.py', 'offline_review_from_status', 2, 4, 0).
python_function('src/nexu/llm.py', 'call_litellm_review', 1, 2, 2).
python_function('src/nexu/mcp_server.py', '_schema', 2, 2, 0).
python_function('src/nexu/mcp_server.py', '_apply_promotion_from_mcp', 2, 1, 2).
python_function('src/nexu/mcp_server.py', '_tool_map', 1, 2, 2).
python_function('src/nexu/mcp_server.py', 'call_tool', 3, 3, 2).
python_function('src/nexu/mcp_server.py', '_result_content', 1, 1, 1).
python_function('src/nexu/mcp_server.py', '_resource_list', 1, 2, 2).
python_function('src/nexu/mcp_server.py', '_read_resource', 2, 6, 9).
python_function('src/nexu/mcp_server.py', '_prompts_list', 0, 1, 0).
python_function('src/nexu/mcp_server.py', '_prompt_get', 2, 3, 2).
python_function('src/nexu/mcp_server.py', '_rpc_initialize', 1, 1, 1).
python_function('src/nexu/mcp_server.py', '_rpc_handlers', 1, 3, 9).
python_function('src/nexu/mcp_server.py', 'handle_mcp_message', 2, 5, 4).
python_function('src/nexu/mcp_server.py', 'run_mcp_stdio', 1, 6, 7).
python_function('src/nexu/models.py', 'utc_now', 0, 1, 2).
python_function('src/nexu/models.py', 'write_yaml', 2, 1, 3).
python_function('src/nexu/models.py', 'read_yaml', 1, 3, 4).
python_function('src/nexu/orchestrate.py', '_contract_dicts', 1, 2, 0).
python_function('src/nexu/orchestrate.py', 'build_orchestration_context', 2, 2, 9).
python_function('src/nexu/orchestrate.py', 'build_orchestration_prompt', 1, 1, 1).
python_function('src/nexu/orchestrate.py', 'offline_orchestration_from_context', 1, 13, 6).
python_function('src/nexu/orchestrate.py', 'build_capsule_orchestration', 2, 2, 16).
python_function('src/nexu/orchestrate.py', '_render_orchestration_markdown', 1, 9, 4).
python_function('src/nexu/paths.py', 'project_root', 1, 1, 3).
python_function('src/nexu/paths.py', 'nexu_dir', 1, 1, 0).
python_function('src/nexu/paths.py', 'snapshots_dir', 1, 1, 1).
python_function('src/nexu/paths.py', 'capsules_dir', 1, 1, 1).
python_function('src/nexu/paths.py', 'capsule_dir', 2, 1, 1).
python_function('src/nexu/paths.py', 'ensure_project_dirs', 1, 2, 4).
python_function('src/nexu/plan.py', '_contract_summary', 1, 9, 1).
python_function('src/nexu/plan.py', 'build_iteration_plan', 2, 7, 15).
python_function('src/nexu/promote.py', '_promotion_map', 3, 2, 3).
python_function('src/nexu/promote.py', 'build_promotion_plan', 2, 6, 14).
python_function('src/nexu/promote.py', 'apply_promotion_plan', 2, 4, 7).
python_function('src/nexu/report.py', '_finding_table', 1, 2, 5).
python_function('src/nexu/report.py', '_html_from_markdownish', 2, 1, 1).
python_function('src/nexu/report.py', 'build_capsule_report', 2, 1, 18).
python_function('src/nexu/review.py', '_markdown_review_prompt', 1, 1, 1).
python_function('src/nexu/review.py', 'build_review_packet', 2, 5, 19).
python_function('src/nexu/runtime.py', '_read_fixture', 1, 5, 5).
python_function('src/nexu/runtime.py', '_collect_fixtures', 1, 5, 7).
python_function('src/nexu/runtime.py', '_html_page', 2, 9, 5).
python_function('src/nexu/runtime.py', 'build_capsule_runtime', 2, 3, 13).
python_function('src/nexu/status.py', 'capsule_status', 2, 3, 6).
python_function('src/nexu/verify.py', '_scan_capsule_contracts', 2, 2, 4).
python_function('src/nexu/verify.py', '_text', 1, 2, 1).
python_function('src/nexu/verify.py', '_contains_patterns', 2, 3, 2).
python_function('src/nexu/verify.py', '_find_term_evidence', 3, 6, 8).
python_function('src/nexu/verify.py', '_check_contracts_presence', 1, 4, 2).
python_function('src/nexu/verify.py', '_check_source_files_presence', 2, 3, 3).
python_function('src/nexu/verify.py', '_check_baseline_lock', 3, 2, 3).
python_function('src/nexu/verify.py', '_check_forbidden_write', 2, 6, 4).
python_function('src/nexu/verify.py', '_check_forbidden_secret', 2, 7, 4).
python_function('src/nexu/verify.py', '_check_output_presence', 3, 12, 5).
python_function('src/nexu/verify.py', '_check_required_intents', 1, 12, 2).
python_function('src/nexu/verify.py', '_check_iteration_count', 1, 2, 2).
python_function('src/nexu/verify.py', '_summary_status', 1, 5, 5).
python_function('src/nexu/verify.py', 'verify_capsule', 2, 1, 18).
python_function('tests/conftest.py', '_prepend_intract_src', 0, 4, 5).
python_function('tests/test_capsule_flow.py', 'test_capsule_flow', 1, 5, 7).
python_function('tests/test_capsule_next_stage.py', 'test_capsule_blueprint_prompt_diff_status_and_drift', 1, 11, 14).
python_function('tests/test_capsule_runtime_report.py', 'test_plan_runtime_report_and_journal', 1, 13, 13).
python_function('tests/test_cinema_baseline_contracts.py', 'test_calculator_baseline_contracts_count', 0, 6, 2).
python_function('tests/test_cinema_baseline_contracts.py', 'test_is_calculator_capsule_by_name', 1, 2, 3).
python_function('tests/test_cinema_baseline_contracts.py', 'test_ensure_capsule_intract_yaml_writes', 1, 4, 4).
python_function('tests/test_cinema_baseline_contracts.py', 'test_snapshot_includes_calculator_baselines', 1, 3, 3).
python_function('tests/test_cinema_baseline_contracts.py', 'test_merge_does_not_duplicate', 1, 2, 2).
python_function('tests/test_cinema_dom_patch.py', 'test_build_function_option_patches_returns_valid_abc', 0, 7, 3).
python_function('tests/test_cinema_dom_patch.py', 'test_build_function_option_patches_applies_delete_marks', 0, 5, 3).
python_function('tests/test_cinema_dom_patch.py', 'test_function_patch_context_is_compact_ir', 0, 4, 1).
python_function('tests/test_cinema_dom_patch.py', 'test_supports_function_patch_only_for_web_like_projects', 0, 5, 1).
python_function('tests/test_cinema_goal_contracts.py', 'test_propose_goal_extension_has_baseline_require', 0, 8, 3).
python_function('tests/test_cinema_goal_contracts.py', 'test_goal_ledger_roundtrip', 1, 5, 6).
python_function('tests/test_cinema_goal_contracts.py', 'test_goal_ledger_stores_scope_contract_context', 1, 6, 4).
python_function('tests/test_cinema_goal_contracts.py', 'test_goal_traits_from_contract_lines', 0, 5, 3).
python_function('tests/test_cinema_goal_contracts.py', 'test_funnels_cohorts_goal_gets_dashboard_trait', 0, 3, 2).
python_function('tests/test_cinema_goal_contracts.py', 'test_api_routes_goal_gets_api_trait_and_template_anchor', 0, 7, 4).
python_function('tests/test_cinema_goal_contracts.py', 'test_offline_project_options_show_goal_banner', 1, 5, 4).
python_function('tests/test_cinema_history.py', 'test_save_list_and_restore_files', 2, 7, 9).
python_function('tests/test_cinema_html_validate.py', 'test_repair_adds_missing_head_and_doctype', 0, 4, 4).
python_function('tests/test_cinema_html_validate.py', 'test_relocate_style_tags_to_head', 0, 5, 3).
python_function('tests/test_cinema_html_validate.py', 'test_validate_calculator_requires_screen_and_buttons', 0, 4, 3).
python_function('tests/test_cinema_html_validate.py', 'test_prepare_rejects_non_html', 0, 4, 1).
python_function('tests/test_cinema_html_validate.py', 'test_filter_valid_option_batch_requires_all_three', 0, 5, 4).
python_function('tests/test_cinema_html_validate.py', 'test_validate_css_safety_rejects_flow_breaking_layout_css', 0, 4, 2).
python_function('tests/test_cinema_html_validate.py', 'test_validate_css_safety_allows_runtime_overlay_css', 0, 2, 1).
python_function('tests/test_cinema_html_validate.py', 'test_html_validation_rejects_generated_absolute_layout', 0, 3, 3).
python_function('tests/test_cinema_http_preprocess.py', 'test_extract_visual_css_keeps_color_and_shape_rules', 1, 8, 3).
python_function('tests/test_cinema_http_preprocess.py', 'test_build_html_outline_smaller_than_source_and_strips_scripts', 0, 7, 3).
python_function('tests/test_cinema_http_preprocess.py', 'test_preprocess_cinema_seed_writes_artifacts_beside_stage0', 1, 7, 4).
python_function('tests/test_cinema_http_preprocess.py', 'test_load_cinema_ui_profile_includes_seed_preprocess', 1, 5, 5).
python_function('tests/test_cinema_http_preprocess.py', 'test_load_cinema_seed_preprocess_artifacts_reads_active_metadata', 1, 4, 4).
python_function('tests/test_cinema_http_preprocess.py', 'test_preprocess_http_import_writes_artifacts', 1, 7, 6).
python_function('tests/test_cinema_http_preprocess.py', 'test_http_preprocess_artifacts_present_requires_files_and_patch_mode', 1, 4, 5).
python_function('tests/test_cinema_http_preprocess.py', 'test_ensure_http_preprocess_artifacts_skips_when_present', 1, 2, 4).
python_function('tests/test_cinema_http_preprocess.py', 'test_ensure_http_preprocess_artifacts_regenerates_when_missing', 1, 4, 6).
python_function('tests/test_cinema_http_preprocess.py', 'test_build_http_llm_context_combines_css_and_outline', 0, 4, 2).
python_function('tests/test_cinema_http_preprocess.py', 'test_load_cinema_ui_profile_includes_http_preprocess', 1, 5, 5).
python_function('tests/test_cinema_http_preprocess.py', 'test_extract_visual_css_rejects_paths_outside_source_dir', 1, 2, 3).
python_function('tests/test_cinema_http_preprocess.py', 'test_sanitize_http_preview_strips_external_and_fetch_scripts', 0, 8, 1).
python_function('tests/test_cinema_http_preprocess.py', 'test_prepare_http_preview_injects_network_shim', 0, 5, 3).
python_function('tests/test_cinema_http_preprocess.py', 'test_prepare_http_preview_with_shield_keeps_network_shim', 0, 5, 3).
python_function('tests/test_cinema_iterate.py', 'test_build_iterate_response_payload_offline_shape', 0, 11, 2).
python_function('tests/test_cinema_iterate.py', 'test_build_iterate_response_payload_functions_llm_failed_hint', 0, 6, 3).
python_function('tests/test_cinema_iterate.py', 'test_build_iterate_response_payload_defaults_scope_label', 0, 4, 1).
python_function('tests/test_cinema_llm.py', 'test_extract_html_document_from_fences', 0, 2, 1).
python_function('tests/test_cinema_llm.py', 'test_extract_html_document_strips_rich_terminal_frame', 0, 4, 2).
python_function('tests/test_cinema_llm.py', 'test_normalize_html_document_without_doctype', 0, 3, 2).
python_function('tests/test_cinema_llm.py', 'test_normalize_html_document_closes_partial_html', 0, 3, 4).
python_function('tests/test_cinema_llm.py', 'test_call_cinema_html_llm_rejects_invalid_structure', 2, 4, 4).
python_function('tests/test_cinema_llm.py', 'test_parse_batch_alt_options_skips_invalid_calculator_html', 0, 2, 1).
python_function('tests/test_cinema_llm.py', 'test_parse_batch_alt_options_repairs_missing_head', 0, 4, 5).
python_function('tests/test_cinema_llm.py', 'test_parse_batch_alt_options_flexible_markers_web', 0, 5, 3).
python_function('tests/test_cinema_llm.py', 'test_call_cinema_html_llm_accepts_html_without_doctype', 2, 5, 6).
python_function('tests/test_cinema_llm.py', 'test_has_terminal_artifacts_detects_box_drawing', 0, 3, 1).
python_function('tests/test_cinema_llm.py', 'test_extract_content_supports_choice_text_fallback', 0, 2, 2).
python_function('tests/test_cinema_llm.py', 'test_extract_content_error_includes_response_shape', 0, 5, 3).
python_function('tests/test_cinema_llm.py', 'test_compact_llm_error_openrouter_payload', 0, 2, 1).
python_function('tests/test_cinema_llm.py', 'test_call_cinema_html_llm_blocks_when_network_disabled', 1, 3, 2).
python_function('tests/test_cinema_llm.py', 'test_call_cinema_html_llm_requires_api_key', 2, 3, 3).
python_function('tests/test_cinema_llm.py', 'test_call_cinema_html_llm_uses_litellm', 2, 6, 5).
python_function('tests/test_cinema_llm.py', 'test_call_cinema_html_llm_uses_nexu_yaml_default_model', 2, 4, 5).
python_function('tests/test_cinema_llm.py', 'test_call_cinema_text_llm_returns_raw_content', 2, 3, 4).
python_function('tests/test_cinema_llm.py', 'test_call_cinema_html_llm_error_includes_non_html_preview', 2, 4, 4).
python_function('tests/test_cinema_llm_contracts.py', 'test_calculator_llm_contract_protects_screen', 0, 5, 2).
python_function('tests/test_cinema_llm_contracts.py', 'test_llm_contract_block_tracks_scope_and_policy', 0, 9, 1).
python_function('tests/test_cinema_llm_contracts.py', 'test_llm_option_variants_are_scope_contracts_not_domain_templates', 0, 9, 3).
python_function('tests/test_cinema_marked_context.py', 'test_build_marked_element_context_extracts_subtree_and_css', 0, 9, 1).
python_function('tests/test_cinema_marked_context.py', 'test_build_marked_element_context_uses_client_fragment_fallback', 0, 3, 1).
python_function('tests/test_cinema_marked_context.py', 'test_build_marked_element_context_returns_none_without_marks', 0, 2, 1).
python_function('tests/test_cinema_marked_context.py', 'test_build_marked_element_context_patch_mode_note', 0, 4, 1).
python_function('tests/test_cinema_marked_context.py', 'test_ui_patch_prompt_uses_marked_context_fragment', 0, 5, 2).
python_function('tests/test_cinema_marked_context.py', 'test_has_ui_marks', 0, 5, 1).
python_function('tests/test_cinema_marked_context.py', 'test_restrict_scope_css_to_marks_targets_delete_only', 0, 4, 1).
python_function('tests/test_cinema_marked_context.py', 'test_inject_scope_style_skips_global_css_for_keep_only_marks', 0, 2, 1).
python_function('tests/test_cinema_marked_context.py', 'test_inject_scope_style_scopes_css_to_delete_marks', 0, 5, 1).
python_function('tests/test_cinema_marked_context.py', 'test_resolve_marked_selectors_includes_classes', 0, 5, 3).
python_function('tests/test_cinema_marked_context.py', 'test_marked_scope_colors_css_differs_by_variant', 0, 4, 1).
python_function('tests/test_cinema_marked_context.py', 'test_should_block_full_html_for_imported_marks', 0, 5, 1).
python_function('tests/test_cinema_marked_context.py', 'test_marked_css_selectors_includes_btn_prefix', 0, 3, 1).
python_function('tests/test_cinema_markpact.py', 'test_build_markpact_readme', 1, 10, 3).
python_function('tests/test_cinema_markpact.py', 'test_markpact_download_filename', 0, 2, 1).
python_function('tests/test_cinema_offline_options.py', 'test_is_chemical_goal', 0, 4, 1).
python_function('tests/test_cinema_offline_options.py', 'test_write_chemical_options', 1, 5, 3).
python_function('tests/test_cinema_offline_options.py', 'test_calculator_chemical_goal_respects_colors_scope', 1, 7, 6).
python_function('tests/test_cinema_offline_options.py', 'test_chemical_html_has_elements', 0, 3, 2).
python_function('tests/test_cinema_offline_options.py', 'test_policy_scientific_includes_mandatory_trig', 0, 3, 1).
python_function('tests/test_cinema_offline_options.py', 'test_policy_options_a_and_b_differ', 0, 10, 1).
python_function('tests/test_cinema_offline_options.py', 'test_calculator_cinema_uses_scientific_offline', 1, 4, 3).
python_function('tests/test_cinema_offline_options.py', 'test_dashboard_project_does_not_reuse_stale_calculator_options', 1, 7, 4).
python_function('tests/test_cinema_offline_options.py', 'test_offline_chemical_from_goal_contract_lines', 1, 3, 3).
python_function('tests/test_cinema_offline_options.py', 'test_offline_scientific_screen_shows_goal', 1, 4, 2).
python_function('tests/test_cinema_offline_options.py', 'test_dashboard_seed_with_calc_body_class_stays_project_options', 1, 5, 4).
python_function('tests/test_cinema_offline_options.py', 'test_enforce_deletes_respects_session_rekeep', 1, 4, 3).
python_function('tests/test_cinema_offline_options.py', 'test_write_policy_options_without_chemical_hints', 1, 9, 2).
python_function('tests/test_cinema_offline_options.py', 'test_policy_options_restore_digit_after_delete', 1, 4, 3).
python_function('tests/test_cinema_offline_options.py', 'test_minimal_policy_keeps_all_marked_keys_even_when_compact', 1, 4, 2).
python_function('tests/test_cinema_offline_options.py', 'test_chemical_minimal_respects_keep_science_and_keep_wins_delete', 1, 4, 2).
python_function('tests/test_cinema_offline_options.py', 'test_chemical_goal_title_is_not_inside_calculator_screen', 0, 4, 2).
python_function('tests/test_cinema_offline_options.py', 'test_write_chemical_options_respects_deletes', 1, 5, 3).
python_function('tests/test_cinema_options_cache.py', 'test_options_cache_key_changes_with_stage_or_ledger', 0, 3, 1).
python_function('tests/test_cinema_options_cache.py', 'test_write_read_and_apply_options_cache', 1, 5, 6).
python_function('tests/test_cinema_policy.py', 'test_resolve_iteration_mode', 0, 7, 1).
python_function('tests/test_cinema_policy.py', 'test_normalize_manifest_target_defaults_invalid', 0, 3, 1).
python_function('tests/test_cinema_policy.py', 'test_apply_ledger_from_cinema_project_only', 1, 3, 6).
python_function('tests/test_cinema_policy.py', 'test_effective_ui_constraints_from_ledger_last_wins', 0, 3, 1).
python_function('tests/test_cinema_policy.py', 'test_merge_ui_constraint_lists_session_overrides_ledger', 0, 3, 1).
python_function('tests/test_cinema_policy.py', 'test_sync_option_previews_empty_delete_ids_mirrors_workspace', 1, 4, 5).
python_function('tests/test_cinema_policy.py', 'test_sync_option_previews_from_workspace', 1, 6, 5).
python_function('tests/test_cinema_policy.py', 'test_enforce_deletes_on_option_previews', 1, 5, 4).
python_function('tests/test_cinema_policy.py', 'test_ensure_option_previews_from_stages', 1, 3, 4).
python_function('tests/test_cinema_policy.py', 'test_propose_ui_delta_and_validate', 1, 5, 6).
python_function('tests/test_cinema_project_imports.py', 'test_import_zip_project_creates_markpact_migration_and_options', 1, 22, 12).
python_function('tests/test_cinema_project_imports.py', 'test_merged_projects_catalog_includes_imported', 1, 4, 11).
python_function('tests/test_cinema_project_imports.py', 'test_delete_project_hides_demo_from_workspace_catalog', 1, 4, 3).
python_function('tests/test_cinema_project_imports.py', 'test_activate_imported_project_reloads_stages', 1, 3, 10).
python_function('tests/test_cinema_project_imports.py', 'test_validate_urls_reject_file_scheme', 0, 3, 2).
python_function('tests/test_cinema_project_imports.py', 'test_safe_extract_zip_rejects_unsafe_paths', 1, 1, 5).
python_function('tests/test_cinema_project_imports.py', 'test_import_http_project_fetches_and_migrates', 1, 23, 15).
python_function('tests/test_cinema_project_imports.py', 'test_activate_http_import_regenerates_preview_stage0', 1, 17, 11).
python_function('tests/test_cinema_project_imports.py', 'test_activate_http_import_regenerates_preprocess_when_missing', 1, 14, 16).
python_function('tests/test_cinema_project_imports.py', 'test_activate_http_import_empty_subtitle_not_goal', 1, 7, 10).
python_function('tests/test_cinema_project_imports.py', 'test_activate_zip_import_does_not_require_user_goal', 1, 3, 9).
python_function('tests/test_cinema_project_imports.py', 'test_activate_imported_project_resets_calculator_ledger', 1, 3, 11).
python_function('tests/test_cinema_project_imports.py', 'test_import_http_project_requires_network_flag', 1, 2, 2).
python_function('tests/test_cinema_project_imports.py', 'test_import_git_project_requires_network_flag', 1, 2, 3).
python_function('tests/test_cinema_project_imports.py', 'test_is_deletable_imported_id', 0, 7, 1).
python_function('tests/test_cinema_project_imports.py', 'test_delete_imported_http_domain_id_with_dot', 1, 8, 6).
python_function('tests/test_cinema_project_imports.py', 'test_delete_imported_project_removes_directory', 1, 6, 11).
python_function('tests/test_cinema_project_imports.py', 'test_read_imported_markpact_returns_markdown', 1, 3, 8).
python_function('tests/test_cinema_project_ir.py', 'test_build_project_ir_extracts_functional_outline', 0, 5, 3).
python_function('tests/test_cinema_projects.py', 'test_list_project_catalog_has_nine_examples', 0, 3, 2).
python_function('tests/test_cinema_projects.py', 'test_workspace_catalog_can_hide_demo_project', 1, 6, 6).
python_function('tests/test_cinema_projects.py', 'test_activate_example_project_seeds_when_no_source', 1, 11, 7).
python_function('tests/test_cinema_projects.py', 'test_activate_frontend_view_seeds_selectable_web_gui', 1, 7, 5).
python_function('tests/test_cinema_projects.py', 'test_activate_analytics_copies_cinema_when_repo_available', 0, 7, 8).
python_function('tests/test_cinema_projects.py', 'test_activate_copies_dashboard_cinema_when_repo_available', 0, 6, 7).
python_function('tests/test_cinema_projects.py', 'test_activate_backend_service_resets_ledger_and_distinct_options', 1, 11, 12).
python_function('tests/test_cinema_projects.py', 'test_activate_dashboard_replaces_stale_calculator_options', 1, 7, 7).
python_function('tests/test_cinema_projects.py', 'test_activate_calculator_preserves_distinct_option_previews', 0, 5, 11).
python_function('tests/test_cinema_publish.py', 'cinema_setup', 1, 1, 2).
python_function('tests/test_cinema_publish.py', 'test_publish_creates_service_files', 1, 11, 6).
python_function('tests/test_cinema_publish.py', 'test_list_and_start_stop_service', 1, 10, 8).
python_function('tests/test_cinema_publish.py', 'test_publish_missing_stage_returns_error', 1, 2, 1).
python_function('tests/test_cinema_scope.py', 'test_dashboard_disallows_keypad_scope', 0, 4, 3).
python_function('tests/test_cinema_scope.py', 'test_calculator_allows_keypad_scope', 0, 3, 2).
python_function('tests/test_cinema_scope.py', 'test_offline_fast_scopes_per_kind', 0, 10, 2).
python_function('tests/test_cinema_scope.py', 'test_dashboard_colors_offline_labels', 1, 4, 4).
python_function('tests/test_cinema_scope.py', 'test_scope_option_variants_dashboard_functions', 0, 2, 2).
python_function('tests/test_cinema_scope.py', 'test_strip_and_inject_scope_style', 0, 4, 2).
python_function('tests/test_cinema_scope.py', 'test_scoped_html_fragment_for_calculator_colors', 0, 3, 1).
python_function('tests/test_cinema_scope.py', 'test_cinema_has_offline_baseline', 1, 4, 2).
python_function('tests/test_cinema_scope.py', 'test_inject_scope_style_calculator_colors', 0, 4, 1).
python_function('tests/test_cinema_scope.py', 'test_load_cinema_ui_profile_from_active_and_stage', 1, 3, 2).
python_function('tests/test_cinema_scope.py', 'test_ui_profile_ignores_runtime_script_tokens', 1, 2, 2).
python_function('tests/test_cinema_scope.py', 'test_can_use_offline_fast_iterate', 1, 7, 2).
python_function('tests/test_cinema_scope.py', 'test_imported_kind_uses_web_scopes', 0, 3, 2).
python_function('tests/test_cinema_scope.py', 'test_http_import_offline_colors_keeps_site_markers', 2, 9, 11).
python_function('tests/test_cinema_scope.py', 'test_http_import_offline_colors_recolors_marked_buttons', 1, 11, 7).
python_function('tests/test_cinema_scripts.py', 'test_finalize_strips_truncated_llm_script_and_injects_canonical', 0, 5, 3).
python_function('tests/test_cinema_scripts.py', 'test_finalize_marks_web_gui_components_as_selectable_targets', 0, 4, 1).
python_function('tests/test_cinema_scripts.py', 'test_inject_cinema_shield_preserves_existing_scripts', 0, 4, 3).
python_function('tests/test_cinema_scripts.py', 'test_inject_cinema_shield_posts_compact_marked_fragment', 0, 4, 1).
python_function('tests/test_cinema_server.py', 'test_render_server_script_embeds_runtime_context', 0, 74, 5).
python_function('tests/test_cinema_server.py', 'test_render_server_script_embeds_openrouter_model', 0, 3, 4).
python_function('tests/test_cinema_server.py', 'test_write_cinema_nexu_hooks_uses_template', 1, 5, 3).
python_function('tests/test_cinema_server.py', 'test_render_stage_template_injects_runtime_scripts', 0, 4, 1).
python_function('tests/test_cinema_server.py', 'test_cinema_player_template_is_externalized', 0, 68, 1).
python_function('tests/test_cinema_server.py', 'test_render_server_script_embeds_project_import_routes', 0, 17, 4).
python_function('tests/test_cinema_server.py', 'test_write_cinema_nexu_hooks_includes_import_helpers', 1, 6, 3).
python_function('tests/test_cinema_server.py', '_free_port', 0, 1, 4).
python_function('tests/test_cinema_server.py', 'test_iterate_colors_scope_uses_offline_path', 1, 15, 31).
python_function('tests/test_cinema_server.py', 'test_iterate_dashboard_kinds_colors_prefers_offline_before_llm', 1, 13, 32).
python_function('tests/test_cinema_server.py', 'test_iterate_colors_scope_uses_llm_patch_when_available', 1, 9, 30).
python_function('tests/test_cinema_server.py', 'test_effective_markpact_mode_off_for_visual_scope', 0, 5, 4).
python_function('tests/test_cinema_server.py', 'test_iterate_functions_scope_skips_offline_fast_path', 1, 10, 29).
python_function('tests/test_cinema_server.py', 'test_iterate_colors_without_stage0_skips_offline', 1, 9, 28).
python_function('tests/test_cinema_server.py', 'test_start_cinema_player_server_returns_url_without_opening', 2, 2, 3).
python_function('tests/test_cinema_server.py', 'test_projects_import_zip_endpoint', 1, 19, 33).
python_function('tests/test_cinema_server.py', 'test_delete_imported_http_domain_id_via_api', 1, 13, 28).
python_function('tests/test_cinema_spatial_patch.py', 'test_apply_spatial_deletes_removes_dashboard_kpi_card', 0, 4, 1).
python_function('tests/test_cinema_spatial_patch.py', 'test_apply_spatial_deletes_removes_only_marked_buttons', 0, 4, 3).
python_function('tests/test_cinema_traces.py', 'test_load_config_llm_model_default', 1, 2, 1).
python_function('tests/test_cinema_traces.py', 'test_load_config_llm_model_from_yaml', 1, 3, 2).
python_function('tests/test_cinema_traces.py', 'test_llm_model_env_overrides_yaml', 2, 2, 3).
python_function('tests/test_cinema_traces.py', 'test_redact_secrets_masks_api_keys', 0, 3, 1).
python_function('tests/test_cinema_traces.py', 'test_text_metrics_counts_utf8_bytes_and_estimated_tokens', 0, 4, 1).
python_function('tests/test_cinema_traces.py', 'test_write_and_read_llm_trace', 1, 14, 6).
python_function('tests/test_cinema_traces.py', 'test_load_config_reads_cinema_section', 1, 8, 3).
python_function('tests/test_cinema_ui_patch.py', 'test_build_ui_patch_prompt_is_json_contract', 0, 7, 1).
python_function('tests/test_cinema_ui_patch.py', 'test_parse_and_apply_ui_patch_response', 0, 6, 4).
python_function('tests/test_cinema_ui_patch.py', 'test_apply_ui_patch_restricts_visual_scope_to_red_marks', 0, 4, 1).
python_function('tests/test_cinema_ui_patch.py', 'test_apply_ui_patch_noops_visual_scope_with_keep_only_marks', 0, 3, 1).
python_function('tests/test_cinema_ui_patch.py', 'test_apply_ui_patch_rejects_unsafe_css', 0, 1, 2).
python_function('tests/test_cinema_ui_patch.py', 'test_apply_ui_patch_rejects_flow_breaking_css', 0, 1, 2).
python_function('tests/test_cinema_ui_patch.py', 'test_supports_llm_patch_scope', 0, 6, 1).
python_function('tests/test_export_prompt_ledger.py', 'test_export_prompt_includes_cinema_ledger_block', 1, 3, 7).
python_function('tests/test_fast_delivery.py', 'test_choose_options_route_prefers_cache', 0, 4, 1).
python_function('tests/test_fast_delivery.py', 'test_choose_options_route_uses_llm_patch_before_offline', 0, 4, 1).
python_function('tests/test_fast_delivery.py', 'test_choose_options_route_falls_back_to_offline', 0, 3, 1).
python_function('tests/test_fast_delivery.py', 'test_choose_options_route_falls_back_to_parallel_llm', 0, 3, 1).
python_function('tests/test_fast_delivery.py', 'test_options_status_helpers', 0, 4, 2).
python_function('tests/test_fast_delivery.py', 'test_compact_html_for_llm_removes_scripts_and_limits', 0, 3, 1).
python_function('tests/test_fast_delivery.py', 'test_markpact_context_helpers', 0, 4, 2).
python_function('tests/test_fast_delivery.py', 'test_fast_delivery_options_cache_roundtrip', 1, 6, 6).
python_function('tests/test_fast_delivery.py', 'test_fast_delivery_options_cache_rejects_invalid_cached_html', 1, 4, 4).
python_function('tests/test_fast_delivery.py', 'test_fast_delivery_options_cache_rejects_calculator_for_web_stage', 1, 4, 4).
python_function('tests/test_intract.py', 'test_parse_intract_line', 0, 5, 1).
python_function('tests/test_models.py', 'test_capsule_roundtrip', 0, 3, 4).
python_function('tests/test_models.py', 'test_snapshot_roundtrip', 0, 2, 3).
python_function('tests/test_nexu.py', 'test_placeholder', 0, 2, 0).
python_function('tests/test_nexu.py', 'test_import', 0, 1, 0).
python_function('tests/test_orchestration_mcp.py', '_make_project', 1, 1, 2).
python_function('tests/test_orchestration_mcp.py', 'test_orchestration_offline', 1, 5, 6).
python_function('tests/test_orchestration_mcp.py', 'test_mcp_tool_dispatch_and_protocol', 1, 7, 5).
python_function('tests/test_promote_apply.py', 'test_apply_promotion_plan', 1, 3, 9).
python_function('tests/test_review_bundle.py', 'test_review_bundle_and_promotion_prechecks', 1, 13, 14).
python_function('tests/test_verify_intract.py', 'test_verify_treats_manifest_intract_fail_as_warn', 1, 8, 8).

% ── Python Classes ───────────────────────────────────────
python_class('examples/web_app_calculator/cinema/server.py', 'CustomHTTPRequestHandler').
python_method('CustomHTTPRequestHandler', '__init__', 0, 1, 3).
python_method('CustomHTTPRequestHandler', 'do_GET', 0, 34, 28).
python_method('CustomHTTPRequestHandler', 'do_POST', 0, 211, 120).
python_method('CustomHTTPRequestHandler', 'do_DELETE', 0, 9, 12).
python_method('CustomHTTPRequestHandler', 'do_OPTIONS', 0, 1, 3).
python_class('examples/web_app_calculator/cinema/server.py', 'ThreadingHTTPServer').
python_class('src/nexu/cinema_http_preprocess.py', '_OutlineParser').
python_method('_OutlineParser', '__init__', 0, 1, 2).
python_method('_OutlineParser', '_keep_attr', 1, 2, 2).
python_method('_OutlineParser', 'handle_starttag', 2, 8, 3).
python_method('_OutlineParser', 'handle_endtag', 1, 4, 2).
python_method('_OutlineParser', 'handle_data', 1, 4, 3).
python_class('src/nexu/cinema_project_ir.py', '_ProjectIRParser').
python_method('_ProjectIRParser', '__init__', 0, 1, 2).
python_method('_ProjectIRParser', 'handle_starttag', 2, 5, 2).
python_method('_ProjectIRParser', '_classify_node', 4, 12, 4).
python_method('_ProjectIRParser', 'handle_endtag', 1, 8, 9).
python_method('_ProjectIRParser', 'handle_data', 1, 4, 2).
python_class('src/nexu/cinema_projects.py', 'ExampleProject').
python_method('ExampleProject', 'to_public_dict', 0, 1, 2).
python_class('src/nexu/config.py', 'LLMConfig').
python_class('src/nexu/config.py', 'ReviewConfig').
python_class('src/nexu/config.py', 'CinemaConfig').
python_class('src/nexu/config.py', 'nexuConfig').
python_class('src/nexu/fast_delivery/router.py', 'DeliveryRoute').
python_class('src/nexu/intract.py', 'IntentContract').
python_method('IntentContract', 'key', 0, 3, 0).
python_class('src/nexu/models.py', 'FrozenFile').
python_class('src/nexu/models.py', 'FrozenSnapshot').
python_method('FrozenSnapshot', 'to_dict', 0, 1, 1).
python_method('FrozenSnapshot', 'from_dict', 2, 2, 4).
python_class('src/nexu/models.py', 'CapsuleSelection').
python_class('src/nexu/models.py', 'CapsuleRuntime').
python_class('src/nexu/models.py', 'Capsule').
python_method('Capsule', 'to_dict', 0, 1, 1).
python_method('Capsule', 'from_dict', 2, 2, 7).
python_class('src/nexu/models.py', 'VerificationFinding').
python_class('src/nexu/models.py', 'VerificationReport').
python_method('VerificationReport', 'to_dict', 0, 1, 1).
python_class('src/nexu/models.py', 'CapsuleDiff').
python_method('CapsuleDiff', 'to_dict', 0, 1, 1).
python_class('src/nexu/models.py', 'PromptExport').
python_method('PromptExport', 'to_dict', 0, 1, 1).
python_class('tests/test_cinema_server.py', '_LLMConfig').

% ── Dependencies ─────────────────────────────────────────

% ── Makefile Targets ─────────────────────────────────────
makefile_target('test', '').
makefile_target('examples', '').
makefile_target('docs-links', '').
makefile_target('quality-intract', '').
makefile_target('quality-redup', '').
makefile_target('quality', '').
makefile_target('quality-strict', '').
makefile_target('cinema', '').
makefile_target('cinema-open', '').
makefile_target('cinema-test', '').
makefile_target('cinema-stop', '').
makefile_target('cinema-restart', '').
makefile_target('cinema-repair', '').
makefile_target('ci-cinema-smoke', '').

% ── Taskfile Tasks ───────────────────────────────────────

% ── Environment Variables ────────────────────────────────
env_variable('OPENROUTER_API_KEY', '*(not set)*', 'Required: OpenRouter API key (https://openrouter.ai/keys)').
env_variable('LLM_MODEL', 'openrouter/qwen/qwen3-coder-next', 'Model (default: openrouter/qwen/qwen3-coder-next)').
env_variable('PFIX_AUTO_APPLY', 'true', 'true = apply fixes without asking').
env_variable('PFIX_AUTO_INSTALL_DEPS', 'true', 'true = auto pip/uv install').
env_variable('PFIX_AUTO_RESTART', 'false', 'true = os.execv restart after fix').
env_variable('PFIX_MAX_RETRIES', '3', '').
env_variable('PFIX_DRY_RUN', 'false', '').
env_variable('PFIX_ENABLED', 'true', '').
env_variable('PFIX_GIT_COMMIT', 'false', 'true = auto-commit fixes').
env_variable('PFIX_GIT_PREFIX', 'pfix:', 'commit message prefix').
env_variable('PFIX_CREATE_BACKUPS', 'false', 'false = disable .pfix_backups/ directory').

% ── TestQL Scenarios ─────────────────────────────────────
testql_scenario('generated-cli-tests.testql.toon.yaml', 'cli').

% ── Semantic Facts from SUMD.md ──────────────────────────
sumd_declared_file('app.doql.less', 'doql').
sumd_declared_file('testql-scenarios/generated-cli-tests.testql.toon.yaml', 'testql').
sumd_declared_file('pyqual.yaml', 'pyqual').
sumd_declared_file('project/map.toon.yaml', 'analysis').
sumd_declared_file('project/logic.pl', 'analysis').
sumd_declared_file('project/calls.toon.yaml', 'analysis').
sumd_interface('api', '').
sumd_interface('cli', 'argparse').
sumd_interface('cli', '').
sumd_workflow('test', 'manual').
sumd_workflow_step('test', 1, 'pytest -q').
sumd_workflow('examples', 'manual').
sumd_workflow_step('examples', 1, 'python examples/run_examples.py').
sumd_workflow('docs-links', 'manual').
sumd_workflow_step('docs-links', 1, 'python scripts/check-doc-links.py .').
sumd_workflow('quality-intract', 'manual').
sumd_workflow_step('quality-intract', 1, 'intract check src --format text').
sumd_workflow_step('quality-intract', 2, 'intract coverage src').
sumd_workflow('quality-redup', 'manual').
sumd_workflow_step('quality-redup', 1, 'redup scan src --format toon --min-lines 8').
sumd_workflow('quality', 'manual').
sumd_workflow_step('quality', 1, 'ruff check \').
sumd_workflow_step('quality', 2, 'src/nexu/cinema.py \').
sumd_workflow_step('quality', 3, 'src/nexu/cinema_server.py \').
sumd_workflow_step('quality', 4, 'src/nexu/cinema_baseline_contracts.py \').
sumd_workflow_step('quality', 5, 'src/nexu/cinema_goal_contracts.py \').
sumd_workflow_step('quality', 6, 'src/nexu/cinema_html.py \').
sumd_workflow_step('quality', 7, 'src/nexu/cinema_html_validate.py \').
sumd_workflow_step('quality', 8, 'src/nexu/cinema_llm_contracts.py \').
sumd_workflow_step('quality', 9, 'src/nexu/cinema_markpact.py \').
sumd_workflow_step('quality', 10, 'src/nexu/cinema_dom_patch.py \').
sumd_workflow_step('quality', 11, 'src/nexu/cinema_project_ir.py \').
sumd_workflow_step('quality', 12, 'src/nexu/cinema_project_imports.py \').
sumd_workflow_step('quality', 13, 'src/nexu/cinema_projects.py \').
sumd_workflow_step('quality', 14, 'src/nexu/cinema_scripts.py \').
sumd_workflow_step('quality', 15, 'src/nexu/cinema_publish.py \').
sumd_workflow_step('quality', 16, 'src/nexu/cinema_offline_options.py \').
sumd_workflow_step('quality', 17, 'src/nexu/cinema_options_cache.py \').
sumd_workflow_step('quality', 18, 'src/nexu/cinema_ui_patch.py \').
sumd_workflow_step('quality', 19, 'src/nexu/fast_delivery/__init__.py \').
sumd_workflow_step('quality', 20, 'src/nexu/fast_delivery/context.py \').
sumd_workflow_step('quality', 21, 'src/nexu/fast_delivery/options.py \').
sumd_workflow_step('quality', 22, 'src/nexu/fast_delivery/router.py \').
sumd_workflow_step('quality', 23, 'src/nexu/intract.py \').
sumd_workflow_step('quality', 24, 'src/nexu/verify.py \').
sumd_workflow_step('quality', 25, 'src/nexu/intract_adapter.py \').
sumd_workflow_step('quality', 26, 'tests/test_cinema_server.py \').
sumd_workflow_step('quality', 27, 'tests/test_cinema_baseline_contracts.py \').
sumd_workflow_step('quality', 28, 'tests/test_cinema_goal_contracts.py \').
sumd_workflow_step('quality', 29, 'tests/test_cinema_markpact.py \').
sumd_workflow_step('quality', 30, 'tests/test_cinema_dom_patch.py \').
sumd_workflow_step('quality', 31, 'tests/test_cinema_project_ir.py \').
sumd_workflow_step('quality', 32, 'tests/test_cinema_project_imports.py \').
sumd_workflow_step('quality', 33, 'tests/test_cinema_projects.py \').
sumd_workflow_step('quality', 34, 'tests/test_cinema_scripts.py \').
sumd_workflow_step('quality', 35, 'tests/test_cinema_publish.py \').
sumd_workflow_step('quality', 36, 'tests/test_cinema_offline_options.py \').
sumd_workflow_step('quality', 37, 'tests/test_cinema_options_cache.py \').
sumd_workflow_step('quality', 38, 'tests/test_cinema_ui_patch.py \').
sumd_workflow_step('quality', 39, 'tests/test_fast_delivery.py').
sumd_workflow('quality-strict', 'manual').
sumd_workflow_step('quality-strict', 1, 'pytest -q').
sumd_workflow_step('quality-strict', 2, 'ruff check src tests --statistics').
sumd_workflow_step('quality-strict', 3, 'intract check . --format text').
sumd_workflow_step('quality-strict', 4, 'redup scan src --format toon').
sumd_workflow('cinema', 'manual').
sumd_workflow_step('cinema', 1, 'uv sync --quiet').
sumd_workflow_step('cinema', 2, '$(CINEMA_MODEL_ARG) uv run nexu capsule iterate $(CINEMA_CAPSULE) --steps 1 --goal "$(CINEMA_GOAL)" --cinema --path $(CINEMA_PATH)').
sumd_workflow('cinema-open', 'manual').
sumd_workflow_step('cinema-open', 1, 'url="$$( uv sync --quiet').
sumd_workflow_step('cinema-open', 2, 'if [ -z "$$url" ]').
sumd_workflow_step('cinema-open', 3, 'echo "Could not detect Nexu URL. See /tmp/nexu-cinema-open.log"').
sumd_workflow_step('cinema-open', 4, 'exit 1').
sumd_workflow_step('cinema-open', 5, 'fi').
sumd_workflow_step('cinema-open', 6, 'echo "Opening $$url"').
sumd_workflow_step('cinema-open', 7, '( xdg-open "$$url" >/dev/null 2>&1 || sensible-browser "$$url" >/dev/null 2>&1 || firefox "$$url" >/dev/null 2>&1 || google-chrome "$$url" >/dev/null 2>&1 || true )').
sumd_workflow('cinema-test', 'manual').
sumd_workflow_step('cinema-test', 1, 'pytest -q').
sumd_workflow('cinema-stop', 'manual').
sumd_workflow_step('cinema-stop', 1, 'pkill -f \'[/]cinema/server.py\' >/dev/null 2>&1 || true').
sumd_workflow_step('cinema-stop', 2, 'echo \'Stopped cinema server.py process(es) if any were running.\'').
sumd_workflow('cinema-restart', 'manual').
sumd_workflow_step('cinema-restart', 1, '$(MAKE) cinema-stop').
sumd_workflow_step('cinema-restart', 2, '$(MAKE) cinema').
sumd_workflow('cinema-repair', 'manual').
sumd_workflow_step('cinema-repair', 1, 'uv run python -c "from pathlib import Path').
sumd_workflow('ci-cinema-smoke', 'manual').
sumd_workflow_step('ci-cinema-smoke', 1, './scripts/ci-cinema-smoke.sh').
```

## Call Graph

*381 nodes · 500 edges · 63 modules · CC̄=4.8*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `do_GET` *(in examples.web_app_calculator.cinema.server.CustomHTTPRequestHandler)* | 34 ⚠ | 0 | 183 | **183** |
| `print` *(in scripts.ci-cinema-smoke)* | 0 | 94 | 0 | **94** |
| `load_config` *(in src.nexu.config)* | 14 ⚠ | 5 | 76 | **81** |
| `read_manifest_contracts` *(in src.nexu.intract)* | 12 ⚠ | 8 | 32 | **40** |
| `main` *(in examples.web_app_pactown_ecosystem.run)* | 8 | 0 | 39 | **39** |
| `main` *(in examples.web_app_event_monitor.run)* | 13 ⚠ | 0 | 37 | **37** |
| `build_intract_policy_snapshot` *(in src.nexu.cinema)* | 11 ⚠ | 4 | 32 | **36** |
| `apply_spatial_deletes_to_html` *(in src.nexu.cinema_scripts)* | 4 | 7 | 29 | **36** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/nexu
# generated in 0.43s
# nodes: 381 | edges: 500 | modules: 63
# CC̄=4.8

HUBS[20]:
  examples.web_app_calculator.cinema.server.CustomHTTPRequestHandler.do_GET
    CC=34  in:0  out:183  total:183
  scripts.ci-cinema-smoke.print
    CC=0  in:94  out:0  total:94
  src.nexu.config.load_config
    CC=14  in:5  out:76  total:81
  src.nexu.intract.read_manifest_contracts
    CC=12  in:8  out:32  total:40
  examples.web_app_pactown_ecosystem.run.main
    CC=8  in:0  out:39  total:39
  examples.web_app_event_monitor.run.main
    CC=13  in:0  out:37  total:37
  src.nexu.cinema.build_intract_policy_snapshot
    CC=11  in:4  out:32  total:36
  src.nexu.cinema_scripts.apply_spatial_deletes_to_html
    CC=4  in:7  out:29  total:36
  examples.web_app_dashboard.run.main
    CC=2  in:0  out:35  total:35
  src.nexu.report.build_capsule_report
    CC=1  in:2  out:32  total:34
  src.nexu.cinema_server._render_server_script
    CC=1  in:1  out:31  total:32
  src.nexu.paths.project_root
    CC=1  in:29  out:3  total:32
  src.nexu.capsule.create_capsule
    CC=8  in:7  out:24  total:31
  src.nexu.orchestrate.build_capsule_orchestration
    CC=2  in:2  out:28  total:30
  src.nexu.cinema_http_preprocess.load_http_preprocess_artifacts
    CC=16  in:1  out:27  total:28
  examples.run_examples.run_example
    CC=2  in:1  out:26  total:27
  src.nexu.paths.capsule_dir
    CC=1  in:25  out:1  total:26
  examples.web_app_calculator.cinema.server._llm_status_payload
    CC=3  in:1  out:25  total:26
  src.nexu.cinema_baseline_contracts.ensure_capsule_intract_yaml
    CC=9  in:1  out:25  total:26
  src.nexu.review.build_review_packet
    CC=5  in:2  out:24  total:26

MODULES:
  examples.nexu_markpact_exporter  [1 funcs]
    main  CC=3  out:22
  examples.realtime_lane_nexu_sync  [1 funcs]
    simulate_realtime_sync  CC=2  out:10
  examples.run_examples  [2 funcs]
    main  CC=2  out:1
    run_example  CC=2  out:26
  examples.scientific_calculator_demo  [1 funcs]
    main  CC=2  out:23
  examples.scientific_calculator_demo2  [2 funcs]
    main  CC=2  out:17
    print_code  CC=1  out:6
  examples.web_app_calculator.cinema.nexu_hooks  [28 funcs]
    activate_project  CC=2  out:6
    active_project  CC=1  out:3
    append_goal_policy_entry  CC=11  out:19
    append_policy_entry  CC=1  out:1
    apply_manifest_from_ledger  CC=1  out:1
    apply_spatial_patch  CC=2  out:2
    delete_imported  CC=1  out:4
    effective_ui_constraints  CC=1  out:1
    export_markpact_readme  CC=2  out:5
    goal_contract_lines  CC=1  out:1
  examples.web_app_calculator.cinema.server  [38 funcs]
    do_DELETE  CC=9  out:23
    do_GET  CC=34  out:183
    _append_policy_entry  CC=2  out:2
    _append_policy_entry_legacy  CC=3  out:12
    _compact_html_for_llm  CC=1  out:4
    _compact_llm_error  CC=2  out:4
    _compact_markpact_for_llm  CC=3  out:10
    _delete_imported_project  CC=2  out:1
    _effective_markpact_mode  CC=1  out:7
    _effective_ui_constraints_from_ledger  CC=17  out:16
  examples.web_app_calculator.run  [1 funcs]
    main  CC=2  out:23
  examples.web_app_dashboard.run  [1 funcs]
    main  CC=2  out:35
  examples.web_app_event_monitor.run  [1 funcs]
    main  CC=13  out:37
  examples.web_app_pactown_ecosystem.run  [1 funcs]
    main  CC=8  out:39
  scripts.ci-cinema-smoke  [1 funcs]
    print  CC=0  out:0
  src.nexu.blueprint  [1 funcs]
    build_blueprint  CC=7  out:8
  src.nexu.bundle  [2 funcs]
    _should_include  CC=5  out:4
    build_capsule_bundle  CC=3  out:15
  src.nexu.capsule  [4 funcs]
    create_capsule  CC=8  out:24
    list_capsules  CC=4  out:5
    load_capsule  CC=1  out:3
    save_capsule  CC=1  out:3
  src.nexu.cinema  [9 funcs]
    _cinema_template_text  CC=1  out:3
    _contract_to_public_dict  CC=1  out:1
    _render_cinema_template  CC=2  out:5
    _start_cinema_server  CC=2  out:3
    build_intract_policy_snapshot  CC=11  out:32
    generate_cinema_player  CC=1  out:18
    sync_cinema_templates  CC=1  out:4
    write_cinema_nexu_hooks  CC=1  out:8
    write_intract_policy_files  CC=2  out:5
  src.nexu.cinema_baseline_contracts  [5 funcs]
    _contract  CC=3  out:2
    calculator_baseline_contracts  CC=1  out:7
    ensure_capsule_intract_yaml  CC=9  out:25
    is_calculator_capsule  CC=5  out:5
    merge_calculator_baselines  CC=5  out:5
  src.nexu.cinema_dom_patch  [8 funcs]
    _goal_label  CC=3  out:2
    _inject_into_body  CC=2  out:3
    _inject_into_head  CC=4  out:5
    _strip_existing_patch  CC=2  out:3
    _variant_section  CC=3  out:11
    build_function_option_patches  CC=8  out:14
    build_function_patch_context  CC=2  out:3
    supports_function_patch  CC=4  out:4
  src.nexu.cinema_goal_contracts  [14 funcs]
    _build_detail_text  CC=5  out:5
    _collect_trait_proposals  CC=3  out:6
    _detect_api_trait  CC=3  out:3
    _detect_chemical_trait  CC=2  out:2
    _detect_dashboard_trait  CC=3  out:3
    _detect_engineering_trait  CC=4  out:3
    _detect_expanded_trait  CC=4  out:3
    _detect_minimal_trait  CC=4  out:3
    _goal_contract_dict  CC=6  out:15
    _hints_text  CC=3  out:6
  src.nexu.cinema_history  [13 funcs]
    _build_label  CC=4  out:7
    _copy_checkpoint_files  CC=3  out:3
    _ledger_snapshot  CC=3  out:4
    _load_index  CC=3  out:5
    _refresh_policy_snapshot  CC=1  out:1
    _write_index  CC=1  out:5
    ensure_initial_checkpoint  CC=3  out:4
    history_dir  CC=1  out:0
    history_index_path  CC=1  out:1
    ledger_archive_for_display  CC=5  out:16
  src.nexu.cinema_html_validate  [1 funcs]
    prepare_cinema_html_document  CC=2  out:2
  src.nexu.cinema_http_preprocess  [24 funcs]
    _extract_inline_css  CC=4  out:4
    _extract_stylesheet_hrefs  CC=7  out:4
    _filter_visual_css  CC=3  out:4
    _load_project_meta  CC=4  out:4
    _normalize_linked_paths  CC=9  out:9
    _project_meta_path  CC=1  out:0
    _rule_is_visual  CC=7  out:8
    _safe_read_under  CC=5  out:7
    _script_src_allowed_for_preview  CC=4  out:5
    _should_remove_preview_script  CC=2  out:3
  src.nexu.cinema_llm  [3 funcs]
    _cached_config  CC=4  out:4
    _litellm_completion  CC=2  out:0
    compact_llm_error  CC=5  out:11
  src.nexu.cinema_llm_contracts  [1 funcs]
    build_llm_contract_block  CC=2  out:2
  src.nexu.cinema_markpact  [5 funcs]
    _escape_markdown_fence  CC=2  out:1
    _get_app_title  CC=3  out:3
    _get_baseline_block  CC=6  out:4
    build_markpact_readme  CC=11  out:21
    markpact_download_filename  CC=2  out:2
  src.nexu.cinema_offline_options  [1 funcs]
    _delete_without_keeps  CC=3  out:2
  src.nexu.cinema_options_cache  [4 funcs]
    _digest  CC=2  out:4
    goal_slug  CC=4  out:5
    options_cache_key  CC=7  out:16
    write_options_cache  CC=5  out:14
  src.nexu.cinema_policy  [38 funcs]
    _build_constraint_result  CC=5  out:4
    _html_files_distinct  CC=3  out:6
    _normalize_html_body  CC=1  out:2
    _process_keep_delete_entries  CC=7  out:6
    _process_ledger_entry  CC=4  out:4
    _process_proposed_contracts  CC=8  out:3
    _proposal_kind_and_element  CC=12  out:8
    _replace_html_title  CC=2  out:2
    _resolve_ledger_path  CC=2  out:2
    append_goal_ledger_entry  CC=7  out:13
  src.nexu.cinema_project_imports  [8 funcs]
    activate_imported_project  CC=4  out:6
    delete_imported_project  CC=7  out:12
    import_git_project  CC=11  out:16
    import_http_project  CC=7  out:21
    import_zip_project  CC=5  out:13
    imported_project_llm_log  CC=8  out:14
    merged_projects_catalog  CC=10  out:13
    read_imported_markpact  CC=9  out:17
  src.nexu.cinema_project_ir  [6 funcs]
    _classify_node  CC=12  out:10
    handle_data  CC=4  out:2
    handle_endtag  CC=8  out:11
    _clean_text  CC=2  out:3
    build_project_ir  CC=2  out:8
    summarize_project_ir  CC=12  out:21
  src.nexu.cinema_projects  [24 funcs]
    _active_project_meta  CC=1  out:2
    _apply_preprocess_meta  CC=3  out:5
    _bootstrap_goal_from_project  CC=4  out:6
    _catalog_filters  CC=14  out:12
    _copy_cinema_files  CC=4  out:6
    _copy_or_seed_project_files  CC=3  out:2
    _find_example_project  CC=3  out:1
    _init_project_activation  CC=3  out:4
    _project_catalog_entry  CC=2  out:2
    _project_widgets  CC=1  out:1
  src.nexu.cinema_publish  [20 funcs]
    _allocate_service_port  CC=11  out:11
    _generate_markpact_export  CC=1  out:5
    _handle_existing_service  CC=7  out:8
    _http_ok  CC=2  out:1
    _load_registry  CC=3  out:6
    _pick_port  CC=4  out:2
    _port_open  CC=2  out:1
    _prepare_service_directory  CC=1  out:4
    _refresh_service_status  CC=3  out:1
    _register_service  CC=4  out:6
  src.nexu.cinema_scope  [2 funcs]
    load_cinema_ui_profile  CC=10  out:15
    scope_meta_for_project  CC=1  out:3
  src.nexu.cinema_scripts  [4 funcs]
    apply_spatial_deletes_to_html  CC=4  out:29
    finalize_cinema_html  CC=6  out:6
    repair_cinema_html_files  CC=5  out:8
    write_cinema_inject_files  CC=1  out:3
  src.nexu.cinema_server  [7 funcs]
    _available_port  CC=4  out:8
    _litellm_available  CC=1  out:1
    _open_browser  CC=3  out:2
    _render_server_script  CC=1  out:31
    _try_spawn_on_port  CC=2  out:5
    start_cinema_player_server  CC=2  out:4
    start_persistent_http_server  CC=2  out:7
  src.nexu.cinema_traces  [7 funcs]
    list_llm_traces  CC=1  out:2
    read_llm_trace  CC=2  out:5
    read_trace_index  CC=3  out:3
    redact_secrets  CC=9  out:9
    text_metrics  CC=3  out:6
    trace_slug  CC=3  out:3
    write_llm_trace  CC=8  out:18
  src.nexu.cli  [22 funcs]
    _print_yaml  CC=1  out:3
    _relative_to_root  CC=1  out:2
    capsule_blueprint  CC=2  out:8
    capsule_bundle  CC=1  out:9
    capsule_create  CC=1  out:15
    capsule_diff  CC=1  out:19
    capsule_drift  CC=2  out:10
    capsule_export_prompt  CC=1  out:8
    capsule_iterate  CC=2  out:14
    capsule_journal  CC=2  out:17
  src.nexu.config  [3 funcs]
    _load_env_file  CC=10  out:11
    load_config  CC=14  out:76
    load_env_files  CC=3  out:3
  src.nexu.export_prompt  [2 funcs]
    _cinema_policy_ledger_block  CC=12  out:13
    export_iteration_prompt  CC=3  out:18
  src.nexu.fast_delivery.context  [3 funcs]
    compact_html_for_llm  CC=3  out:6
    compact_markpact_for_llm  CC=9  out:12
    effective_markpact_mode  CC=8  out:7
  src.nexu.fast_delivery.options  [2 funcs]
    read_cached_options  CC=11  out:17
    store_options_cache  CC=3  out:4
  src.nexu.files  [4 funcs]
    collect_files  CC=8  out:8
    is_text_file  CC=2  out:1
    matches_any  CC=3  out:4
    rel  CC=1  out:2
  src.nexu.init_project  [1 funcs]
    init_project  CC=3  out:7
  src.nexu.intract  [7 funcs]
    _split_csv  CC=4  out:4
    _tokenize_contract  CC=5  out:10
    format_intract_v1_line  CC=3  out:1
    parse_intract_line  CC=3  out:22
    read_manifest_contracts  CC=12  out:32
    scan_contracts_in_file  CC=3  out:5
    scan_contracts_in_text  CC=3  out:4
  src.nexu.intract_adapter  [6 funcs]
    _ensure_intract_on_path  CC=3  out:4
    _finding_for_result  CC=9  out:16
    _policy_findings  CC=3  out:4
    _result_status  CC=1  out:3
    _sibling_intract_src  CC=4  out:3
    check_intract_policy  CC=7  out:11
  src.nexu.iterate  [1 funcs]
    iterate_capsule  CC=7  out:14
  src.nexu.journal  [2 funcs]
    append_journal  CC=2  out:6
    read_journal  CC=5  out:6
  src.nexu.llm  [5 funcs]
    _extract_content  CC=4  out:5
    _strip_fences  CC=7  out:9
    call_litellm_json  CC=8  out:13
    call_litellm_review  CC=2  out:3
    offline_review_from_status  CC=4  out:0
  src.nexu.mcp_server  [1 funcs]
    run_mcp_stdio  CC=6  out:7
  src.nexu.orchestrate  [6 funcs]
    _contract_dicts  CC=2  out:0
    _render_orchestration_markdown  CC=9  out:22
    build_capsule_orchestration  CC=2  out:28
    build_orchestration_context  CC=2  out:11
    build_orchestration_prompt  CC=1  out:2
    offline_orchestration_from_context  CC=13  out:22
  src.nexu.paths  [6 funcs]
    capsule_dir  CC=1  out:1
    capsules_dir  CC=1  out:1
    ensure_project_dirs  CC=2  out:7
    nexu_dir  CC=1  out:0
    project_root  CC=1  out:3
    snapshots_dir  CC=1  out:1
  src.nexu.plan  [2 funcs]
    _contract_summary  CC=9  out:3
    build_iteration_plan  CC=7  out:15
  src.nexu.promote  [3 funcs]
    _promotion_map  CC=2  out:4
    apply_promotion_plan  CC=4  out:8
    build_promotion_plan  CC=6  out:16
  src.nexu.report  [1 funcs]
    build_capsule_report  CC=1  out:32
  src.nexu.review  [2 funcs]
    _markdown_review_prompt  CC=1  out:6
    build_review_packet  CC=5  out:24
  src.nexu.runtime  [3 funcs]
    _collect_fixtures  CC=5  out:7
    _read_fixture  CC=5  out:6
    build_capsule_runtime  CC=3  out:16
  src.vico.diff  [1 funcs]
    diff_capsule  CC=12  out:14
  src.vico.drift  [1 funcs]
    check_source_drift  CC=7  out:10
  src.vico.freeze  [1 funcs]
    freeze_project  CC=2  out:12
  src.vico.git  [1 funcs]
    current_git_sha  CC=4  out:3
  src.vico.hashing  [1 funcs]
    sha256_file  CC=2  out:6
  src.vico.models  [4 funcs]
    from_dict  CC=2  out:6
    read_yaml  CC=3  out:4
    utc_now  CC=1  out:2
    write_yaml  CC=1  out:3
  src.vico.status  [1 funcs]
    capsule_status  CC=3  out:10

EDGES:
  examples.nexu_markpact_exporter.main → scripts.ci-cinema-smoke.print
  examples.scientific_calculator_demo.main → scripts.ci-cinema-smoke.print
  examples.scientific_calculator_demo.main → src.nexu.init_project.init_project
  examples.scientific_calculator_demo.main → src.vico.freeze.freeze_project
  examples.scientific_calculator_demo.main → src.nexu.capsule.create_capsule
  examples.realtime_lane_nexu_sync.simulate_realtime_sync → scripts.ci-cinema-smoke.print
  examples.run_examples.run_example → src.nexu.init_project.init_project
  examples.run_examples.run_example → src.vico.freeze.freeze_project
  examples.run_examples.run_example → src.nexu.capsule.create_capsule
  examples.run_examples.run_example → src.nexu.plan.build_iteration_plan
  examples.run_examples.run_example → src.nexu.blueprint.build_blueprint
  examples.run_examples.run_example → src.nexu.iterate.iterate_capsule
  examples.run_examples.run_example → src.nexu.runtime.build_capsule_runtime
  examples.run_examples.run_example → src.nexu.export_prompt.export_iteration_prompt
  examples.run_examples.main → examples.run_examples.run_example
  examples.scientific_calculator_demo2.print_code → scripts.ci-cinema-smoke.print
  examples.scientific_calculator_demo2.main → examples.scientific_calculator_demo2.print_code
  examples.scientific_calculator_demo2.main → src.nexu.init_project.init_project
  examples.scientific_calculator_demo2.main → src.vico.freeze.freeze_project
  examples.scientific_calculator_demo2.main → src.nexu.capsule.create_capsule
  examples.scientific_calculator_demo2.main → src.nexu.iterate.iterate_capsule
  examples.web_app_event_monitor.run.main → scripts.ci-cinema-smoke.print
  examples.web_app_calculator.run.main → src.nexu.init_project.init_project
  examples.web_app_calculator.run.main → src.vico.freeze.freeze_project
  examples.web_app_calculator.run.main → scripts.ci-cinema-smoke.print
  examples.web_app_calculator.run.main → src.nexu.capsule.create_capsule
  examples.web_app_calculator.cinema.nexu_hooks.apply_manifest_from_ledger → src.nexu.cinema_policy.apply_ledger_from_cinema
  examples.web_app_calculator.cinema.nexu_hooks.verify_capsule → src.nexu.cinema_policy.verify_capsule_workspace
  examples.web_app_calculator.cinema.nexu_hooks.apply_spatial_patch → src.nexu.cinema_scripts.apply_spatial_deletes_to_html
  examples.web_app_calculator.cinema.nexu_hooks.apply_spatial_patch → src.nexu.cinema_scripts.finalize_cinema_html
  examples.web_app_calculator.cinema.nexu_hooks.propose_llm → src.nexu.cinema_policy.propose_llm_for_stage
  examples.web_app_calculator.cinema.nexu_hooks.append_policy_entry → src.nexu.cinema_policy.append_iteration_ledger_entry
  examples.web_app_calculator.cinema.nexu_hooks.append_goal_policy_entry → src.nexu.cinema_policy.append_goal_ledger_entry
  examples.web_app_calculator.cinema.nexu_hooks.append_goal_policy_entry → src.nexu.cinema_projects.load_active_project
  examples.web_app_calculator.cinema.nexu_hooks.goal_contract_lines → src.nexu.cinema_policy.load_goal_contract_lines
  examples.web_app_calculator.cinema.nexu_hooks.validate_artifact → src.nexu.cinema_policy.validate_intract_artifact
  examples.web_app_calculator.cinema.nexu_hooks.save_history → src.nexu.cinema_history.save_history_checkpoint
  examples.web_app_calculator.cinema.nexu_hooks.list_history → src.nexu.cinema_history.list_history_checkpoints
  examples.web_app_calculator.cinema.nexu_hooks.list_history → src.nexu.cinema_history.ledger_archive_for_display
  examples.web_app_calculator.cinema.nexu_hooks.restore_history → src.nexu.cinema_history.restore_history_checkpoint
  examples.web_app_calculator.cinema.nexu_hooks.effective_ui_constraints → src.nexu.cinema_policy.load_effective_ui_constraints
  examples.web_app_calculator.cinema.nexu_hooks.sync_option_previews → src.nexu.cinema_policy.sync_option_previews_from_workspace
  examples.web_app_calculator.cinema.nexu_hooks.patch_option_previews → src.nexu.cinema_policy.load_effective_ui_constraints
  examples.web_app_calculator.cinema.nexu_hooks.patch_option_previews → src.nexu.cinema_policy.enforce_deletes_on_option_previews
  examples.web_app_calculator.cinema.nexu_hooks.patch_option_previews → src.nexu.cinema_policy.merge_ui_constraint_lists
  examples.web_app_calculator.cinema.nexu_hooks.projects_catalog → src.nexu.cinema_project_imports.merged_projects_catalog
  examples.web_app_calculator.cinema.nexu_hooks.activate_project → src.nexu.cinema_projects.activate_example_project
  examples.web_app_calculator.cinema.nexu_hooks.activate_project → src.nexu.cinema_project_imports.activate_imported_project
  examples.web_app_calculator.cinema.nexu_hooks.activate_project → src.nexu.cinema_projects.find_nexu_repo_root
  examples.web_app_calculator.cinema.nexu_hooks.import_project_from_zip → src.nexu.cinema_project_imports.import_zip_project
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

## Intent

Visual Intent Contract Orchestrator: freeze project slices, evolve capsules, verify intent contracts.
