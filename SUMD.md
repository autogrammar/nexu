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
- **version**: `0.5.17`
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
  version: 0.5.17;
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
  step-1: run cmd=ruff check src/nexu/cinema.py src/nexu/cinema_server.py src/nexu/cinema_baseline_contracts.py src/nexu/cinema_markpact.py src/nexu/cinema_publish.py src/nexu/cinema_offline_options.py src/nexu/verify.py src/nexu/intract_adapter.py tests/test_cinema_server.py tests/test_cinema_baseline_contracts.py tests/test_cinema_markpact.py tests/test_cinema_publish.py tests/test_cinema_offline_options.py;
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
      run: ruff check src/nexu/cinema.py src/nexu/cinema_server.py src/nexu/cinema_baseline_contracts.py src/nexu/cinema_markpact.py src/nexu/cinema_publish.py src/nexu/cinema_offline_options.py src/nexu/verify.py src/nexu/intract_adapter.py tests/test_cinema_server.py tests/test_cinema_baseline_contracts.py tests/test_cinema_markpact.py tests/test_cinema_publish.py tests/test_cinema_offline_options.py

  loop:
    max_iterations: 1
    on_fail: report
```

## Configuration

```yaml
project:
  name: nexu
  version: 0.5.17
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
- **version files**: `VERSION`, `pyproject.toml:version`, `.venv/lib/python3.13/site-packages/httpcore/__init__.py:__version__`

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
# nexu | 86f 9431L | python:82,shell:3,less:1 | 2026-05-31
# stats: 339 func | 15 cls | 86 mod | CC̄=4.0 | critical:27 | cycles:0
# alerts[5]: CC build_markpact_readme=18; CC start_published_service=17; CC write_goal_options_offline=16; CC activate_example_project=16; CC _write_service_readme=14
# hotspots[5]: run_example fan=23; activate_example_project fan=21; create_capsule fan=20; build_review_packet fan=19; start_published_service fan=18
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[86]:
  app.doql.less,117
  examples/backend_service/app/users.py,9
  examples/frontend_view/src/menu_icons.py,25
  examples/mcp_service/src/demo.py,11
  examples/nexu_markpact_exporter.py,96
  examples/realtime_lane_nexu_sync.py,63
  examples/run_examples.py,80
  examples/scientific_calculator_demo.py,62
  examples/scientific_calculator_demo2.py,87
  examples/vertical_slice/src/flow.py,10
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
  scripts/ci-cinema-smoke.sh,49
  src/nexu/__init__.py,6
  src/nexu/__main__.py,5
  src/nexu/blueprint.py,74
  src/nexu/bundle.py,56
  src/nexu/capsule.py,125
  src/nexu/cinema.py,200
  src/nexu/cinema_baseline_contracts.py,185
  src/nexu/cinema_history.py,245
  src/nexu/cinema_markpact.py,121
  src/nexu/cinema_offline_options.py,521
  src/nexu/cinema_policy.py,656
  src/nexu/cinema_projects.py,360
  src/nexu/cinema_publish.py,460
  src/nexu/cinema_scripts.py,623
  src/nexu/cinema_server.py,120
  src/nexu/cli.py,380
  src/nexu/config.py,122
  src/nexu/diff.py,36
  src/nexu/drift.py,37
  src/nexu/export_prompt.py,161
  src/nexu/files.py,52
  src/nexu/freeze.py,27
  src/nexu/git.py,23
  src/nexu/hashing.py,17
  src/nexu/init_project.py,87
  src/nexu/intract.py,136
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
  tests/test_cinema_history.py,50
  tests/test_cinema_markpact.py,45
  tests/test_cinema_offline_options.py,106
  tests/test_cinema_policy.py,187
  tests/test_cinema_projects.py,70
  tests/test_cinema_publish.py,99
  tests/test_cinema_scripts.py,15
  tests/test_cinema_server.py,71
  tests/test_cinema_spatial_patch.py,17
  tests/test_export_prompt_ledger.py,42
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
    e: _cinema_template_text,_render_cinema_template,write_cinema_nexu_hooks,_contract_to_public_dict,format_intract_v1_line,build_intract_policy_snapshot,write_intract_policy_files,generate_cinema_player,_start_cinema_server
    _cinema_template_text(name)
    _render_cinema_template(name)
    write_cinema_nexu_hooks(cinema_dir;root;name)
    _contract_to_public_dict(contract)
    format_intract_v1_line(contract)
    build_intract_policy_snapshot(root;name)
    write_intract_policy_files(cinema_dir;root;name)
    generate_cinema_player(root;name)
    _start_cinema_server(cinema_dir;root;name)
  src/nexu/cinema_baseline_contracts.py:
    e: _line,_contract,calculator_baseline_contracts,is_calculator_capsule,merge_calculator_baselines,ensure_capsule_intract_yaml
    _line(contract)
    _contract(contract_id;intent;meaning)
    calculator_baseline_contracts()
    is_calculator_capsule(root;name)
    merge_calculator_baselines(capsule_contracts;root;name)
    ensure_capsule_intract_yaml(root;name)
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
  src/nexu/cinema_markpact.py:
    e: _escape_markdown_fence,build_markpact_readme,markpact_download_filename
    _escape_markdown_fence(text;fence)
    build_markpact_readme(cinema_dir)
    markpact_download_filename(capsule_name;stage)
  src/nexu/cinema_offline_options.py:
    e: _hints_text,is_chemical_goal,_btn,_keep_ids_lower,_mandatory_trig,_trig_row,_policy_constrained,_numpad_token_btn,_numpad_rows,_numpad_from_policy,_policy_screen_text,_expanded_excess_row,_chemical_shell,_cinema_is_calculator,_option_shell,build_policy_scientific_option_html,build_chemical_option_html,_render_packaged_alt,write_goal_options_offline
    _hints_text(hints)
    is_chemical_goal(hints)
    _btn(label;el_id)
    _keep_ids_lower(keep_els)
    _mandatory_trig(keep_els)
    _trig_row(keep_els)
    _policy_constrained(keep_els;delete_els)
    _numpad_token_btn(token)
    _numpad_rows(cols)
    _numpad_from_policy(keep_els)
    _policy_screen_text(variant;keep_els)
    _expanded_excess_row(keep_els)
    _chemical_shell()
    _cinema_is_calculator(cinema_dir)
    _option_shell()
    build_policy_scientific_option_html(variant;keep_els)
    build_chemical_option_html(variant;keep_els)
    _render_packaged_alt(name)
    write_goal_options_offline(cinema_dir)
  src/nexu/cinema_policy.py:
    e: _process_ledger_entry,_process_keep_delete_entries,_process_proposed_contracts,_build_constraint_result,effective_ui_constraints_from_ledger,merge_ui_constraint_lists,_normalize_html_body,_html_files_distinct,option_previews_are_distinct,stage_files_are_distinct,ensure_option_previews_from_stages,_replace_html_title,sync_option_previews_from_workspace,enforce_deletes_on_option_previews,load_effective_ui_constraints,resolve_iteration_mode,normalize_manifest_target,cinema_model_label,cinema_dir_for,policy_snapshot_path,policy_ledger_path,load_policy_snapshot,manifest_paths_from_snapshot,apply_ledger_from_cinema,ensure_intract_on_path,propose_ui_delta_contract_dicts,append_policy_ledger_entry,_proposal_kind_and_element,normalize_proposals_for_ledger,append_iteration_ledger_entry,propose_llm_for_stage,validate_intract_artifact,verify_capsule_workspace
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
    _replace_html_title(html;title)
    sync_option_previews_from_workspace(cinema_dir)
    enforce_deletes_on_option_previews(cinema_dir;delete_ids)
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
    append_policy_ledger_entry(root;capsule_name;entry)
    _proposal_kind_and_element(proposal)
    normalize_proposals_for_ledger(stage;capsule_name;proposals)
    append_iteration_ledger_entry(root;capsule_name)
    propose_llm_for_stage(root;capsule_name;stage;goal)
    validate_intract_artifact(artifact;proposals)
    verify_capsule_workspace(root;capsule_name)
  src/nexu/cinema_projects.py:
    e: find_nexu_repo_root,list_project_catalog,_resolve_source_cinema,_seed_html_for_project,_copy_cinema_files,_write_seed_variants,activate_example_project,load_active_project,ExampleProject
    ExampleProject: to_public_dict(0)
    find_nexu_repo_root(start)
    list_project_catalog()
    _resolve_source_cinema(project;repo_root)
    _seed_html_for_project(project)
    _copy_cinema_files(source;cinema_dir)
    _write_seed_variants(cinema_dir;stage_html)
    activate_example_project(cinema_dir;project_id)
    load_active_project(cinema_dir)
  src/nexu/cinema_publish.py:
    e: services_root,_registry_path,_load_registry,_save_registry,_slug_service_id,_pick_port,_port_open,_http_ok,_service_alive,_refresh_service_status,list_published_services,_write_service_readme,_prepare_service_directory,_generate_markpact_export,_allocate_service_port,_create_service_entry,_register_service,_handle_existing_service,publish_project_service,start_published_service,stop_published_service
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
    start_published_service(cinema_dir;service_id)
    stop_published_service(cinema_dir;service_id)
  src/nexu/cinema_scripts.py:
    e: _delete_match_keys,apply_spatial_deletes_to_html,finalize_cinema_html,write_cinema_inject_files,repair_cinema_html_files
    _delete_match_keys(element_id)
    apply_spatial_deletes_to_html(html;delete_ids)
    finalize_cinema_html(html)
    write_cinema_inject_files(cinema_dir)
    repair_cinema_html_files(cinema_dir)
  src/nexu/cinema_server.py:
    e: _template_text,_render_server_script,_litellm_available,_try_spawn_on_port,_available_port,start_persistent_http_server,_open_browser,start_cinema_player_server
    _template_text()
    _render_server_script(root;name;llm_config;python_executable)
    _litellm_available(python_executable)
    _try_spawn_on_port(directory;port;python_executable)
    _available_port(directory;python_executable)
    start_persistent_http_server(directory;root;name)
    _open_browser(url)
    start_cinema_player_server(cinema_dir;root;name)
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
    e: _as_list,_load_env_file,load_env_files,_resolved_model_from_env,load_config,LLMConfig,ReviewConfig,nexuConfig
    LLMConfig:
    ReviewConfig:
    nexuConfig:
    _as_list(value;default)
    _load_env_file(path)
    load_env_files(root)
    _resolved_model_from_env(yaml_model)
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
  tests/test_cinema_history.py:
    e: test_save_list_and_restore_files
    test_save_list_and_restore_files(tmp_path;monkeypatch)
  tests/test_cinema_markpact.py:
    e: test_build_markpact_readme,test_markpact_download_filename
    test_build_markpact_readme(tmp_path)
    test_markpact_download_filename()
  tests/test_cinema_offline_options.py:
    e: test_is_chemical_goal,test_write_chemical_options,test_chemical_html_has_elements,test_policy_scientific_includes_mandatory_trig,test_policy_options_a_and_b_differ,test_calculator_cinema_uses_scientific_offline,test_write_policy_options_without_chemical_hints,test_write_chemical_options_respects_deletes
    test_is_chemical_goal()
    test_write_chemical_options(tmp_path)
    test_chemical_html_has_elements()
    test_policy_scientific_includes_mandatory_trig()
    test_policy_options_a_and_b_differ()
    test_calculator_cinema_uses_scientific_offline(tmp_path)
    test_write_policy_options_without_chemical_hints(tmp_path)
    test_write_chemical_options_respects_deletes(tmp_path)
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
  tests/test_cinema_projects.py:
    e: test_list_project_catalog_has_nine_examples,test_activate_example_project_seeds_when_no_source,test_activate_copies_dashboard_cinema_when_repo_available,test_activate_calculator_preserves_distinct_option_previews
    test_list_project_catalog_has_nine_examples()
    test_activate_example_project_seeds_when_no_source(tmp_path)
    test_activate_copies_dashboard_cinema_when_repo_available()
    test_activate_calculator_preserves_distinct_option_previews()
  tests/test_cinema_publish.py:
    e: cinema_setup,test_publish_creates_service_files,test_list_and_start_stop_service,test_publish_missing_stage_returns_error
    cinema_setup(tmp_path)
    test_publish_creates_service_files(cinema_setup)
    test_list_and_start_stop_service(cinema_setup)
    test_publish_missing_stage_returns_error(cinema_setup)
  tests/test_cinema_scripts.py:
    e: test_finalize_strips_truncated_llm_script_and_injects_canonical
    test_finalize_strips_truncated_llm_script_and_injects_canonical()
  tests/test_cinema_server.py:
    e: test_render_server_script_embeds_runtime_context,test_write_cinema_nexu_hooks_uses_template,test_render_stage_template_injects_runtime_scripts,test_cinema_player_template_is_externalized,test_start_cinema_player_server_returns_url_without_opening,_LLMConfig
    _LLMConfig:
    test_render_server_script_embeds_runtime_context()
    test_write_cinema_nexu_hooks_uses_template(tmp_path)
    test_render_stage_template_injects_runtime_scripts()
    test_cinema_player_template_is_externalized()
    test_start_cinema_player_server_returns_url_without_opening(monkeypatch;tmp_path)
  tests/test_cinema_spatial_patch.py:
    e: test_apply_spatial_deletes_removes_only_marked_buttons
    test_apply_spatial_deletes_removes_only_marked_buttons()
  tests/test_export_prompt_ledger.py:
    e: test_export_prompt_includes_cinema_ledger_block
    test_export_prompt_includes_cinema_ledger_block(tmp_path)
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
project_metadata('nexu', '0.5.17', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.less', 117, 'less').
project_file('examples/backend_service/app/users.py', 9, 'python').
project_file('examples/frontend_view/src/menu_icons.py', 25, 'python').
project_file('examples/mcp_service/src/demo.py', 11, 'python').
project_file('examples/nexu_markpact_exporter.py', 96, 'python').
project_file('examples/realtime_lane_nexu_sync.py', 63, 'python').
project_file('examples/run_examples.py', 80, 'python').
project_file('examples/scientific_calculator_demo.py', 62, 'python').
project_file('examples/scientific_calculator_demo2.py', 87, 'python').
project_file('examples/vertical_slice/src/flow.py', 10, 'python').
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
project_file('scripts/ci-cinema-smoke.sh', 49, 'shell').
project_file('src/nexu/__init__.py', 6, 'python').
project_file('src/nexu/__main__.py', 5, 'python').
project_file('src/nexu/blueprint.py', 74, 'python').
project_file('src/nexu/bundle.py', 56, 'python').
project_file('src/nexu/capsule.py', 125, 'python').
project_file('src/nexu/cinema.py', 190, 'python').
project_file('src/nexu/cinema_baseline_contracts.py', 185, 'python').
project_file('src/nexu/cinema_history.py', 245, 'python').
project_file('src/nexu/cinema_markpact.py', 121, 'python').
project_file('src/nexu/cinema_offline_options.py', 521, 'python').
project_file('src/nexu/cinema_policy.py', 656, 'python').
project_file('src/nexu/cinema_projects.py', 360, 'python').
project_file('src/nexu/cinema_publish.py', 460, 'python').
project_file('src/nexu/cinema_scripts.py', 623, 'python').
project_file('src/nexu/cinema_server.py', 120, 'python').
project_file('src/nexu/cli.py', 380, 'python').
project_file('src/nexu/config.py', 122, 'python').
project_file('src/nexu/diff.py', 36, 'python').
project_file('src/nexu/drift.py', 37, 'python').
project_file('src/nexu/export_prompt.py', 161, 'python').
project_file('src/nexu/files.py', 52, 'python').
project_file('src/nexu/freeze.py', 27, 'python').
project_file('src/nexu/git.py', 23, 'python').
project_file('src/nexu/hashing.py', 17, 'python').
project_file('src/nexu/init_project.py', 87, 'python').
project_file('src/nexu/intract.py', 136, 'python').
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
project_file('tests/test_cinema_history.py', 50, 'python').
project_file('tests/test_cinema_markpact.py', 45, 'python').
project_file('tests/test_cinema_offline_options.py', 106, 'python').
project_file('tests/test_cinema_policy.py', 187, 'python').
project_file('tests/test_cinema_projects.py', 70, 'python').
project_file('tests/test_cinema_publish.py', 99, 'python').
project_file('tests/test_cinema_scripts.py', 15, 'python').
project_file('tests/test_cinema_server.py', 71, 'python').
project_file('tests/test_cinema_spatial_patch.py', 17, 'python').
project_file('tests/test_export_prompt_ledger.py', 42, 'python').
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
python_function('src/nexu/cinema.py', 'write_intract_policy_files', 3, 2, 4).
python_function('src/nexu/cinema.py', 'generate_cinema_player', 2, 2, 12).
python_function('src/nexu/cinema.py', '_start_cinema_server', 3, 2, 3).
python_function('src/nexu/cinema_baseline_contracts.py', '_contract', 3, 3, 2).
python_function('src/nexu/cinema_baseline_contracts.py', 'calculator_baseline_contracts', 0, 1, 1).
python_function('src/nexu/cinema_baseline_contracts.py', 'is_calculator_capsule', 2, 5, 5).
python_function('src/nexu/cinema_baseline_contracts.py', 'merge_calculator_baselines', 3, 5, 5).
python_function('src/nexu/cinema_baseline_contracts.py', 'ensure_capsule_intract_yaml', 2, 9, 9).
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
python_function('src/nexu/cinema_markpact.py', '_escape_markdown_fence', 2, 2, 1).
python_function('src/nexu/cinema_markpact.py', 'build_markpact_readme', 1, 18, 14).
python_function('src/nexu/cinema_markpact.py', 'markpact_download_filename', 2, 2, 2).
python_function('src/nexu/cinema_offline_options.py', '_hints_text', 1, 3, 4).
python_function('src/nexu/cinema_offline_options.py', 'is_chemical_goal', 1, 2, 2).
python_function('src/nexu/cinema_offline_options.py', '_btn', 2, 3, 1).
python_function('src/nexu/cinema_offline_options.py', '_keep_ids_lower', 1, 3, 3).
python_function('src/nexu/cinema_offline_options.py', '_mandatory_trig', 1, 3, 1).
python_function('src/nexu/cinema_offline_options.py', '_trig_row', 1, 7, 4).
python_function('src/nexu/cinema_offline_options.py', '_policy_constrained', 2, 2, 1).
python_function('src/nexu/cinema_offline_options.py', '_numpad_token_btn', 1, 4, 3).
python_function('src/nexu/cinema_offline_options.py', '_numpad_rows', 1, 5, 4).
python_function('src/nexu/cinema_offline_options.py', '_numpad_from_policy', 1, 11, 10).
python_function('src/nexu/cinema_offline_options.py', '_policy_screen_text', 2, 2, 4).
python_function('src/nexu/cinema_offline_options.py', '_expanded_excess_row', 1, 8, 6).
python_function('src/nexu/cinema_offline_options.py', '_chemical_shell', 0, 1, 0).
python_function('src/nexu/cinema_offline_options.py', '_cinema_is_calculator', 1, 4, 2).
python_function('src/nexu/cinema_offline_options.py', '_option_shell', 0, 3, 1).
python_function('src/nexu/cinema_offline_options.py', 'build_policy_scientific_option_html', 2, 3, 6).
python_function('src/nexu/cinema_offline_options.py', 'build_chemical_option_html', 2, 7, 5).
python_function('src/nexu/cinema_offline_options.py', '_render_packaged_alt', 1, 1, 5).
python_function('src/nexu/cinema_offline_options.py', 'write_goal_options_offline', 1, 16, 14).
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
python_function('src/nexu/cinema_policy.py', '_replace_html_title', 2, 2, 2).
python_function('src/nexu/cinema_policy.py', 'sync_option_previews_from_workspace', 1, 10, 10).
python_function('src/nexu/cinema_policy.py', 'enforce_deletes_on_option_previews', 2, 5, 10).
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
python_function('src/nexu/cinema_policy.py', 'append_policy_ledger_entry', 3, 3, 8).
python_function('src/nexu/cinema_policy.py', '_proposal_kind_and_element', 1, 12, 3).
python_function('src/nexu/cinema_policy.py', 'normalize_proposals_for_ledger', 3, 6, 7).
python_function('src/nexu/cinema_policy.py', 'append_iteration_ledger_entry', 2, 1, 7).
python_function('src/nexu/cinema_policy.py', 'propose_llm_for_stage', 4, 8, 12).
python_function('src/nexu/cinema_policy.py', 'validate_intract_artifact', 2, 8, 4).
python_function('src/nexu/cinema_policy.py', 'verify_capsule_workspace', 2, 2, 4).
python_function('src/nexu/cinema_projects.py', 'find_nexu_repo_root', 1, 5, 3).
python_function('src/nexu/cinema_projects.py', 'list_project_catalog', 0, 6, 2).
python_function('src/nexu/cinema_projects.py', '_resolve_source_cinema', 2, 5, 2).
python_function('src/nexu/cinema_projects.py', '_seed_html_for_project', 1, 2, 2).
python_function('src/nexu/cinema_projects.py', '_copy_cinema_files', 2, 4, 4).
python_function('src/nexu/cinema_projects.py', '_write_seed_variants', 2, 3, 4).
python_function('src/nexu/cinema_projects.py', 'activate_example_project', 2, 16, 21).
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
python_function('src/nexu/cinema_publish.py', 'start_published_service', 2, 17, 18).
python_function('src/nexu/cinema_publish.py', 'stop_published_service', 2, 9, 8).
python_function('src/nexu/cinema_scripts.py', '_delete_match_keys', 1, 4, 5).
python_function('src/nexu/cinema_scripts.py', 'apply_spatial_deletes_to_html', 2, 4, 9).
python_function('src/nexu/cinema_scripts.py', 'finalize_cinema_html', 1, 6, 5).
python_function('src/nexu/cinema_scripts.py', 'write_cinema_inject_files', 1, 1, 2).
python_function('src/nexu/cinema_scripts.py', 'repair_cinema_html_files', 1, 5, 8).
python_function('src/nexu/cinema_server.py', '_template_text', 0, 1, 3).
python_function('src/nexu/cinema_server.py', '_render_server_script', 4, 1, 6).
python_function('src/nexu/cinema_server.py', '_litellm_available', 1, 1, 1).
python_function('src/nexu/cinema_server.py', '_try_spawn_on_port', 3, 2, 4).
python_function('src/nexu/cinema_server.py', '_available_port', 2, 4, 7).
python_function('src/nexu/cinema_server.py', 'start_persistent_http_server', 3, 2, 7).
python_function('src/nexu/cinema_server.py', '_open_browser', 1, 3, 2).
python_function('src/nexu/cinema_server.py', 'start_cinema_player_server', 3, 2, 3).
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
python_function('src/nexu/config.py', 'load_config', 1, 6, 13).
python_function('src/nexu/diff.py', 'diff_capsule', 2, 12, 10).
python_function('src/nexu/drift.py', 'check_source_drift', 2, 7, 9).
python_function('src/nexu/export_prompt.py', '_cinema_policy_ledger_block', 1, 12, 7).
python_function('src/nexu/export_prompt.py', '_latest_iteration', 1, 2, 0).
python_function('src/nexu/export_prompt.py', 'export_iteration_prompt', 2, 3, 15).
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
python_function('tests/test_cinema_history.py', 'test_save_list_and_restore_files', 2, 7, 9).
python_function('tests/test_cinema_markpact.py', 'test_build_markpact_readme', 1, 10, 3).
python_function('tests/test_cinema_markpact.py', 'test_markpact_download_filename', 0, 2, 1).
python_function('tests/test_cinema_offline_options.py', 'test_is_chemical_goal', 0, 4, 1).
python_function('tests/test_cinema_offline_options.py', 'test_write_chemical_options', 1, 5, 3).
python_function('tests/test_cinema_offline_options.py', 'test_chemical_html_has_elements', 0, 3, 2).
python_function('tests/test_cinema_offline_options.py', 'test_policy_scientific_includes_mandatory_trig', 0, 3, 1).
python_function('tests/test_cinema_offline_options.py', 'test_policy_options_a_and_b_differ', 0, 10, 1).
python_function('tests/test_cinema_offline_options.py', 'test_calculator_cinema_uses_scientific_offline', 1, 4, 3).
python_function('tests/test_cinema_offline_options.py', 'test_write_policy_options_without_chemical_hints', 1, 9, 2).
python_function('tests/test_cinema_offline_options.py', 'test_write_chemical_options_respects_deletes', 1, 5, 3).
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
python_function('tests/test_cinema_projects.py', 'test_list_project_catalog_has_nine_examples', 0, 3, 2).
python_function('tests/test_cinema_projects.py', 'test_activate_example_project_seeds_when_no_source', 1, 5, 5).
python_function('tests/test_cinema_projects.py', 'test_activate_copies_dashboard_cinema_when_repo_available', 0, 6, 7).
python_function('tests/test_cinema_projects.py', 'test_activate_calculator_preserves_distinct_option_previews', 0, 5, 11).
python_function('tests/test_cinema_publish.py', 'cinema_setup', 1, 1, 2).
python_function('tests/test_cinema_publish.py', 'test_publish_creates_service_files', 1, 11, 6).
python_function('tests/test_cinema_publish.py', 'test_list_and_start_stop_service', 1, 10, 8).
python_function('tests/test_cinema_publish.py', 'test_publish_missing_stage_returns_error', 1, 2, 1).
python_function('tests/test_cinema_scripts.py', 'test_finalize_strips_truncated_llm_script_and_injects_canonical', 0, 5, 3).
python_function('tests/test_cinema_server.py', 'test_render_server_script_embeds_runtime_context', 0, 8, 4).
python_function('tests/test_cinema_server.py', 'test_write_cinema_nexu_hooks_uses_template', 1, 5, 3).
python_function('tests/test_cinema_server.py', 'test_render_stage_template_injects_runtime_scripts', 0, 4, 1).
python_function('tests/test_cinema_server.py', 'test_cinema_player_template_is_externalized', 0, 4, 1).
python_function('tests/test_cinema_server.py', 'test_start_cinema_player_server_returns_url_without_opening', 2, 2, 3).
python_function('tests/test_cinema_spatial_patch.py', 'test_apply_spatial_deletes_removes_only_marked_buttons', 0, 4, 3).
python_function('tests/test_export_prompt_ledger.py', 'test_export_prompt_includes_cinema_ledger_block', 1, 3, 7).
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
python_class('src/nexu/cinema_projects.py', 'ExampleProject').
python_method('ExampleProject', 'to_public_dict', 0, 1, 2).
python_class('src/nexu/config.py', 'LLMConfig').
python_class('src/nexu/config.py', 'ReviewConfig').
python_class('src/nexu/config.py', 'nexuConfig').
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
sumd_workflow_step('quality', 1, 'ruff check src/nexu/cinema.py src/nexu/cinema_server.py src/nexu/cinema_baseline_contracts.py src/nexu/cinema_markpact.py src/nexu/cinema_publish.py src/nexu/cinema_offline_options.py src/nexu/verify.py src/nexu/intract_adapter.py tests/test_cinema_server.py tests/test_cinema_baseline_contracts.py tests/test_cinema_markpact.py tests/test_cinema_publish.py tests/test_cinema_offline_options.py').
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

*248 nodes · 414 edges · 45 modules · CC̄=3.8*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `load_config` *(in src.nexu.config)* | 6 | 4 | 42 | **46** |
| `_btn` *(in src.nexu.cinema_offline_options)* | 3 | 39 | 1 | **40** |
| `read_manifest_contracts` *(in src.vico.intract)* | 12 ⚠ | 8 | 32 | **40** |
| `build_intract_policy_snapshot` *(in src.nexu.cinema)* | 11 ⚠ | 3 | 32 | **35** |
| `main` *(in examples.web_app_dashboard.run)* | 2 | 0 | 35 | **35** |
| `build_policy_scientific_option_html` *(in src.nexu.cinema_offline_options)* | 3 | 1 | 34 | **35** |
| `build_capsule_report` *(in src.nexu.report)* | 1 | 2 | 32 | **34** |
| `verify_capsule` *(in src.nexu.verify)* | 1 | 7 | 26 | **33** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/nexu
# generated in 0.16s
# nodes: 248 | edges: 414 | modules: 45
# CC̄=3.8

HUBS[20]:
  src.nexu.config.load_config
    CC=6  in:4  out:42  total:46
  src.nexu.cinema_offline_options._btn
    CC=3  in:39  out:1  total:40
  src.vico.intract.read_manifest_contracts
    CC=12  in:8  out:32  total:40
  src.nexu.cinema.build_intract_policy_snapshot
    CC=11  in:3  out:32  total:35
  examples.web_app_dashboard.run.main
    CC=2  in:0  out:35  total:35
  src.nexu.cinema_offline_options.build_policy_scientific_option_html
    CC=3  in:1  out:34  total:35
  src.nexu.report.build_capsule_report
    CC=1  in:2  out:32  total:34
  src.nexu.verify.verify_capsule
    CC=1  in:7  out:26  total:33
  src.nexu.paths.project_root
    CC=1  in:28  out:3  total:31
  src.nexu.capsule.create_capsule
    CC=8  in:7  out:24  total:31
  src.nexu.cinema_publish.start_published_service
    CC=17  in:1  out:29  total:30
  src.nexu.orchestrate.build_capsule_orchestration
    CC=2  in:2  out:28  total:30
  examples.run_examples.run_example
    CC=2  in:1  out:26  total:27
  src.nexu.cinema_markpact.build_markpact_readme
    CC=18  in:1  out:25  total:26
  src.nexu.cinema_baseline_contracts.ensure_capsule_intract_yaml
    CC=9  in:1  out:25  total:26
  src.nexu.review.build_review_packet
    CC=5  in:2  out:24  total:26
  src.nexu.paths.capsule_dir
    CC=1  in:25  out:1  total:26
  src.nexu.cinema_publish._write_service_readme
    CC=14  in:1  out:24  total:25
  src.vico.models.write_yaml
    CC=1  in:22  out:3  total:25
  src.nexu.cinema_projects.activate_example_project
    CC=16  in:0  out:24  total:24

MODULES:
  examples.run_examples  [2 funcs]
    main  CC=2  out:1
    run_example  CC=2  out:26
  examples.scientific_calculator_demo  [1 funcs]
    main  CC=2  out:23
  examples.scientific_calculator_demo2  [2 funcs]
    main  CC=2  out:17
    print_code  CC=1  out:6
  examples.web_app_calculator.run  [1 funcs]
    main  CC=2  out:23
  examples.web_app_dashboard.run  [1 funcs]
    main  CC=2  out:35
  scripts.check-doc-links  [8 funcs]
    _anchors  CC=3  out:6
    _is_external  CC=3  out:4
    _markdown_files  CC=4  out:4
    _resolve  CC=1  out:5
    _slug  CC=1  out:5
    _targets  CC=1  out:2
    check_links  CC=12  out:21
    main  CC=3  out:7
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
    format_intract_v1_line  CC=3  out:1
    generate_cinema_player  CC=2  out:21
    write_cinema_nexu_hooks  CC=1  out:8
    write_intract_policy_files  CC=2  out:5
  src.nexu.cinema_baseline_contracts  [6 funcs]
    _contract  CC=3  out:2
    _line  CC=3  out:1
    calculator_baseline_contracts  CC=1  out:7
    ensure_capsule_intract_yaml  CC=9  out:25
    is_calculator_capsule  CC=5  out:5
    merge_calculator_baselines  CC=5  out:5
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
  src.nexu.cinema_markpact  [2 funcs]
    _escape_markdown_fence  CC=2  out:1
    build_markpact_readme  CC=18  out:25
  src.nexu.cinema_offline_options  [18 funcs]
    _btn  CC=3  out:1
    _chemical_shell  CC=1  out:0
    _cinema_is_calculator  CC=4  out:2
    _expanded_excess_row  CC=8  out:6
    _hints_text  CC=3  out:6
    _keep_ids_lower  CC=3  out:5
    _mandatory_trig  CC=3  out:1
    _numpad_from_policy  CC=11  out:11
    _numpad_rows  CC=5  out:4
    _numpad_token_btn  CC=4  out:4
  src.nexu.cinema_policy  [31 funcs]
    _build_constraint_result  CC=5  out:4
    _html_files_distinct  CC=3  out:6
    _normalize_html_body  CC=1  out:2
    _process_keep_delete_entries  CC=7  out:6
    _process_ledger_entry  CC=4  out:4
    _process_proposed_contracts  CC=8  out:3
    _proposal_kind_and_element  CC=12  out:8
    _replace_html_title  CC=2  out:2
    append_iteration_ledger_entry  CC=1  out:7
    append_policy_ledger_entry  CC=3  out:8
  src.nexu.cinema_projects  [5 funcs]
    _copy_cinema_files  CC=4  out:6
    _resolve_source_cinema  CC=5  out:2
    _write_seed_variants  CC=3  out:8
    activate_example_project  CC=16  out:24
    find_nexu_repo_root  CC=5  out:4
  src.nexu.cinema_publish  [21 funcs]
    _allocate_service_port  CC=11  out:11
    _create_service_entry  CC=3  out:2
    _generate_markpact_export  CC=1  out:5
    _handle_existing_service  CC=7  out:8
    _http_ok  CC=2  out:1
    _load_registry  CC=3  out:6
    _pick_port  CC=4  out:2
    _port_open  CC=2  out:1
    _prepare_service_directory  CC=1  out:4
    _refresh_service_status  CC=3  out:1
  src.nexu.cinema_scripts  [5 funcs]
    _delete_match_keys  CC=4  out:11
    apply_spatial_deletes_to_html  CC=4  out:14
    finalize_cinema_html  CC=6  out:6
    repair_cinema_html_files  CC=5  out:8
    write_cinema_inject_files  CC=1  out:3
  src.nexu.cinema_server  [8 funcs]
    _available_port  CC=4  out:8
    _litellm_available  CC=1  out:1
    _open_browser  CC=3  out:2
    _render_server_script  CC=1  out:11
    _template_text  CC=1  out:3
    _try_spawn_on_port  CC=2  out:5
    start_cinema_player_server  CC=2  out:3
    start_persistent_http_server  CC=2  out:7
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
    load_config  CC=6  out:42
    load_env_files  CC=3  out:3
  src.nexu.export_prompt  [2 funcs]
    _cinema_policy_ledger_block  CC=12  out:13
    export_iteration_prompt  CC=3  out:18
  src.nexu.files  [4 funcs]
    collect_files  CC=8  out:8
    is_text_file  CC=2  out:1
    matches_any  CC=3  out:4
    rel  CC=1  out:2
  src.nexu.init_project  [1 funcs]
    init_project  CC=3  out:7
  src.nexu.intract_adapter  [6 funcs]
    _ensure_intract_on_path  CC=3  out:4
    _finding_for_result  CC=9  out:16
    _policy_findings  CC=3  out:4
    _result_status  CC=1  out:3
    _sibling_intract_src  CC=4  out:3
    check_intract_policy  CC=7  out:11
  src.nexu.iterate  [1 funcs]
    iterate_capsule  CC=7  out:14
  src.nexu.journal  [3 funcs]
    append_journal  CC=2  out:6
    journal_path  CC=1  out:1
    read_journal  CC=5  out:6
  src.nexu.llm  [5 funcs]
    _extract_content  CC=4  out:5
    _strip_fences  CC=7  out:9
    call_litellm_json  CC=8  out:13
    call_litellm_review  CC=2  out:3
    offline_review_from_status  CC=4  out:0
  src.nexu.mcp_server  [12 funcs]
    _apply_promotion_from_mcp  CC=1  out:2
    _prompt_get  CC=3  out:3
    _prompts_list  CC=1  out:0
    _read_resource  CC=6  out:11
    _resource_list  CC=2  out:2
    _result_content  CC=1  out:1
    _rpc_handlers  CC=3  out:15
    _rpc_initialize  CC=1  out:1
    _tool_map  CC=2  out:2
    call_tool  CC=3  out:2
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
  src.nexu.verify  [10 funcs]
    _check_baseline_lock  CC=2  out:7
    _check_forbidden_secret  CC=7  out:4
    _check_forbidden_write  CC=6  out:5
    _check_output_presence  CC=12  out:6
    _check_source_files_presence  CC=3  out:4
    _contains_patterns  CC=3  out:2
    _find_term_evidence  CC=6  out:8
    _scan_capsule_contracts  CC=2  out:4
    _text  CC=2  out:1
    verify_capsule  CC=1  out:26
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
  src.vico.intract  [6 funcs]
    _split_csv  CC=4  out:4
    _tokenize_contract  CC=5  out:10
    parse_intract_line  CC=3  out:22
    read_manifest_contracts  CC=12  out:32
    scan_contracts_in_file  CC=3  out:5
    scan_contracts_in_text  CC=3  out:4
  src.vico.models  [4 funcs]
    from_dict  CC=2  out:6
    read_yaml  CC=3  out:4
    utc_now  CC=1  out:2
    write_yaml  CC=1  out:3
  src.vico.status  [1 funcs]
    capsule_status  CC=3  out:10

EDGES:
  examples.scientific_calculator_demo.main → src.nexu.init_project.init_project
  examples.scientific_calculator_demo.main → src.vico.freeze.freeze_project
  examples.scientific_calculator_demo.main → src.nexu.capsule.create_capsule
  examples.run_examples.run_example → src.nexu.init_project.init_project
  examples.run_examples.run_example → src.vico.freeze.freeze_project
  examples.run_examples.run_example → src.nexu.capsule.create_capsule
  examples.run_examples.run_example → src.nexu.plan.build_iteration_plan
  examples.run_examples.run_example → src.nexu.blueprint.build_blueprint
  examples.run_examples.run_example → src.nexu.iterate.iterate_capsule
  examples.run_examples.run_example → src.nexu.runtime.build_capsule_runtime
  examples.run_examples.run_example → src.nexu.export_prompt.export_iteration_prompt
  examples.run_examples.main → examples.run_examples.run_example
  examples.scientific_calculator_demo2.main → examples.scientific_calculator_demo2.print_code
  examples.scientific_calculator_demo2.main → src.nexu.init_project.init_project
  examples.scientific_calculator_demo2.main → src.vico.freeze.freeze_project
  examples.scientific_calculator_demo2.main → src.nexu.capsule.create_capsule
  examples.scientific_calculator_demo2.main → src.nexu.iterate.iterate_capsule
  examples.web_app_calculator.run.main → src.nexu.init_project.init_project
  examples.web_app_calculator.run.main → src.vico.freeze.freeze_project
  examples.web_app_calculator.run.main → src.nexu.capsule.create_capsule
  examples.web_app_dashboard.run.main → src.nexu.init_project.init_project
  examples.web_app_dashboard.run.main → src.vico.freeze.freeze_project
  examples.web_app_dashboard.run.main → src.nexu.capsule.create_capsule
  src.nexu.runtime._collect_fixtures → src.nexu.runtime._read_fixture
  src.nexu.runtime.build_capsule_runtime → src.nexu.capsule.load_capsule
  src.nexu.runtime.build_capsule_runtime → src.nexu.paths.capsule_dir
  src.nexu.runtime.build_capsule_runtime → src.nexu.blueprint.build_blueprint
  src.nexu.runtime.build_capsule_runtime → src.vico.intract.read_manifest_contracts
  src.nexu.runtime.build_capsule_runtime → src.vico.models.write_yaml
  src.nexu.runtime.build_capsule_runtime → src.nexu.journal.append_journal
  src.nexu.runtime.build_capsule_runtime → src.vico.models.utc_now
  src.nexu.init_project.init_project → src.nexu.paths.ensure_project_dirs
  src.nexu.init_project.init_project → src.vico.models.write_yaml
  src.nexu.config.load_env_files → src.nexu.config._load_env_file
  src.nexu.config.load_config → src.nexu.config.load_env_files
  src.nexu.config.load_config → src.vico.models.read_yaml
  src.vico.intract.parse_intract_line → src.vico.intract._tokenize_contract
  src.vico.intract.parse_intract_line → src.vico.intract._split_csv
  src.vico.intract.scan_contracts_in_text → src.vico.intract.parse_intract_line
  src.vico.intract.scan_contracts_in_file → src.vico.intract.scan_contracts_in_text
  src.nexu.cli.init → src.nexu.paths.project_root
  src.nexu.cli.init → src.nexu.init_project.init_project
  src.nexu.cli.freeze → src.nexu.paths.project_root
  src.nexu.cli.freeze → src.vico.freeze.freeze_project
  src.nexu.cli.capsule_create → src.nexu.paths.project_root
  src.nexu.cli.capsule_create → src.nexu.capsule.create_capsule
  src.nexu.cli.capsule_create → src.nexu.blueprint.build_blueprint
  src.nexu.cli.capsule_list → src.nexu.paths.project_root
  src.nexu.cli.capsule_list → src.nexu.capsule.list_capsules
  src.nexu.cli.capsule_status_command → src.nexu.paths.project_root
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

## Intent

Visual Intent Contract Orchestrator: freeze project slices, evolve capsules, verify intent contracts.
