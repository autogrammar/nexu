# System Architecture Analysis
<!-- generated in 0.00s -->

## Overview

- **Project**: /home/tom/github/semcod/nexu
- **Primary Language**: python
- **Languages**: python: 77, yaml: 9, json: 3, txt: 2, shell: 2
- **Analysis Mode**: static
- **Total Functions**: 598
- **Total Classes**: 17
- **Modules**: 100
- **Entry Points**: 151

## Architecture by Module

### src.nexu.cinema_project_imports
- **Functions**: 80
- **File**: `cinema_project_imports.py`

### src.nexu.cinema_policy
- **Functions**: 44
- **File**: `cinema_policy.py`

### src.nexu.cinema_offline_options
- **Functions**: 32
- **File**: `cinema_offline_options.py`

### src.nexu.cinema_http_preprocess
- **Functions**: 32
- **Classes**: 1
- **File**: `cinema_http_preprocess.py`

### examples.web_app_calculator.cinema.nexu_hooks
- **Functions**: 31
- **File**: `nexu_hooks.py`

### src.nexu.cinema_publish
- **Functions**: 30
- **File**: `cinema_publish.py`

### src.nexu.cinema_projects
- **Functions**: 25
- **Classes**: 1
- **File**: `cinema_projects.py`

### src.nexu.cli
- **Functions**: 23
- **File**: `cli.py`

### sdk.js.repatch-sdk
- **Functions**: 23
- **Classes**: 1
- **File**: `repatch-sdk.js`

### src.nexu.cinema_llm
- **Functions**: 18
- **File**: `cinema_llm.py`

### src.nexu.cinema_goal_contracts
- **Functions**: 15
- **File**: `cinema_goal_contracts.py`

### examples.mcp_patch_demo.server
- **Functions**: 14
- **File**: `server.js`

### src.nexu.verify
- **Functions**: 14
- **File**: `verify.py`

### src.nexu.cinema_history
- **Functions**: 13
- **File**: `cinema_history.py`

### src.nexu.cinema_html_validate
- **Functions**: 13
- **File**: `cinema_html_validate.py`

### src.nexu.mcp_server
- **Functions**: 13
- **File**: `mcp_server.py`

### src.vico.models
- **Functions**: 10
- **Classes**: 9
- **File**: `models.py`

### src.nexu.cinema
- **Functions**: 9
- **File**: `cinema.py`

### src.nexu.cinema_server
- **Functions**: 8
- **File**: `cinema_server.py`

### src.nexu.cinema_options_cache
- **Functions**: 8
- **File**: `cinema_options_cache.py`

## Key Entry Points

Main execution flows into the system:

### examples.web_app_pactown_ecosystem.run.main
- **Calls**: scripts.ci-cinema-smoke.print, scripts.ci-cinema-smoke.print, scripts.ci-cinema-smoke.print, scripts.ci-cinema-smoke.print, subprocess.Popen, scripts.ci-cinema-smoke.print, range, scripts.ci-cinema-smoke.print

### examples.web_app_event_monitor.run.main
- **Calls**: scripts.ci-cinema-smoke.print, scripts.ci-cinema-smoke.print, scripts.ci-cinema-smoke.print, scripts.ci-cinema-smoke.print, subprocess.Popen, scripts.ci-cinema-smoke.print, range, scripts.ci-cinema-smoke.print

### examples.web_app_dashboard.run.main
- **Calls**: work.exists, work.mkdir, src_dir.mkdir, shutil.copy, fixtures_dir.mkdir, shutil.copy, scripts.ci-cinema-smoke.print, src.nexu.init_project.init_project

### src.nexu.verify.verify_capsule
- **Calls**: src.nexu.capsule.load_capsule, src.nexu.paths.capsule_dir, src.nexu.verify._scan_capsule_contracts, findings.extend, src.nexu.files.collect_files, findings.extend, findings.extend, findings.extend

