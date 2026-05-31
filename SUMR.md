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
- **version**: `0.5.17`
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
      run: ruff check src/nexu/cinema.py src/nexu/cinema_server.py src/nexu/cinema_baseline_contracts.py src/nexu/cinema_markpact.py src/nexu/cinema_publish.py src/nexu/cinema_offline_options.py src/nexu/intract.py src/nexu/verify.py src/nexu/intract_adapter.py tests/test_cinema_server.py tests/test_cinema_baseline_contracts.py tests/test_cinema_markpact.py tests/test_cinema_publish.py tests/test_cinema_offline_options.py

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

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

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

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 77f 8565L | python:59,yaml:8,shell:3,json:2,yml:1,txt:1,toml:1 | 2026-05-31
# generated in 0.01s
# CC̅=3.8 | critical:4/288 | dups:0 | cycles:0

HEALTH[4]:
  🟡 CC    activate_example_project CC=16 (limit:15)
  🟡 CC    build_markpact_readme CC=18 (limit:15)
  🟡 CC    start_published_service CC=17 (limit:15)
  🟡 CC    write_goal_options_offline CC=16 (limit:15)

REFACTOR[1]:
  1. split 4 high-CC methods  (CC>15)

PIPELINES[63]:
  [1] Src [main]: main
      PURITY: 100% pure
  [2] Src [main]: main → init_project → ensure_project_dirs → nexu_dir
      PURITY: 100% pure
  [3] Src [simulate_realtime_sync]: simulate_realtime_sync
      PURITY: 100% pure
  [4] Src [main]: main → run_example → init_project → ensure_project_dirs → ...(1 more)
      PURITY: 100% pure
  [5] Src [main]: main → print_code
      PURITY: 100% pure
  [6] Src [main]: main
      PURITY: 100% pure
  [7] Src [main]: main → init_project → ensure_project_dirs → nexu_dir
      PURITY: 100% pure
  [8] Src [list_users]: list_users
      PURITY: 100% pure
  [9] Src [preview_menu_icons]: preview_menu_icons
      PURITY: 100% pure
  [10] Src [main]: main → init_project → ensure_project_dirs → nexu_dir
      PURITY: 100% pure
  [11] Src [render_dashboard]: render_dashboard
      PURITY: 100% pure
  [12] Src [render_dashboard]: render_dashboard
      PURITY: 100% pure
  [13] Src [main]: main
      PURITY: 100% pure
  [14] Src [init]: init → project_root
      PURITY: 100% pure
  [15] Src [freeze]: freeze → project_root
      PURITY: 100% pure
  [16] Src [capsule_create]: capsule_create → project_root
      PURITY: 100% pure
  [17] Src [capsule_list]: capsule_list → project_root
      PURITY: 100% pure
  [18] Src [capsule_status_command]: capsule_status_command → project_root
      PURITY: 100% pure
  [19] Src [capsule_iterate]: capsule_iterate → project_root
      PURITY: 100% pure
  [20] Src [capsule_blueprint]: capsule_blueprint → project_root
      PURITY: 100% pure
  [21] Src [capsule_export_prompt]: capsule_export_prompt → project_root
      PURITY: 100% pure
  [22] Src [capsule_diff]: capsule_diff → project_root
      PURITY: 100% pure
  [23] Src [capsule_drift]: capsule_drift → project_root
      PURITY: 100% pure
  [24] Src [capsule_verify]: capsule_verify → project_root
      PURITY: 100% pure
  [25] Src [capsule_plan]: capsule_plan → project_root
      PURITY: 100% pure
  [26] Src [capsule_runtime]: capsule_runtime → project_root
      PURITY: 100% pure
  [27] Src [capsule_report]: capsule_report → project_root
      PURITY: 100% pure
  [28] Src [capsule_journal]: capsule_journal → project_root
      PURITY: 100% pure
  [29] Src [capsule_orchestrate]: capsule_orchestrate → project_root
      PURITY: 100% pure
  [30] Src [capsule_review]: capsule_review → project_root
      PURITY: 100% pure
  [31] Src [capsule_bundle]: capsule_bundle → project_root
      PURITY: 100% pure
  [32] Src [capsule_promote]: capsule_promote → project_root
      PURITY: 100% pure
  [33] Src [mcp_tools]: mcp_tools
      PURITY: 100% pure
  [34] Src [mcp_serve]: mcp_serve → project_root
      PURITY: 100% pure
  [35] Src [to_public_dict]: to_public_dict
      PURITY: 100% pure
  [36] Src [list_project_catalog]: list_project_catalog
      PURITY: 100% pure
  [37] Src [activate_example_project]: activate_example_project → _resolve_source_cinema
      PURITY: 100% pure
  [38] Src [load_active_project]: load_active_project
      PURITY: 100% pure
  [39] Src [list_history_checkpoints]: list_history_checkpoints → _load_index → history_index_path → history_dir
      PURITY: 100% pure
  [40] Src [restore_history_checkpoint]: restore_history_checkpoint → project_root
      PURITY: 100% pure
  [41] Src [ledger_archive_for_display]: ledger_archive_for_display → _ledger_snapshot
      PURITY: 100% pure
  [42] Src [sha256_text]: sha256_text
      PURITY: 100% pure
  [43] Src [to_dict]: to_dict
      PURITY: 100% pure
  [44] Src [from_dict]: from_dict → utc_now
      PURITY: 100% pure
  [45] Src [to_dict]: to_dict
      PURITY: 100% pure
  [46] Src [from_dict]: from_dict → utc_now
      PURITY: 100% pure
  [47] Src [to_dict]: to_dict
      PURITY: 100% pure
  [48] Src [to_dict]: to_dict
      PURITY: 100% pure
  [49] Src [to_dict]: to_dict
      PURITY: 100% pure
  [50] Src [_apply_promotion_from_mcp]: _apply_promotion_from_mcp → build_promotion_plan → load_capsule → read_yaml
      PURITY: 100% pure

