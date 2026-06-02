# Nexu

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Dependencies](#dependencies)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `nexu`
- **version**: `0.5.34`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Makefile, testql(1), app.doql.less, pyqual.yaml, goal.yaml, .env.example, project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: nexu;
  version: 0.5.34;
}

dependencies {
  runtime: "pyyaml>=6.0, typer>=0.12.0, rich>=13.0, litellm>=1.0, repatch[web] @ file:///home/tom/github/semcod/repatch";
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
  step-11: run cmd=src/nexu/cinema_project_imports.py \;
  step-12: run cmd=src/nexu/cinema_projects.py \;
  step-13: run cmd=src/nexu/cinema_scripts.py \;
  step-14: run cmd=src/nexu/cinema_publish.py \;
  step-15: run cmd=src/nexu/cinema_offline_options.py \;
  step-16: run cmd=src/nexu/cinema_options_cache.py \;
  step-17: run cmd=src/nexu/fast_delivery/__init__.py \;
  step-18: run cmd=src/nexu/fast_delivery/context.py \;
  step-19: run cmd=src/nexu/fast_delivery/options.py \;
  step-20: run cmd=src/nexu/fast_delivery/router.py \;
  step-21: run cmd=src/nexu/intract.py \;
  step-22: run cmd=src/nexu/verify.py \;
  step-23: run cmd=src/nexu/intract_adapter.py \;
  step-24: run cmd=tests/test_cinema_server.py \;
  step-25: run cmd=tests/test_cinema_baseline_contracts.py \;
  step-26: run cmd=tests/test_cinema_goal_contracts.py \;
  step-27: run cmd=tests/test_cinema_markpact.py \;
  step-28: run cmd=tests/test_cinema_dom_patch.py \;
  step-29: run cmd=tests/test_cinema_project_ir.py \;
  step-30: run cmd=tests/test_cinema_project_imports.py \;
  step-31: run cmd=tests/test_cinema_projects.py \;
  step-32: run cmd=tests/test_cinema_scripts.py \;
  step-33: run cmd=tests/test_cinema_publish.py \;
  step-34: run cmd=tests/test_cinema_offline_options.py \;
  step-35: run cmd=tests/test_cinema_options_cache.py \;
  step-36: run cmd=tests/test_cinema_ui_patch.py \;
  step-37: run cmd=tests/test_fast_delivery.py;
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

workflow[name="publish-test"] {
  trigger: manual;
  step-1: run cmd=echo "🚀 Publishing to TestPyPI...";
  step-2: run cmd=bash -c 'if [ -z "$${TWINE_USERNAME}" ] && [ -z "$${TWINE_PASSWORD}" ] && [ -z "$${PYPI_API_TOKEN}" ]; then \;
  step-3: run cmd=echo "⚠️  No PyPI credentials found. Set TWINE_USERNAME and TWINE_PASSWORD or PYPI_API_TOKEN"; \;
  step-4: run cmd=echo "   Example: TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-xxx make publish-test"; \;
  step-5: run cmd=echo "   Skipping publish-test."; \;
  step-6: run cmd=else \;
  step-7: run cmd=$(PYTHON) -m venv publish-test-env && \;
  step-8: run cmd=publish-test-env/bin/pip install twine && \;
  step-9: run cmd=publish-test-env/bin/python -m twine upload --repository testpypi dist/* && \;
  step-10: run cmd=rm -rf publish-test-env && \;
  step-11: run cmd=echo "✓ Published to TestPyPI"; \;
  step-12: run cmd=fi';
}

workflow[name="bump-patch"] {
  trigger: manual;
  step-1: run cmd=echo "🔢 Bumping patch version...";
  step-2: run cmd=$(PYTHON) scripts/bump_version.py patch 2>/dev/null || echo "Create scripts/bump_version.py or edit pyproject.toml manually";
}

workflow[name="bump-minor"] {
  trigger: manual;
  step-1: run cmd=echo "🔢 Bumping minor version...";
  step-2: run cmd=$(PYTHON) scripts/bump_version.py minor 2>/dev/null || echo "Create scripts/bump_version.py or edit pyproject.toml manually";
}

workflow[name="bump-major"] {
  trigger: manual;
  step-1: run cmd=echo "🔢 Bumping major version...";
  step-2: run cmd=$(PYTHON) scripts/bump_version.py major 2>/dev/null || echo "Create scripts/bump_version.py or edit pyproject.toml manually";
}

workflow[name="publish"] {
  trigger: manual;
  step-1: run cmd=echo "🚀 Publishing to PyPI...";
  step-2: run cmd=echo "🔢 Bumping patch version...";
  step-3: run cmd=$(MAKE) bump-patch;
  step-4: run cmd=echo "🔨 Rebuilding package with new version...";
  step-5: run cmd=$(MAKE) build;
  step-6: run cmd=echo "📦 Publishing to PyPI...";
  step-7: run cmd=$(PYTHON) -m venv publish-env;
  step-8: run cmd=publish-env/bin/pip install twine;
  step-9: run cmd=publish-env/bin/python -m twine upload dist/*;
  step-10: run cmd=rm -rf publish-env;
  step-11: run cmd=echo "✓ Published to PyPI";
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

## Dependencies

### Runtime

```text markpact:deps python
pyyaml>=6.0
typer>=0.12.0
rich>=13.0
litellm>=1.0
repatch[web] @ file:///home/tom/github/semcod/repatch
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

## Call Graph

*347 nodes · 500 edges · 58 modules · CC̄=4.2*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `print` *(in scripts.ci-cinema-smoke)* | 0 | 94 | 0 | **94** |
| `load_config` *(in src.nexu.config)* | 14 ⚠ | 6 | 76 | **82** |
| `main` *(in examples.web_app_pactown_ecosystem.run)* | 8 | 0 | 39 | **39** |
| `main` *(in examples.web_app_event_monitor.run)* | 13 ⚠ | 0 | 37 | **37** |
| `build_intract_policy_snapshot` *(in src.nexu.cinema)* | 11 ⚠ | 4 | 32 | **36** |
| `main` *(in examples.web_app_dashboard.run)* | 2 | 0 | 35 | **35** |
| `build_capsule_report` *(in src.nexu.report)* | 1 | 2 | 32 | **34** |
| `_render_server_script` *(in src.nexu.cinema_server)* | 1 | 2 | 31 | **33** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/nexu
# generated in 0.17s
# nodes: 347 | edges: 500 | modules: 58
# CC̄=4.2

HUBS[20]:
  scripts.ci-cinema-smoke.print
    CC=0  in:94  out:0  total:94
  src.nexu.config.load_config
    CC=14  in:6  out:76  total:82
  examples.web_app_pactown_ecosystem.run.main
    CC=8  in:0  out:39  total:39
  examples.web_app_event_monitor.run.main
    CC=13  in:0  out:37  total:37
  src.nexu.cinema.build_intract_policy_snapshot
    CC=11  in:4  out:32  total:36
  examples.web_app_dashboard.run.main
    CC=2  in:0  out:35  total:35
  src.nexu.report.build_capsule_report
    CC=1  in:2  out:32  total:34
  src.nexu.cinema_server._render_server_script
    CC=1  in:2  out:31  total:33
  src.nexu.paths.project_root
    CC=1  in:29  out:3  total:32
  src.nexu.capsule.create_capsule
    CC=8  in:7  out:24  total:31
  src.nexu.orchestrate.build_capsule_orchestration
    CC=2  in:2  out:28  total:30
  src.nexu.cinema_offline_options._write_project_options_from_stages
    CC=13  in:1  out:26  total:27
  examples.run_examples.run_example
    CC=2  in:1  out:26  total:27
  src.nexu.cinema_baseline_contracts.ensure_capsule_intract_yaml
    CC=9  in:1  out:25  total:26
  src.nexu.review.build_review_packet
    CC=5  in:2  out:24  total:26
  src.nexu.paths.capsule_dir
    CC=1  in:25  out:1  total:26
  src.vico.models.write_yaml
    CC=1  in:22  out:3  total:25
  src.nexu.cinema_offline_options._write_scoped_calculator_options
    CC=11  in:1  out:24  total:25
  src.nexu.cinema_publish._write_service_readme
    CC=14  in:1  out:24  total:25
  src.nexu.cinema_projects._seed_html_for_project
    CC=9  in:3  out:21  total:24

MODULES:
  examples.mcp_patch_demo.server  [5 funcs]
    broadcast  CC=2  out:3
    data  CC=4  out:6
    dslCommand  CC=4  out:6
    presetDsl  CC=2  out:3
    presetName  CC=2  out:3
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
  examples.web_app_calculator.cinema.nexu_hooks  [31 funcs]
    activate_project  CC=2  out:6
    active_project  CC=1  out:3
    append_goal_policy_entry  CC=11  out:19
    append_policy_entry  CC=6  out:14
    apply_manifest_from_ledger  CC=1  out:1
    apply_spatial_patch  CC=2  out:2
    delete_imported  CC=1  out:4
    delete_service  CC=1  out:3
    delete_workspace_project  CC=1  out:4
    effective_ui_constraints  CC=2  out:3
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
  src.nexu.cinema_html  [1 funcs]
    ensure_html_document_closure  CC=5  out:3
  src.nexu.cinema_html_validate  [1 funcs]
    prepare_cinema_html_document  CC=2  out:2
  src.nexu.cinema_http_preprocess  [1 funcs]
    preprocess_cinema_seed  CC=3  out:3
  src.nexu.cinema_llm  [17 funcs]
    _as_plain_data  CC=5  out:4
    _cached_config  CC=4  out:4
    _compact_response_preview  CC=2  out:3
    _extract_content  CC=12  out:21
    _litellm_completion  CC=2  out:0
    _lookup  CC=2  out:4
    _response_shape  CC=2  out:3
    _strip_markdown_fences  CC=8  out:11
    _strip_rich_console_artifacts  CC=7  out:14
    call_cinema_html_llm  CC=12  out:8
  src.nexu.cinema_markpact  [5 funcs]
    _escape_markdown_fence  CC=2  out:1
    _get_app_title  CC=3  out:3
    _get_baseline_block  CC=6  out:4
    build_markpact_readme  CC=11  out:21
    markpact_download_filename  CC=2  out:2
  src.nexu.cinema_offline_options  [18 funcs]
    _active_is_imported  CC=5  out:7
    _active_project_meta  CC=4  out:5
    _btn  CC=3  out:1
    _cinema_is_calculator  CC=12  out:12
    _delete_without_keeps  CC=3  out:2
    _expanded_excess_row  CC=8  out:6
    _inject_goal_banner  CC=4  out:5
    _keep_ids_lower  CC=3  out:2
    _mandatory_trig  CC=3  out:1
    _normal_id  CC=5  out:6
  src.nexu.cinema_options_cache  [4 funcs]
    _digest  CC=2  out:4
    goal_slug  CC=4  out:5
    options_cache_key  CC=7  out:16
    write_options_cache  CC=5  out:14
  src.nexu.cinema_policy  [41 funcs]
    _build_constraint_result  CC=5  out:4
    _html_files_distinct  CC=1  out:1
    _intract_manifest_path  CC=4  out:4
    _ledger_entry_matches_project  CC=8  out:10
    _ledger_entry_matches_scope  CC=5  out:7
    _process_keep_delete_entries  CC=7  out:6
    _process_ledger_entry  CC=6  out:6
    _process_proposed_contracts  CC=8  out:3
    _proposal_kind_and_element  CC=12  out:8
    _replace_html_title  CC=1  out:1
  src.nexu.cinema_project_imports  [10 funcs]
    activate_imported_project  CC=4  out:6
    delete_imported_project  CC=7  out:13
    delete_project  CC=3  out:6
    import_git_project  CC=11  out:16
    import_http_project  CC=12  out:21
    import_markpact_project  CC=12  out:18
    import_zip_project  CC=5  out:13
    imported_project_llm_log  CC=8  out:14
    merged_projects_catalog  CC=10  out:13
    read_imported_markpact  CC=9  out:17
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
  src.nexu.cinema_publish  [30 funcs]
    _allocate_service_port  CC=11  out:11
    _bundle_imported_source_assets  CC=5  out:12
    _create_service_entry  CC=3  out:3
    _generate_markpact_export  CC=1  out:5
    _handle_existing_service  CC=7  out:8
    _http_ok  CC=2  out:1
    _imported_project_ids_in_html  CC=1  out:2
    _load_registry  CC=3  out:6
    _pick_port  CC=4  out:2
    _port_open  CC=2  out:1
  src.nexu.cinema_scope  [2 funcs]
    scope_meta_for_project  CC=1  out:3
    scope_option_variants  CC=12  out:2
  src.nexu.cinema_scripts  [3 funcs]
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
  examples.mcp_patch_demo.server.data → examples.mcp_patch_demo.server.broadcast
  examples.mcp_patch_demo.server.dslCommand → examples.mcp_patch_demo.server.broadcast
  examples.mcp_patch_demo.server.presetName → examples.mcp_patch_demo.server.broadcast
  examples.mcp_patch_demo.server.presetDsl → examples.mcp_patch_demo.server.broadcast
  examples.web_app_calculator.run.main → src.nexu.init_project.init_project
  examples.web_app_calculator.run.main → src.vico.freeze.freeze_project
  examples.web_app_calculator.run.main → scripts.ci-cinema-smoke.print
  examples.web_app_calculator.run.main → src.nexu.capsule.create_capsule
  examples.web_app_calculator.cinema.nexu_hooks.apply_manifest_from_ledger → src.nexu.cinema_policy.apply_ledger_from_cinema
  examples.web_app_calculator.cinema.nexu_hooks.verify_capsule → src.nexu.cinema_policy.verify_capsule_workspace
  examples.web_app_calculator.cinema.nexu_hooks.apply_spatial_patch → src.nexu.cinema_scripts.finalize_cinema_html
  examples.web_app_calculator.cinema.nexu_hooks.propose_llm → src.nexu.cinema_policy.propose_llm_for_stage
  examples.web_app_calculator.cinema.nexu_hooks.append_policy_entry → src.nexu.cinema_policy.append_iteration_ledger_entry
  examples.web_app_calculator.cinema.nexu_hooks.append_policy_entry → src.nexu.cinema_projects.load_active_project
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
  examples.web_app_calculator.cinema.nexu_hooks.patch_option_previews → src.nexu.cinema_policy.promote_applies_spatial_deletes
  examples.web_app_calculator.cinema.nexu_hooks.patch_option_previews → src.nexu.cinema_policy.merge_ui_constraint_lists
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/nexu
# generated in 0.17s
# nodes: 347 | edges: 500 | modules: 58
# CC̄=4.2

HUBS[20]:
  scripts.ci-cinema-smoke.print
    CC=0  in:94  out:0  total:94
  src.nexu.config.load_config
    CC=14  in:6  out:76  total:82
  examples.web_app_pactown_ecosystem.run.main
    CC=8  in:0  out:39  total:39
  examples.web_app_event_monitor.run.main
    CC=13  in:0  out:37  total:37
  src.nexu.cinema.build_intract_policy_snapshot
    CC=11  in:4  out:32  total:36
  examples.web_app_dashboard.run.main
    CC=2  in:0  out:35  total:35
  src.nexu.report.build_capsule_report
    CC=1  in:2  out:32  total:34
  src.nexu.cinema_server._render_server_script
    CC=1  in:2  out:31  total:33
  src.nexu.paths.project_root
    CC=1  in:29  out:3  total:32
  src.nexu.capsule.create_capsule
    CC=8  in:7  out:24  total:31
  src.nexu.orchestrate.build_capsule_orchestration
    CC=2  in:2  out:28  total:30
  src.nexu.cinema_offline_options._write_project_options_from_stages
    CC=13  in:1  out:26  total:27
  examples.run_examples.run_example
    CC=2  in:1  out:26  total:27
  src.nexu.cinema_baseline_contracts.ensure_capsule_intract_yaml
    CC=9  in:1  out:25  total:26
  src.nexu.review.build_review_packet
    CC=5  in:2  out:24  total:26
  src.nexu.paths.capsule_dir
    CC=1  in:25  out:1  total:26
  src.vico.models.write_yaml
    CC=1  in:22  out:3  total:25
  src.nexu.cinema_offline_options._write_scoped_calculator_options
    CC=11  in:1  out:24  total:25
  src.nexu.cinema_publish._write_service_readme
    CC=14  in:1  out:24  total:25
  src.nexu.cinema_projects._seed_html_for_project
    CC=9  in:3  out:21  total:24

MODULES:
  examples.mcp_patch_demo.server  [5 funcs]
    broadcast  CC=2  out:3
    data  CC=4  out:6
    dslCommand  CC=4  out:6
    presetDsl  CC=2  out:3
    presetName  CC=2  out:3
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
  examples.web_app_calculator.cinema.nexu_hooks  [31 funcs]
    activate_project  CC=2  out:6
    active_project  CC=1  out:3
    append_goal_policy_entry  CC=11  out:19
    append_policy_entry  CC=6  out:14
    apply_manifest_from_ledger  CC=1  out:1
    apply_spatial_patch  CC=2  out:2
    delete_imported  CC=1  out:4
    delete_service  CC=1  out:3
    delete_workspace_project  CC=1  out:4
    effective_ui_constraints  CC=2  out:3
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
  src.nexu.cinema_html  [1 funcs]
    ensure_html_document_closure  CC=5  out:3
  src.nexu.cinema_html_validate  [1 funcs]
    prepare_cinema_html_document  CC=2  out:2
  src.nexu.cinema_http_preprocess  [1 funcs]
    preprocess_cinema_seed  CC=3  out:3
  src.nexu.cinema_llm  [17 funcs]
    _as_plain_data  CC=5  out:4
    _cached_config  CC=4  out:4
    _compact_response_preview  CC=2  out:3
    _extract_content  CC=12  out:21
    _litellm_completion  CC=2  out:0
    _lookup  CC=2  out:4
    _response_shape  CC=2  out:3
    _strip_markdown_fences  CC=8  out:11
    _strip_rich_console_artifacts  CC=7  out:14
    call_cinema_html_llm  CC=12  out:8
  src.nexu.cinema_markpact  [5 funcs]
    _escape_markdown_fence  CC=2  out:1
    _get_app_title  CC=3  out:3
    _get_baseline_block  CC=6  out:4
    build_markpact_readme  CC=11  out:21
    markpact_download_filename  CC=2  out:2
  src.nexu.cinema_offline_options  [18 funcs]
    _active_is_imported  CC=5  out:7
    _active_project_meta  CC=4  out:5
    _btn  CC=3  out:1
    _cinema_is_calculator  CC=12  out:12
    _delete_without_keeps  CC=3  out:2
    _expanded_excess_row  CC=8  out:6
    _inject_goal_banner  CC=4  out:5
    _keep_ids_lower  CC=3  out:2
    _mandatory_trig  CC=3  out:1
    _normal_id  CC=5  out:6
  src.nexu.cinema_options_cache  [4 funcs]
    _digest  CC=2  out:4
    goal_slug  CC=4  out:5
    options_cache_key  CC=7  out:16
    write_options_cache  CC=5  out:14
  src.nexu.cinema_policy  [41 funcs]
    _build_constraint_result  CC=5  out:4
    _html_files_distinct  CC=1  out:1
    _intract_manifest_path  CC=4  out:4
    _ledger_entry_matches_project  CC=8  out:10
    _ledger_entry_matches_scope  CC=5  out:7
    _process_keep_delete_entries  CC=7  out:6
    _process_ledger_entry  CC=6  out:6
    _process_proposed_contracts  CC=8  out:3
    _proposal_kind_and_element  CC=12  out:8
    _replace_html_title  CC=1  out:1
  src.nexu.cinema_project_imports  [10 funcs]
    activate_imported_project  CC=4  out:6
    delete_imported_project  CC=7  out:13
    delete_project  CC=3  out:6
    import_git_project  CC=11  out:16
    import_http_project  CC=12  out:21
    import_markpact_project  CC=12  out:18
    import_zip_project  CC=5  out:13
    imported_project_llm_log  CC=8  out:14
    merged_projects_catalog  CC=10  out:13
    read_imported_markpact  CC=9  out:17
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
  src.nexu.cinema_publish  [30 funcs]
    _allocate_service_port  CC=11  out:11
    _bundle_imported_source_assets  CC=5  out:12
    _create_service_entry  CC=3  out:3
    _generate_markpact_export  CC=1  out:5
    _handle_existing_service  CC=7  out:8
    _http_ok  CC=2  out:1
    _imported_project_ids_in_html  CC=1  out:2
    _load_registry  CC=3  out:6
    _pick_port  CC=4  out:2
    _port_open  CC=2  out:1
  src.nexu.cinema_scope  [2 funcs]
    scope_meta_for_project  CC=1  out:3
    scope_option_variants  CC=12  out:2
  src.nexu.cinema_scripts  [3 funcs]
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
  examples.mcp_patch_demo.server.data → examples.mcp_patch_demo.server.broadcast
  examples.mcp_patch_demo.server.dslCommand → examples.mcp_patch_demo.server.broadcast
  examples.mcp_patch_demo.server.presetName → examples.mcp_patch_demo.server.broadcast
  examples.mcp_patch_demo.server.presetDsl → examples.mcp_patch_demo.server.broadcast
  examples.web_app_calculator.run.main → src.nexu.init_project.init_project
  examples.web_app_calculator.run.main → src.vico.freeze.freeze_project
  examples.web_app_calculator.run.main → scripts.ci-cinema-smoke.print
  examples.web_app_calculator.run.main → src.nexu.capsule.create_capsule
  examples.web_app_calculator.cinema.nexu_hooks.apply_manifest_from_ledger → src.nexu.cinema_policy.apply_ledger_from_cinema
  examples.web_app_calculator.cinema.nexu_hooks.verify_capsule → src.nexu.cinema_policy.verify_capsule_workspace
  examples.web_app_calculator.cinema.nexu_hooks.apply_spatial_patch → src.nexu.cinema_scripts.finalize_cinema_html
  examples.web_app_calculator.cinema.nexu_hooks.propose_llm → src.nexu.cinema_policy.propose_llm_for_stage
  examples.web_app_calculator.cinema.nexu_hooks.append_policy_entry → src.nexu.cinema_policy.append_iteration_ledger_entry
  examples.web_app_calculator.cinema.nexu_hooks.append_policy_entry → src.nexu.cinema_projects.load_active_project
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
  examples.web_app_calculator.cinema.nexu_hooks.patch_option_previews → src.nexu.cinema_policy.promote_applies_spatial_deletes
  examples.web_app_calculator.cinema.nexu_hooks.patch_option_previews → src.nexu.cinema_policy.merge_ui_constraint_lists
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 100f 15609L | python:77,yaml:9,json:3,txt:2,shell:2,javascript:2,toml:1,yml:1 | 2026-06-02
# generated in 0.02s
# CC̅=4.2 | critical:2/598 | dups:0 | cycles:0

HEALTH[2]:
  🟡 CC    propose_goal_extension_contracts CC=15 (limit:15)
  🟡 CC    start_published_service CC=15 (limit:15)

REFACTOR[1]:
  1. split 2 high-CC methods  (CC>15)

PIPELINES[145]:
  [1] Src [main]: main → print
      PURITY: 100% pure
  [2] Src [main]: main → print
      PURITY: 100% pure
  [3] Src [simulate_realtime_sync]: simulate_realtime_sync → print
      PURITY: 100% pure
  [4] Src [main]: main → run_example → init_project → ensure_project_dirs → ...(1 more)
      PURITY: 100% pure
  [5] Src [main]: main → print_code → print
      PURITY: 100% pure
  [6] Src [main]: main → print
      PURITY: 100% pure
  [7] Src [express]: express
      PURITY: 100% pure
  [8] Src [http]: http
      PURITY: 100% pure
  [9] Src [WebSocket]: WebSocket
      PURITY: 100% pure
  [10] Src [path]: path
      PURITY: 100% pure
  [11] Src [app]: app
      PURITY: 100% pure
  [12] Src [port]: port
      PURITY: 100% pure
  [13] Src [server]: server
      PURITY: 100% pure
  [14] Src [wss]: wss
      PURITY: 100% pure
  [15] Src [data]: data → broadcast
      PURITY: 100% pure
  [16] Src [dslCommand]: dslCommand → broadcast
      PURITY: 100% pure
  [17] Src [presetName]: presetName → broadcast
      PURITY: 100% pure
  [18] Src [presetDsl]: presetDsl → broadcast
      PURITY: 100% pure
  [19] Src [serialized]: serialized
      PURITY: 100% pure
  [20] Src [main]: main → init_project → ensure_project_dirs → nexu_dir
      PURITY: 100% pure
  [21] Src [apply_manifest_from_ledger]: apply_manifest_from_ledger → apply_ledger_from_cinema → project_root
      PURITY: 100% pure
  [22] Src [apply_spatial_patch]: apply_spatial_patch → finalize_cinema_html
      PURITY: 100% pure
  [23] Src [propose_llm]: propose_llm → propose_llm_for_stage → cinema_dir_for → capsule_dir → ...(2 more)
      PURITY: 100% pure
  [24] Src [append_policy_entry]: append_policy_entry → append_iteration_ledger_entry → normalize_proposals_for_ledger → _proposal_kind_and_element
      PURITY: 100% pure
  [25] Src [append_goal_policy_entry]: append_goal_policy_entry → append_goal_ledger_entry → normalize_proposals_for_ledger → _proposal_kind_and_element
      PURITY: 100% pure
  [26] Src [goal_contract_lines]: goal_contract_lines → load_goal_contract_lines → _resolve_ledger_path → policy_ledger_path → ...(4 more)
      PURITY: 100% pure
  [27] Src [validate_artifact]: validate_artifact → validate_intract_artifact → ensure_intract_on_path → project_root
      PURITY: 100% pure
  [28] Src [save_history]: save_history → save_history_checkpoint → _load_index → history_index_path → ...(1 more)
      PURITY: 100% pure
  [29] Src [list_history]: list_history → list_history_checkpoints → _load_index → history_index_path → ...(1 more)
      PURITY: 100% pure
  [30] Src [restore_history]: restore_history → restore_history_checkpoint → project_root
      PURITY: 100% pure
  [31] Src [effective_ui_constraints]: effective_ui_constraints → load_effective_ui_constraints → effective_ui_constraints_from_ledger → _build_constraint_result
      PURITY: 100% pure
  [32] Src [sync_option_previews]: sync_option_previews → sync_option_previews_from_workspace → load_effective_ui_constraints → effective_ui_constraints_from_ledger → ...(1 more)
      PURITY: 100% pure
  [33] Src [patch_option_previews]: patch_option_previews → load_effective_ui_constraints → effective_ui_constraints_from_ledger → _build_constraint_result
      PURITY: 100% pure
  [34] Src [projects_catalog]: projects_catalog → merged_projects_catalog → list_project_catalog → deleted_project_ids
      PURITY: 100% pure
  [35] Src [activate_project]: activate_project → activate_example_project → _find_example_project
      PURITY: 100% pure
  [36] Src [import_project_from_zip]: import_project_from_zip → import_zip_project → _project_dir → _imports_root
      PURITY: 100% pure
  [37] Src [import_project_from_git]: import_project_from_git → import_git_project → _validate_git_url
      PURITY: 100% pure
  [38] Src [import_project_from_http]: import_project_from_http → import_http_project → _project_dir → _imports_root
      PURITY: 100% pure
  [39] Src [import_project_from_markpact]: import_project_from_markpact → import_markpact_project → _title_from_markpact_content
      PURITY: 100% pure
  [40] Src [delete_imported]: delete_imported → find_nexu_repo_root
      PURITY: 100% pure
  [41] Src [delete_workspace_project]: delete_workspace_project → find_nexu_repo_root
      PURITY: 100% pure
  [42] Src [imported_markpact]: imported_markpact → read_imported_markpact → normalize_imported_project_id
      PURITY: 100% pure
  [43] Src [imported_llm_log]: imported_llm_log → imported_project_llm_log → normalize_imported_project_id
      PURITY: 100% pure
  [44] Src [active_project]: active_project → load_active_project
      PURITY: 100% pure
  [45] Src [export_markpact_readme]: export_markpact_readme → load_effective_ui_constraints → effective_ui_constraints_from_ledger → _build_constraint_result
      PURITY: 100% pure
  [46] Src [services_catalog]: services_catalog → list_published_services → _load_registry → _registry_path → ...(1 more)
      PURITY: 100% pure
  [47] Src [publish_service]: publish_service → publish_project_service → _slug_service_id
      PURITY: 100% pure
  [48] Src [start_service]: start_service → start_published_service → _load_registry → _registry_path → ...(1 more)
      PURITY: 100% pure
  [49] Src [stop_service]: stop_service → stop_published_service → _load_registry → _registry_path → ...(1 more)
      PURITY: 100% pure
  [50] Src [delete_service]: delete_service → delete_published_service → _validate_service_id
      PURITY: 100% pure

LAYERS:
  src/                            CC̄=4.5    ←in:0  →out:0
  │ !! cinema_project_imports    1683L  0C   80m  CC=12     ←1
  │ !! cinema_policy              914L  0C   44m  CC=14     ←6
  │ !! cinema_offline_options     901L  0C   32m  CC=13     ←0
  │ !! cinema_projects            720L  1C   25m  CC=14     ←4
  │ !! cinema_scripts             712L  0C    4m  CC=6      ←5
  │ !! cinema_http_preprocess     687L  1C   32m  CC=13     ←3
  │ !! cinema_publish             602L  0C   30m  CC=15     ←2
  │ mcp_server                 393L  0C   13m  CC=6      ←1
  │ cli                        379L  0C   23m  CC=4      ←0
  │ !! cinema_goal_contracts      345L  0C   15m  CC=15     ←2
  │ cinema_llm                 332L  0C   18m  CC=12     ←0
  │ verify                     325L  0C   14m  CC=12     ←0
  │ cinema_scope               253L  0C    5m  CC=12     ←3
  │ cinema_history             244L  0C   13m  CC=8      ←2
  │ orchestrate                232L  0C    6m  CC=13     ←2
  │ cinema_markpact            215L  0C    7m  CC=14     ←2
  │ cinema_html_validate       205L  0C   13m  CC=12     ←2
  │ cinema_llm_contracts       196L  0C    7m  CC=9      ←0
  │ cinema                     194L  0C    9m  CC=11     ←6
  │ config                     191L  4C    6m  CC=14     ←6
  │ cinema_baseline_contracts   173L  0C    5m  CC=9      ←2
  │ cinema_traces              166L  0C    7m  CC=9      ←1
  │ llm                        165L  0C    5m  CC=8      ←2
  │ export_prompt              160L  0C    3m  CC=12     ←4
  │ review                     157L  0C    2m  CC=5      ←2
  │ cinema_server              144L  0C    8m  CC=4      ←2
  │ intract_adapter            133L  0C    6m  CC=9      ←1
  │ runtime                    131L  0C    4m  CC=9      ←4
  │ cinema_options_cache       128L  0C    8m  CC=9      ←1
  │ options                    128L  0C    5m  CC=11     ←0
  │ capsule                    124L  0C    5m  CC=8      ←18
  │ report                      94L  0C    3m  CC=2      ←2
  │ promote                     92L  0C    3m  CC=6      ←3
  │ init_project                86L  0C    1m  CC=3      ←6
  │ plan                        81L  0C    2m  CC=9      ←4
  │ blueprint                   73L  0C    1m  CC=7      ←7
  │ router                      68L  1C    3m  CC=9      ←0
  │ cinema_iterate              66L  0C    1m  CC=11     ←0
  │ context                     66L  0C    3m  CC=9      ←0
  │ bundle                      55L  0C    2m  CC=5      ←2
  │ files                       51L  0C    4m  CC=8      ←7
  │ intract                     46L  0C    0m  CC=0.0    ←0
  │ iterate                     44L  0C    1m  CC=7      ←5
  │ journal                     43L  0C    3m  CC=5      ←8
  │ paths                       35L  0C    6m  CC=2      ←23
  │ cinema_dom_patch            27L  0C    1m  CC=1      ←0
  │ __init__                    24L  0C    0m  CC=0.0    ←0
  │ cinema_html                 16L  0C    1m  CC=5      ←2
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ freeze                       0L  0C    1m  CC=2      ←6
  │ status                       0L  0C    1m  CC=3      ←3
  │ drift                        0L  0C    1m  CC=7      ←5
  │ git                          0L  0C    1m  CC=4      ←2
  │ hashing                      0L  0C    2m  CC=2      ←4
  │ models                       0L  9C   10m  CC=3      ←20
  │ diff                         0L  0C    1m  CC=12     ←9
  │ __main__                     0L  0C    0m  CC=0.0    ←0
  │
  deploy/                         CC̄=4.0    ←in:0  →out:0
  │ cinema_serve                53L  0C    1m  CC=4      ←0
  │ Dockerfile                  53L  0C    0m  CC=0.0    ←0
  │
  scripts/                        CC̄=3.1    ←in:91  →out:0
  │ check-doc-links            114L  0C    8m  CC=12     ←0
  │ ci-cinema-smoke.sh          85L  0C    1m  CC=0.0    ←12
  │
  sdk/                            CC̄=2.8    ←in:0  →out:0
  │ repatch-sdk.js             186L  1C   18m  CC=12     ←0
  │
  examples/                       CC̄=2.2    ←in:0  →out:60  !! split
  │ nexu_hooks                 353L  0C   31m  CC=11     ←7
  │ run                        118L  0C    1m  CC=2      ←0
  │ run                        110L  0C    1m  CC=2      ←0
  │ run                         97L  0C    1m  CC=8      ←0
  │ nexu_markpact_exporter      95L  0C    1m  CC=3      ←0
  │ run                         90L  0C    1m  CC=13     ←0
  │ server.js                   87L  0C   14m  CC=4      ←0
  │ scientific_calculator_demo2    86L  0C    2m  CC=2      ←0
  │ run_examples                79L  0C    2m  CC=2      ←0
  │ docker-compose.yml          70L  0C    0m  CC=0.0    ←0
  │ realtime_lane_nexu_sync     62L  0C    1m  CC=2      ←0
  │ scientific_calculator_demo    61L  0C    1m  CC=2      ←0
  │ nexu.yaml                   54L  0C    0m  CC=0.0    ←0
  │ nexu.yaml                   42L  0C    0m  CC=0.0    ←0
  │ calculator                  38L  0C    1m  CC=1      ←0
  │ calculator                  38L  0C    1m  CC=1      ←0
  │ pactown.yaml                31L  0C    0m  CC=0.0    ←0
  │ intract.yaml                30L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  27L  0C    0m  CC=0.0    ←0
  │ menu_icons                  24L  0C    1m  CC=3      ←0
  │ dashboard                   24L  0C    1m  CC=2      ←0
  │ pactown.yaml                19L  0C    0m  CC=0.0    ←0
  │ package.json                14L  0C    0m  CC=0.0    ←0
  │ dashboard                   10L  0C    1m  CC=1      ←0
  │ demo                        10L  0C    1m  CC=1      ←0
  │ flow                         9L  0C    1m  CC=1      ←0
  │ users                        8L  0C    1m  CC=4      ←0
  │ menu_items.yaml              7L  0C    0m  CC=0.0    ←0
  │ dashboard_data.json          6L  0C    0m  CC=0.0    ←0
  │ inputs.json                  4L  0C    0m  CC=0.0    ←0
  │ requirements.txt             1L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! goal.yaml                  512L  0C    0m  CC=0.0    ←0
  │ tree.txt                   272L  0C    0m  CC=0.0    ←0
  │ Makefile                   142L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              89L  0C    0m  CC=0.0    ←0
  │ project.sh                  50L  0C    0m  CC=0.0    ←0
  │ pyqual.yaml                 25L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-cli-tests.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     src/vico/__main__.py                      0L
     src/vico/diff.py                          0L
     src/vico/drift.py                         0L
     src/vico/freeze.py                        0L
     src/vico/git.py                           0L
     src/vico/hashing.py                       0L
     src/vico/models.py                        0L
     src/vico/status.py                        0L

COUPLING:
                                                                src.nexu                             scripts                            src.vico                            examples         examples.web_app_calculator  examples.web_app_pactown_ecosystem          examples.web_app_dashboard      examples.web_app_event_monitor                       deploy.docker
                            src.nexu                                  ──                                   2                                  53                                 ←20                                   6                                                                      ←9                                                                      ←6  hub
                             scripts                                  ←2                                  ──                                                                     ←34                                  ←4                                 ←22                                 ←10                                 ←19                                      hub
                            src.vico                                  12                                                                      ──                                  ←5                                  ←1                                                                      ←1                                                                          hub
                            examples                                  20                                  34                                   5                                  ──                                   1                                                                                                                                                  !! fan-out
         examples.web_app_calculator                                  48                                   4                                   1                                  ←1                                  ──                                                                                                                                                  hub
  examples.web_app_pactown_ecosystem                                                                      22                                                                                                                                              ──                                                                                                              !! fan-out
          examples.web_app_dashboard                                   9                                  10                                   1                                                                                                                                              ──                                                                          !! fan-out
      examples.web_app_event_monitor                                                                      19                                                                                                                                                                                                                      ──                                      !! fan-out
                       deploy.docker                                   6                                                                                                                                                                                                                                                                                              ──
  CYCLES: none
  HUB: src.nexu/ (fan-in=95)
  HUB: examples.web_app_calculator/ (fan-in=7)
  HUB: src.vico/ (fan-in=60)
  HUB: scripts/ (fan-in=91)
  SMELL: examples.web_app_dashboard/ fan-out=20 → split needed
  SMELL: src.nexu/ fan-out=61 → split needed
  SMELL: examples.web_app_calculator/ fan-out=53 → split needed
  SMELL: src.vico/ fan-out=12 → split needed
  SMELL: examples.web_app_event_monitor/ fan-out=19 → split needed
  SMELL: examples.web_app_pactown_ecosystem/ fan-out=22 → split needed
  SMELL: examples/ fan-out=60 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 8 groups | 79f 17364L | 2026-06-02

SUMMARY:
  files_scanned: 79
  total_lines:   17364
  dup_groups:    8
  dup_fragments: 19
  saved_lines:   128
  scan_ms:       2721

HOTSPOTS[7] (files with most duplication):
  examples/web_app_calculator/cinema/nexu_hooks.py  dup=59L  groups=4  frags=10  (0.3%)
  examples/web_app_calculator/markpact_sandbox/sandbox/src/calculator.py  dup=37L  groups=1  frags=1  (0.2%)
  examples/web_app_calculator/src/calculator.py  dup=37L  groups=1  frags=1  (0.2%)
  examples/web_app_calculator/workspace/src/calculator.py  dup=37L  groups=1  frags=1  (0.2%)
  src/nexu/cinema_goal_contracts.py  dup=34L  groups=1  frags=2  (0.2%)
  src/nexu/cinema_policy.py  dup=8L  groups=1  frags=2  (0.0%)
  src/nexu/cinema_html_validate.py  dup=3L  groups=1  frags=1  (0.0%)

DUPLICATES[8] (ranked by impact):
  [f3aa7c7e1fe24b1d] ! EXAC  render_calculator  L=37 N=3 saved=74 sim=1.00
      examples/web_app_calculator/markpact_sandbox/sandbox/src/calculator.py:2-38  (render_calculator)
      examples/web_app_calculator/src/calculator.py:2-38  (render_calculator)
      examples/web_app_calculator/workspace/src/calculator.py:2-38  (render_calculator)
  [48ce0f91dd3f86de]   STRU  _detect_minimal_trait  L=17 N=2 saved=17 sim=1.00
      src/nexu/cinema_goal_contracts.py:143-159  (_detect_minimal_trait)
      src/nexu/cinema_goal_contracts.py:162-178  (_detect_expanded_trait)
  [7c8ae0bd1ddf68cf]   STRU  delete_imported  L=10 N=2 saved=10 sim=1.00
      examples/web_app_calculator/cinema/nexu_hooks.py:266-275  (delete_imported)
      examples/web_app_calculator/cinema/nexu_hooks.py:278-287  (delete_workspace_project)
  [cecd75a67622a9fb]   STRU  imported_markpact  L=3 N=4 saved=9 sim=1.00
      examples/web_app_calculator/cinema/nexu_hooks.py:290-292  (imported_markpact)
      examples/web_app_calculator/cinema/nexu_hooks.py:341-343  (start_service)
      examples/web_app_calculator/cinema/nexu_hooks.py:346-348  (stop_service)
      examples/web_app_calculator/cinema/nexu_hooks.py:351-353  (delete_service)
  [f434dfddb54cc94d]   STRU  import_project_from_zip  L=8 N=2 saved=8 sim=1.00
      examples/web_app_calculator/cinema/nexu_hooks.py:226-233  (import_project_from_zip)
      examples/web_app_calculator/cinema/nexu_hooks.py:251-263  (import_project_from_markpact)
  [3e7f254259144cfa]   STRU  option_previews_are_distinct  L=4 N=2 saved=4 sim=1.00
      src/nexu/cinema_policy.py:206-209  (option_previews_are_distinct)
      src/nexu/cinema_policy.py:212-215  (stage_files_are_distinct)
  [20e75f93cb3619db]   STRU  projects_catalog  L=3 N=2 saved=3 sim=1.00
      examples/web_app_calculator/cinema/nexu_hooks.py:207-209  (projects_catalog)
      examples/web_app_calculator/cinema/nexu_hooks.py:322-324  (services_catalog)
  [e7ad03f571bde886]   STRU  _looks_like_html_document  L=3 N=2 saved=3 sim=1.00
      src/nexu/cinema_html_validate.py:32-34  (_looks_like_html_document)
      src/nexu/cinema_llm.py:81-83  (looks_like_html_document)

REFACTOR[8] (ranked by priority):
  [1] ◐ extract_function   → examples/web_app_calculator/utils/render_calculator.py
      WHY: 3 occurrences of 37-line block across 3 files — saves 74 lines
      FILES: examples/web_app_calculator/markpact_sandbox/sandbox/src/calculator.py, examples/web_app_calculator/src/calculator.py, examples/web_app_calculator/workspace/src/calculator.py
  [2] ○ extract_function   → src/nexu/utils/_detect_minimal_trait.py
      WHY: 2 occurrences of 17-line block across 1 files — saves 17 lines
      FILES: src/nexu/cinema_goal_contracts.py
  [3] ○ extract_function   → examples/web_app_calculator/cinema/utils/delete_imported.py
      WHY: 2 occurrences of 10-line block across 1 files — saves 10 lines
      FILES: examples/web_app_calculator/cinema/nexu_hooks.py
  [4] ○ extract_function   → examples/web_app_calculator/cinema/utils/imported_markpact.py
      WHY: 4 occurrences of 3-line block across 1 files — saves 9 lines
      FILES: examples/web_app_calculator/cinema/nexu_hooks.py
  [5] ○ extract_function   → examples/web_app_calculator/cinema/utils/import_project_from_zip.py
      WHY: 2 occurrences of 8-line block across 1 files — saves 8 lines
      FILES: examples/web_app_calculator/cinema/nexu_hooks.py
  [6] ○ extract_function   → src/nexu/utils/option_previews_are_distinct.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: src/nexu/cinema_policy.py
  [7] ○ extract_function   → examples/web_app_calculator/cinema/utils/projects_catalog.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: examples/web_app_calculator/cinema/nexu_hooks.py
  [8] ○ extract_function   → src/nexu/utils/_looks_like_html_document.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: src/nexu/cinema_html_validate.py, src/nexu/cinema_llm.py

QUICK_WINS[4] (low risk, high savings — do first):
  [2] extract_function   saved=17L  → src/nexu/utils/_detect_minimal_trait.py
      FILES: cinema_goal_contracts.py
  [3] extract_function   saved=10L  → examples/web_app_calculator/cinema/utils/delete_imported.py
      FILES: nexu_hooks.py
  [4] extract_function   saved=9L  → examples/web_app_calculator/cinema/utils/imported_markpact.py
      FILES: nexu_hooks.py
  [5] extract_function   saved=8L  → examples/web_app_calculator/cinema/utils/import_project_from_zip.py
      FILES: nexu_hooks.py

EFFORT_ESTIMATE (total ≈ 5.5h):
  hard   render_calculator                   saved=74L  ~222min
  medium _detect_minimal_trait               saved=17L  ~34min
  easy   delete_imported                     saved=10L  ~20min
  easy   imported_markpact                   saved=9L  ~18min
  easy   import_project_from_zip             saved=8L  ~16min
  easy   option_previews_are_distinct        saved=4L  ~8min
  easy   projects_catalog                    saved=3L  ~6min
  easy   _looks_like_html_document           saved=3L  ~6min

METRICS-TARGET:
  dup_groups:  8 → 0
  saved_lines: 128 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 525 func | 55f | 2026-06-02
# generated in 0.00s

NEXT[4] (ranked by impact):
  [1] !! SPLIT           src/nexu/cinema_project_imports.py
      WHY: 1683L, 0 classes, max CC=12
      EFFORT: ~4h  IMPACT: 20196

  [2] !! SPLIT           src/nexu/cinema_policy.py
      WHY: 914L, 0 classes, max CC=14
      EFFORT: ~4h  IMPACT: 12796

  [3] !! SPLIT           src/nexu/cinema_offline_options.py
      WHY: 901L, 0 classes, max CC=13
      EFFORT: ~4h  IMPACT: 11713

  [4] !  SPLIT-FUNC      start_published_service  CC=15  fan=18
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 270


RISKS[3]:
  ⚠ Splitting src/nexu/cinema_project_imports.py may break 80 import paths
  ⚠ Splitting src/nexu/cinema_policy.py may break 44 import paths
  ⚠ Splitting src/nexu/cinema_offline_options.py may break 32 import paths

METRICS-TARGET:
  CC̄:          4.4 → ≤3.1
  max-CC:      15 → ≤7
  god-modules: 8 → 0
  high-CC(≥15): 2 → ≤1
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=4.5 → now CC̄=4.4
```

## Intent

Visual Intent Contract Orchestrator: freeze project slices, evolve capsules, verify intent contracts.