### deploy.docker.cinema_serve.main
- **Calls**: None.resolve, int, os.environ.get, os.environ.setdefault, src.nexu.config.load_env_files, src.nexu.config.load_config, src.nexu.cinema_policy.cinema_dir_for, cinema_dir.mkdir

### examples.scientific_calculator_demo.main
- **Calls**: work.exists, work.mkdir, None.mkdir, None.write_text, scripts.ci-cinema-smoke.print, src.nexu.init_project.init_project, src.vico.freeze.freeze_project, src.nexu.capsule.create_capsule

### examples.web_app_calculator.run.main
- **Calls**: work.exists, work.mkdir, src_dir.mkdir, shutil.copy, fixtures_dir.mkdir, shutil.copy, src.nexu.init_project.init_project, src.vico.freeze.freeze_project

### examples.nexu_markpact_exporter.main
- **Calls**: scripts.ci-cinema-smoke.print, src_file.read_text, scripts.ci-cinema-smoke.print, scripts.ci-cinema-smoke.print, output_dir.mkdir, readme_path.write_text, scripts.ci-cinema-smoke.print, scripts.ci-cinema-smoke.print

### examples.web_app_calculator.cinema.nexu_hooks.append_goal_policy_entry
- **Calls**: None.strip, None.strip, src.nexu.cinema_policy.append_goal_ledger_entry, None.resolve, src.nexu.cinema_projects.load_active_project, None.strip, None.strip, str

### src.nexu.cli.capsule_diff
> Compare capsule src files against the frozen baseline lock.
- **Calls**: capsule_app.command, src.nexu.paths.project_root, src.vico.diff.diff_capsule, Table, table.add_row, table.add_row, table.add_row, table.add_row

### src.nexu.cinema_traces.write_llm_trace
- **Calls**: trace_dir.mkdir, None.isoformat, src.nexu.cinema_traces.redact_secrets, src.nexu.cinema_traces.redact_secrets, src.nexu.cinema_traces.redact_secrets, src.nexu.cinema_traces.text_metrics, src.nexu.cinema_traces.text_metrics, path.write_text

### examples.scientific_calculator_demo2.main
- **Calls**: work.exists, work.mkdir, None.mkdir, original_file.write_text, examples.scientific_calculator_demo2.print_code, src.nexu.init_project.init_project, src.vico.freeze.freeze_project, src.nexu.capsule.create_capsule

### src.nexu.cli.capsule_status_command
> Show capsule status, latest iteration, diff counters and verification summary.
- **Calls**: capsule_app.command, src.nexu.paths.project_root, src.vico.status.capsule_status, console.print, console.print, console.print, Table, files.items

### src.nexu.cli.capsule_journal
> Show capsule event journal.
- **Calls**: capsule_app.command, src.nexu.paths.project_root, Table, console.print, src.nexu.journal.read_journal, table.add_row, str, str

### src.nexu.fast_delivery.options.read_cached_options
> Apply cached alt_a/b/c files into a Cinema directory when available.
- **Calls**: src.nexu.cinema_options_cache.options_cache_key, src.nexu.cinema_options_cache.read_options_cache, src.nexu.cinema_html_validate.filter_valid_option_batch, list, Path, enumerate, dict, src.nexu.fast_delivery.options._compatible_with_stage

### src.vico.models.Capsule.from_dict
- **Calls**: CapsuleSelection, CapsuleRuntime, cls, data.get, data.get, data.get, data.get, data.get

### src.nexu.cli.capsule_create
> Create an isolated capsule from selected project files.
- **Calls**: capsule_app.command, src.nexu.paths.project_root, src.nexu.capsule.create_capsule, src.nexu.blueprint.build_blueprint, console.print, console.print, console.print, typer.Argument

### src.nexu.cinema_offline_options.write_goal_options_offline
> Write alt_a/b/c.html without LLM. Returns human labels for options written.
- **Calls**: Path, list, list, list, None.strip, src.nexu.cinema_goal_contracts.goal_traits_from_contract_lines, src.nexu.cinema_offline_options._detect_project_types, None.lower