LAYERS:
  src/                            CC̄=3.9    ←in:0  →out:0
  │ !! cinema_policy              655L  0C   33m  CC=13     ←3
  │ !! cinema_scripts             622L  0C    5m  CC=6      ←4
  │ !! cinema_offline_options     520L  0C   19m  CC=16     ←1
  │ !! cinema_publish             459L  0C   21m  CC=17     ←0
  │ mcp_server                 393L  0C   13m  CC=6      ←1
  │ cli                        379L  0C   23m  CC=4      ←0
  │ !! cinema_projects            359L  1C    9m  CC=16     ←0
  │ verify                     317L  0C   14m  CC=12     ←7
  │ cinema_history             244L  0C   13m  CC=8      ←1
  │ orchestrate                232L  0C    6m  CC=13     ←2
  │ cinema                     199L  0C    9m  CC=11     ←3
  │ cinema_baseline_contracts   184L  0C    6m  CC=9      ←1
  │ llm                        165L  0C    5m  CC=8      ←2
  │ export_prompt              160L  0C    3m  CC=12     ←4
  │ review                     157L  0C    2m  CC=5      ←2
  │ intract_adapter            133L  0C    6m  CC=9      ←1
  │ runtime                    131L  0C    4m  CC=9      ←4
  │ capsule                    124L  0C    5m  CC=8      ←18
  │ config                     121L  3C    5m  CC=10     ←4
  │ !! cinema_markpact            120L  0C    3m  CC=18     ←1
  │ cinema_server              119L  0C    8m  CC=4      ←1
  │ report                      94L  0C    3m  CC=2      ←2
  │ promote                     92L  0C    3m  CC=6      ←3
  │ init_project                86L  0C    1m  CC=3      ←6
  │ plan                        81L  0C    2m  CC=9      ←4
  │ blueprint                   73L  0C    1m  CC=7      ←7
  │ bundle                      55L  0C    2m  CC=5      ←2
  │ files                       51L  0C    4m  CC=8      ←7
  │ iterate                     44L  0C    1m  CC=7      ←5
  │ journal                     43L  0C    3m  CC=5      ←8
  │ paths                       35L  0C    6m  CC=2      ←23
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ intract                      0L  1C    6m  CC=12     ←7
  │ freeze                       0L  0C    1m  CC=2      ←6
  │ status                       0L  0C    1m  CC=3      ←3
  │ drift                        0L  0C    1m  CC=7      ←5
  │ git                          0L  0C    1m  CC=4      ←2
  │ hashing                      0L  0C    2m  CC=2      ←4
  │ models                       0L  9C   10m  CC=3      ←20
  │ diff                         0L  0C    1m  CC=12     ←9
  │ __main__                     0L  0C    0m  CC=0.0    ←0
  │
  scripts/                        CC̄=3.5    ←in:0  →out:0
  │ check-doc-links            114L  0C    8m  CC=12     ←0
  │ ci-cinema-smoke.sh          48L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=2.8    ←in:0  →out:26  !! split
  │ run                        118L  0C    1m  CC=2      ←0
  │ run                        110L  0C    1m  CC=2      ←0
  │ run                         97L  0C    1m  CC=8      ←0
  │ nexu_markpact_exporter      95L  0C    1m  CC=3      ←0
  │ run                         90L  0C    1m  CC=13     ←0
  │ scientific_calculator_demo2    86L  0C    2m  CC=2      ←0
  │ run_examples                79L  0C    2m  CC=2      ←0
  │ docker-compose.yml          70L  0C    0m  CC=0.0    ←0
  │ realtime_lane_nexu_sync     62L  0C    1m  CC=2      ←0
  │ scientific_calculator_demo    61L  0C    1m  CC=2      ←0
  │ nexu.yaml                   42L  0C    0m  CC=0.0    ←0
  │ calculator                  38L  0C    1m  CC=1      ←0
  │ calculator                  38L  0C    1m  CC=1      ←0
  │ pactown.yaml                31L  0C    0m  CC=0.0    ←0
  │ intract.yaml                30L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  27L  0C    0m  CC=0.0    ←0
  │ menu_icons                  24L  0C    1m  CC=3      ←0
  │ dashboard                   24L  0C    1m  CC=2      ←0
  │ pactown.yaml                19L  0C    0m  CC=0.0    ←0
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
  │ pyproject.toml              85L  0C    0m  CC=0.0    ←0
  │ Makefile                    62L  0C    0m  CC=0.0    ←0
  │ project.sh                  50L  0C    0m  CC=0.0    ←0
  │ pyqual.yaml                 25L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
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
     src/vico/intract.py                       0L
     src/vico/models.py                        0L
     src/vico/status.py                        0L

COUPLING:
                                                  src.nexu                     src.vico                     examples   examples.web_app_dashboard  examples.web_app_calculator
                     src.nexu                           ──                           62                          ←21                           ←9                           ←5  hub
                     src.vico                           12                           ──                           ←5                           ←1                           ←1  hub
                     examples                           21                            5                           ──                                                            !! fan-out
   examples.web_app_dashboard                            9                            1                                                        ──                               !! fan-out
  examples.web_app_calculator                            5                            1                                                                                     ──
  CYCLES: none
  HUB: src.nexu/ (fan-in=47)
  HUB: src.vico/ (fan-in=69)
  SMELL: examples/ fan-out=26 → split needed
  SMELL: src.nexu/ fan-out=62 → split needed
  SMELL: examples.web_app_dashboard/ fan-out=10 → split needed
  SMELL: src.vico/ fan-out=12 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 3 groups | 60f 8016L | 2026-05-31

SUMMARY:
  files_scanned: 60
  total_lines:   8016
  dup_groups:    3
  dup_fragments: 7
  saved_lines:   86
  scan_ms:       2327

HOTSPOTS[6] (files with most duplication):
  examples/web_app_calculator/markpact_sandbox/sandbox/src/calculator.py  dup=37L  groups=1  frags=1  (0.5%)
  examples/web_app_calculator/src/calculator.py  dup=37L  groups=1  frags=1  (0.5%)
  examples/web_app_calculator/workspace/src/calculator.py  dup=37L  groups=1  frags=1  (0.5%)
  src/nexu/cinema.py  dup=8L  groups=1  frags=1  (0.1%)
  src/nexu/cinema_baseline_contracts.py  dup=8L  groups=1  frags=1  (0.1%)
  src/nexu/cinema_policy.py  dup=8L  groups=1  frags=2  (0.1%)