### src.nexu.cinema_scope.load_cinema_ui_profile
> Resolve active project kind/title and UI type for Cinema server + offline paths.
- **Calls**: None.lower, None.strip, stage0.is_file, isinstance, Path, ui_type_for_kind, src.nexu.cinema_http_preprocess.load_http_preprocess_artifacts, str

### examples.web_app_calculator.cinema.nexu_hooks.append_policy_entry
- **Calls**: None.strip, None.lower, src.nexu.cinema_policy.append_iteration_ledger_entry, None.resolve, src.nexu.cinema_projects.load_active_project, str, None.strip, None.strip

### examples.web_app_calculator.cinema.nexu_hooks.patch_option_previews
> Apply DELETE policy to alt_a/b/c without copying workspace.
- **Calls**: src.nexu.cinema_policy.load_effective_ui_constraints, src.nexu.cinema_policy.enforce_deletes_on_option_previews, None.resolve, src.nexu.cinema_policy.promote_applies_spatial_deletes, src.nexu.cinema_policy.merge_ui_constraint_lists, list, Path, list

### src.nexu.cli.capsule_iterate
> Create planned S1..Sn iteration folders and prompts.
- **Calls**: capsule_app.command, src.nexu.paths.project_root, src.nexu.iterate.iterate_capsule, src.nexu.journal.append_journal, console.print, src.nexu.cinema.generate_cinema_player, console.print, typer.Argument

### src.nexu.cli.capsule_orchestrate
> Build an offline or LLM-assisted orchestration plan for capsule evolution.
- **Calls**: capsule_app.command, src.nexu.paths.project_root, src.nexu.orchestrate.build_capsule_orchestration, console.print, console.print, console.print, typer.Argument, typer.Option

### src.nexu.cli.capsule_promote
> Build a promotion plan for copying capsule changes back to the source project.
- **Calls**: capsule_app.command, src.nexu.paths.project_root, src.nexu.promote.build_promotion_plan, console.print, console.print, src.nexu.promote.apply_promotion_plan, console.print, typer.Argument

### src.nexu.cinema_llm.parse_batch_alt_options
> Parse NEXU_ALT_A/B/C marked batch LLM output into option filenames.
- **Calls**: src.nexu.cinema_llm._strip_rich_console_artifacts, _BATCH_ALT_FILES.items, re.search, src.nexu.cinema_html_validate.prepare_cinema_html_document, set, set, re.search, src.nexu.cinema_llm.normalize_html_document

### src.nexu.cli.capsule_review
> Build an evidence-based review packet for human or optional LLM review.
- **Calls**: capsule_app.command, src.nexu.paths.project_root, src.nexu.review.build_review_packet, console.print, console.print, console.print, typer.Argument, typer.Option

### sdk.js.repatch-sdk.RepatchSDK.removeMatch
- **Calls**: sdk.js.repatch-sdk.querySelector, sdk.js.repatch-sdk.insertAdjacentHTML, sdk.js.repatch-sdk.log, sdk.js.repatch-sdk.Error, sdk.js.repatch-sdk.trim, sdk.js.repatch-sdk.replace, sdk.js.repatch-sdk.getElementById, sdk.js.repatch-sdk.createElement

### src.nexu.cli.capsule_plan
> Create a deterministic S1..Sn capsule iteration plan.
- **Calls**: capsule_app.command, src.nexu.paths.project_root, src.nexu.plan.build_iteration_plan, console.print, console.print, src.nexu.cli._print_yaml, typer.Argument, typer.Option

### src.nexu.fast_delivery.context.compact_markpact_for_llm
> Keep only high-value Markpact sections for fast LLM requests.
- **Calls**: str, None.lower, re.sub, None.rstrip, None.strip, re.search, None.join, len

### src.nexu.cinema_project_imports.promote_cinema_option
> Promote an option file onto stage{N}; repair HTTP imports before reading alts.
- **Calls**: Path, str, src.nexu.cinema_project_imports._load_http_import_meta, stage_path.write_text, alt_path.is_file, src.nexu.cinema_projects.load_active_project, src.nexu.cinema_project_imports.restore_http_import_stages_if_needed, dict

## Process Flows

Key execution flows identified:

### Flow 1: main
```
main [examples.web_app_pactown_ecosystem.run]
  └─ →> print
  └─ →> print
```

### Flow 2: verify_capsule
```
verify_capsule [src.nexu.verify]
  └─> _scan_capsule_contracts
      └─ →> collect_files
          └─> rel
          └─> matches_any
  └─ →> load_capsule
      └─ →> read_yaml
      └─ →> capsule_dir
          └─> capsules_dir
  └─ →> capsule_dir
      └─> capsules_dir
          └─> nexu_dir
```

### Flow 3: append_goal_policy_entry
```
append_goal_policy_entry [examples.web_app_calculator.cinema.nexu_hooks]
  └─ →> append_goal_ledger_entry
      └─> normalize_proposals_for_ledger
          └─> _proposal_kind_and_element
      └─> append_policy_ledger_entry
  └─ →> load_active_project
```

### Flow 4: capsule_diff
```
capsule_diff [src.nexu.cli]
  └─ →> project_root
  └─ →> diff_capsule
      └─ →> load_capsule
          └─ →> read_yaml
          └─ →> capsule_dir
```

### Flow 5: write_llm_trace
```
write_llm_trace [src.nexu.cinema_traces]
  └─> redact_secrets
  └─> redact_secrets
```

### Flow 6: capsule_status_command
```
capsule_status_command [src.nexu.cli]
  └─ →> project_root
  └─ →> capsule_status
      └─ →> load_capsule
          └─ →> read_yaml
          └─ →> capsule_dir
```

### Flow 7: capsule_journal
```
capsule_journal [src.nexu.cli]
  └─ →> project_root
  └─ →> read_journal
      └─> journal_path
          └─ →> capsule_dir
      └─ →> read_yaml
```

### Flow 8: read_cached_options
```
read_cached_options [src.nexu.fast_delivery.options]
  └─ →> options_cache_key
      └─> _digest
      └─> _digest
  └─ →> read_options_cache
  └─ →> filter_valid_option_batch
      └─> prepare_cinema_html_document
          └─> repair_html_structure
          └─> validate_cinema_html_document
```

### Flow 9: from_dict
```
from_dict [src.vico.models.Capsule]
```

### Flow 10: capsule_create
```
capsule_create [src.nexu.cli]
  └─ →> project_root
  └─ →> create_capsule
      └─ →> ensure_project_dirs
          └─> nexu_dir
          └─> snapshots_dir
  └─ →> build_blueprint
      └─ →> load_capsule
          └─ →> read_yaml
          └─ →> capsule_dir
```

## Key Classes

### sdk.js.repatch-sdk.RepatchSDK
- **Methods**: 23
- **Key Methods**: sdk.js.repatch-sdk.RepatchSDK.connect, sdk.js.repatch-sdk.RepatchSDK._connectWS, sdk.js.repatch-sdk.RepatchSDK.payload, sdk.js.repatch-sdk.RepatchSDK.setTimeout, sdk.js.repatch-sdk.RepatchSDK._connectSSE, sdk.js.repatch-sdk.RepatchSDK.payload, sdk.js.repatch-sdk.RepatchSDK.onPatch, sdk.js.repatch-sdk.RepatchSDK.apply, sdk.js.repatch-sdk.RepatchSDK.dslClean, sdk.js.repatch-sdk.RepatchSDK.addMatch

### src.nexu.cinema_http_preprocess._OutlineParser
- **Methods**: 5
- **Key Methods**: src.nexu.cinema_http_preprocess._OutlineParser.__init__, src.nexu.cinema_http_preprocess._OutlineParser._keep_attr, src.nexu.cinema_http_preprocess._OutlineParser.handle_starttag, src.nexu.cinema_http_preprocess._OutlineParser.handle_endtag, src.nexu.cinema_http_preprocess._OutlineParser.handle_data
- **Inherits**: HTMLParser