DUPLICATES[3] (ranked by impact):
  [f3aa7c7e1fe24b1d] ! EXAC  render_calculator  L=37 N=3 saved=74 sim=1.00
      examples/web_app_calculator/markpact_sandbox/sandbox/src/calculator.py:2-38  (render_calculator)
      examples/web_app_calculator/src/calculator.py:2-38  (render_calculator)
      examples/web_app_calculator/workspace/src/calculator.py:2-38  (render_calculator)
  [08f04a82252038fb]   STRU  format_intract_v1_line  L=8 N=2 saved=8 sim=1.00
      src/nexu/cinema.py:63-70  (format_intract_v1_line)
      src/nexu/cinema_baseline_contracts.py:12-19  (_line)
  [3e7f254259144cfa]   STRU  option_previews_are_distinct  L=4 N=2 saved=4 sim=1.00
      src/nexu/cinema_policy.py:144-147  (option_previews_are_distinct)
      src/nexu/cinema_policy.py:150-153  (stage_files_are_distinct)

REFACTOR[3] (ranked by priority):
  [1] ◐ extract_function   → examples/web_app_calculator/utils/render_calculator.py
      WHY: 3 occurrences of 37-line block across 3 files — saves 74 lines
      FILES: examples/web_app_calculator/markpact_sandbox/sandbox/src/calculator.py, examples/web_app_calculator/src/calculator.py, examples/web_app_calculator/workspace/src/calculator.py
  [2] ○ extract_function   → src/nexu/utils/format_intract_v1_line.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: src/nexu/cinema.py, src/nexu/cinema_baseline_contracts.py
  [3] ○ extract_function   → src/nexu/utils/option_previews_are_distinct.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: src/nexu/cinema_policy.py

QUICK_WINS[1] (low risk, high savings — do first):
  [2] extract_function   saved=8L  → src/nexu/utils/format_intract_v1_line.py
      FILES: cinema.py, cinema_baseline_contracts.py

EFFORT_ESTIMATE (total ≈ 4.1h):
  hard   render_calculator                   saved=74L  ~222min
  easy   format_intract_v1_line              saved=8L  ~16min
  easy   option_previews_are_distinct        saved=4L  ~8min

METRICS-TARGET:
  dup_groups:  3 → 0
  saved_lines: 86 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 261 func | 39f | 2026-05-31
# generated in 0.00s

NEXT[7] (ranked by impact):
  [1] !! SPLIT           src/nexu/cinema_policy.py
      WHY: 655L, 0 classes, max CC=13
      EFFORT: ~4h  IMPACT: 8515

  [2] !! SPLIT           src/nexu/cinema_offline_options.py
      WHY: 520L, 0 classes, max CC=16
      EFFORT: ~4h  IMPACT: 8320

  [3] !! SPLIT           src/nexu/cinema_scripts.py
      WHY: 622L, 0 classes, max CC=6
      EFFORT: ~4h  IMPACT: 3732

  [4] !  SPLIT-FUNC      start_published_service  CC=17  fan=22
      WHY: CC=17 exceeds 15
      EFFORT: ~1h  IMPACT: 374

  [5] !  SPLIT-FUNC      activate_example_project  CC=16  fan=21
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 336

  [6] !  SPLIT-FUNC      build_markpact_readme  CC=18  fan=17
      WHY: CC=18 exceeds 15
      EFFORT: ~1h  IMPACT: 306

  [7] !  SPLIT-FUNC      write_goal_options_offline  CC=16  fan=16
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 256


RISKS[3]:
  ⚠ Splitting src/nexu/cinema_policy.py may break 33 import paths
  ⚠ Splitting src/nexu/cinema_scripts.py may break 5 import paths
  ⚠ Splitting src/nexu/cinema_offline_options.py may break 19 import paths

METRICS-TARGET:
  CC̄:          3.9 → ≤2.7
  max-CC:      18 → ≤9
  god-modules: 4 → 0
  high-CC(≥15): 4 → ≤2
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
  prev CC̄=3.8 → now CC̄=3.9
```

## Intent

Visual Intent Contract Orchestrator: freeze project slices, evolve capsules, verify intent contracts.