### src.vico.models.FrozenSnapshot
- **Methods**: 2
- **Key Methods**: src.vico.models.FrozenSnapshot.to_dict, src.vico.models.FrozenSnapshot.from_dict

### src.vico.models.Capsule
- **Methods**: 2
- **Key Methods**: src.vico.models.Capsule.to_dict, src.vico.models.Capsule.from_dict

### src.nexu.cinema_projects.ExampleProject
- **Methods**: 1
- **Key Methods**: src.nexu.cinema_projects.ExampleProject.to_public_dict

### src.vico.models.VerificationReport
- **Methods**: 1
- **Key Methods**: src.vico.models.VerificationReport.to_dict

### src.vico.models.CapsuleDiff
- **Methods**: 1
- **Key Methods**: src.vico.models.CapsuleDiff.to_dict

### src.vico.models.PromptExport
- **Methods**: 1
- **Key Methods**: src.vico.models.PromptExport.to_dict

### src.nexu.config.LLMConfig
- **Methods**: 0

### src.nexu.config.ReviewConfig
- **Methods**: 0

### src.nexu.config.CinemaConfig
> Cinema live iteration tuning (also overridable via CINEMA_* env vars).
- **Methods**: 0

### src.nexu.config.nexuConfig
- **Methods**: 0

### src.vico.models.FrozenFile
- **Methods**: 0

### src.vico.models.CapsuleSelection
- **Methods**: 0

### src.vico.models.CapsuleRuntime
- **Methods**: 0

### src.vico.models.VerificationFinding
- **Methods**: 0

### src.nexu.fast_delivery.router.DeliveryRoute
> Selected route for one improvement-loop step.
- **Methods**: 0

## Data Transformation Functions

Key functions that process and transform data:

### examples.mcp_patch_demo.server.serialized
- **Output to**: examples.mcp_patch_demo.server.forEach, examples.mcp_patch_demo.server.send

### examples.web_app_calculator.cinema.nexu_hooks.validate_artifact
- **Output to**: src.nexu.cinema_policy.validate_intract_artifact

### src.nexu.cinema_llm.parse_batch_alt_options
> Parse NEXU_ALT_A/B/C marked batch LLM output into option filenames.
- **Output to**: src.nexu.cinema_llm._strip_rich_console_artifacts, _BATCH_ALT_FILES.items, re.search, src.nexu.cinema_html_validate.prepare_cinema_html_document, set

### src.nexu.cinema_projects._apply_preprocess_meta
- **Output to**: None.isoformat, src.nexu.cinema_http_preprocess.preprocess_cinema_seed, str, meta.update, datetime.now

### src.nexu.cinema_policy._process_ledger_entry
> Process a single ledger entry and update the state.
- **Output to**: src.nexu.cinema_policy._process_keep_delete_entries, src.nexu.cinema_policy._process_proposed_contracts, entry.get, src.nexu.cinema_policy._ledger_entry_matches_project, src.nexu.cinema_policy._ledger_entry_matches_scope

### src.nexu.cinema_policy._process_keep_delete_entries
> Process keep and delete entries from a ledger entry.
- **Output to**: entry.get, None.strip, entry.get, None.strip, str

### src.nexu.cinema_policy._process_proposed_contracts
> Process proposed contracts from a ledger entry.
- **Output to**: entry.get, src.nexu.cinema_policy._proposal_kind_and_element, isinstance

### src.nexu.cinema_policy.validate_intract_artifact
- **Output to**: validate_artifact_with_proposals, src.nexu.cinema_policy.ensure_intract_on_path, src.nexu.cinema_policy.ensure_intract_on_path, Path, str

### src.nexu.cinema_options_cache.invalidate_options_cache
- **Output to**: cache_root.is_dir, shutil.rmtree

### src.nexu.cinema_publish._validate_service_id
- **Output to**: None.strip, _SERVICE_ID_RE.fullmatch

### src.nexu.cinema_llm_contracts._format_contract_params
- **Output to**: src.nexu.cinema_llm_contracts._compact, src.nexu.cinema_llm_contracts._compact, src.nexu.cinema_llm_contracts._compact, None.join, None.join

### src.nexu.cinema_html_validate.validate_css_safety
> Reject CSS patterns that commonly break Cinema previews.
- **Output to**: _repatch_validate_css_safety

### src.nexu.cinema_html_validate._validate_basic_tags
- **Output to**: text.lower, src.nexu.cinema_html_validate._looks_like_html_document, errors.append, errors.append, src.nexu.cinema_html_validate._has_open_tag

### src.nexu.cinema_html_validate._validate_calculator_elements
- **Output to**: re.search, errors.append, re.search, errors.append

### src.nexu.cinema_html_validate.validate_cinema_html_document
> Return whether HTML has the minimum structure expected in Cinema previews.
- **Output to**: None.strip, src.nexu.cinema_html_validate._validate_basic_tags, text.lower, lower.find, re.search

### src.nexu.cinema_http_preprocess._write_preprocess_artifacts
- **Output to**: list, src.nexu.cinema_http_preprocess.extract_visual_css, src.nexu.cinema_http_preprocess.build_html_outline, css_path.write_text, outline_path.write_text

### src.nexu.cinema_http_preprocess.preprocess_cinema_seed
> Write nexu-visual.css and nexu-outline.html beside stage0.html; return active_project fields.
- **Output to**: src.nexu.cinema_http_preprocess._write_preprocess_artifacts, stage0.is_file, stage0.read_text

### src.nexu.cinema_http_preprocess.http_preprocess_artifacts_present
> True when compact LLM patch artifacts exist under source_dir.
- **Output to**: str, str, None.is_file, None.is_file, isinstance

### src.nexu.cinema_http_preprocess.ensure_http_preprocess_artifacts
> Regenerate nexu-visual.css + nexu-outline.html when missing (HTTP re-activate migration).
- **Output to**: src.nexu.cinema_http_preprocess.http_preprocess_artifacts_present, src.nexu.cinema_http_preprocess.preprocess_http_import, source_dir.is_dir

### src.nexu.cinema_http_preprocess.preprocess_http_import
> Write nexu-visual.css and nexu-outline.html under source_dir; return project.json fields.
- **Output to**: meta.get, isinstance, index_path.is_file, index_path.is_file, index_path.read_text

### src.nexu.cinema_http_preprocess.load_cinema_seed_preprocess_artifacts
> Load compact seed preprocess artifacts from cinema dir when active_project uses patch mode.
- **Output to**: Path, str, str, isinstance, str

### src.nexu.cinema_http_preprocess.load_http_preprocess_artifacts
> Load compact HTTP import artifacts for LLM prompts when the active project is http-*.
- **Output to**: str, src.nexu.cinema_http_preprocess._project_meta_path, src.nexu.cinema_http_preprocess._load_project_meta, src.nexu.cinema_http_preprocess._read_http_source_artifacts, src.nexu.cinema_http_preprocess._load_organize_patch_context

### src.nexu.cinema_project_imports._validate_http_url
- **Output to**: urlparse, url.strip

### src.nexu.cinema_project_imports._validate_git_url
- **Output to**: url.strip, source.lower, lowered.startswith, lowered.startswith, re.match

### src.nexu.cinema_project_imports._decode_http_bytes
- **Output to**: src.nexu.cinema_project_imports._charset_from_content_type, body.decode, body.decode

## Behavioral Patterns

### state_machine_RepatchSDK
- **Type**: state_machine
- **Confidence**: 0.70
- **Functions**: sdk.js.repatch-sdk.RepatchSDK.connect, sdk.js.repatch-sdk.RepatchSDK._connectWS, sdk.js.repatch-sdk.RepatchSDK.payload, sdk.js.repatch-sdk.RepatchSDK.setTimeout, sdk.js.repatch-sdk.RepatchSDK._connectSSE

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `src.nexu.config.load_config` - 76 calls
- `examples.web_app_pactown_ecosystem.run.main` - 39 calls
- `examples.web_app_event_monitor.run.main` - 37 calls
- `examples.web_app_dashboard.run.main` - 35 calls
- `src.nexu.cinema.build_intract_policy_snapshot` - 32 calls
- `src.nexu.report.build_capsule_report` - 32 calls
- `src.nexu.orchestrate.build_capsule_orchestration` - 28 calls
- `examples.run_examples.run_example` - 26 calls
- `src.nexu.verify.verify_capsule` - 26 calls
- `src.nexu.cinema_baseline_contracts.ensure_capsule_intract_yaml` - 25 calls
- `deploy.docker.cinema_serve.main` - 25 calls
- `src.nexu.review.build_review_packet` - 24 calls
- `src.nexu.cinema_offline_options.build_chemical_option_html` - 24 calls
- `src.nexu.capsule.create_capsule` - 24 calls
- `examples.scientific_calculator_demo.main` - 23 calls
- `examples.web_app_calculator.run.main` - 23 calls
- `examples.nexu_markpact_exporter.main` - 22 calls
- `src.nexu.orchestrate.offline_orchestration_from_context` - 22 calls
- `src.nexu.cinema_markpact.build_markpact_readme` - 21 calls
- `src.nexu.cinema_publish.start_published_service` - 21 calls
- `scripts.check-doc-links.check_links` - 21 calls
- `src.nexu.cinema_project_imports.import_http_project` - 21 calls
- `src.nexu.cinema_html_validate.relocate_style_tags_to_head` - 20 calls
- `src.nexu.cinema_html_validate.repair_html_structure` - 20 calls
- `examples.web_app_calculator.cinema.nexu_hooks.append_goal_policy_entry` - 19 calls
- `src.nexu.cli.capsule_diff` - 19 calls
- `src.nexu.cinema_history.save_history_checkpoint` - 19 calls
- `src.nexu.cinema_http_preprocess.extract_visual_css` - 19 calls
- `src.nexu.cinema.generate_cinema_player` - 18 calls
- `src.nexu.cinema_traces.write_llm_trace` - 18 calls
- `src.nexu.cinema_history.restore_history_checkpoint` - 18 calls
- `src.nexu.export_prompt.export_iteration_prompt` - 18 calls
- `src.nexu.cinema_http_preprocess.load_cinema_seed_preprocess_artifacts` - 18 calls
- `src.nexu.cinema_project_imports.import_markpact_project` - 18 calls
- `examples.scientific_calculator_demo2.main` - 17 calls
- `src.nexu.cli.capsule_status_command` - 17 calls
- `src.nexu.cli.capsule_journal` - 17 calls
- `src.nexu.cinema_projects.delete_example_project` - 17 calls
- `src.nexu.cinema_goal_contracts.propose_goal_extension_contracts` - 17 calls
- `src.nexu.cinema_publish.publish_project_service` - 17 calls

## System Interactions

How components interact:

```mermaid
graph TD
    main --> print
    main --> Popen
    main --> exists
    main --> mkdir
    main --> copy
    verify_capsule --> load_capsule
    verify_capsule --> capsule_dir
    verify_capsule --> _scan_capsule_contra
    verify_capsule --> extend
    verify_capsule --> collect_files
    main --> resolve
    main --> int
    main --> get
    main --> setdefault
    main --> load_env_files
    main --> write_text
    main --> read_text
    append_goal_policy_e --> strip
    append_goal_policy_e --> append_goal_ledger_e
    append_goal_policy_e --> resolve
    append_goal_policy_e --> load_active_project
    capsule_diff --> command
    capsule_diff --> project_root
    capsule_diff --> diff_capsule
    capsule_diff --> Table
    capsule_diff --> add_row
    write_llm_trace --> mkdir
    write_llm_trace --> isoformat
    write_llm_trace --> redact_secrets
    main --> print_code
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.