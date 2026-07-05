"""Cinema policy ledger, manifest merge, and capsule verification.

Split into focused submodules (constraints, snapshot, ledger, proposals,
html_checks, option_previews, llm_proposals, intract_validation,
workspace_verify); this package re-exports the original public and
internal (``_``-prefixed) names so existing imports keep working.
"""

from __future__ import annotations

from repatch import OPTION_PREVIEW_FILES as _REPATCH_OPTION_PREVIEW_FILES

from .constraints import (
    _build_constraint_result,
    _ledger_entry_matches_project,
    _ledger_entry_matches_scope,
    _process_keep_delete_entries,
    _process_ledger_entry,
    _process_proposed_contracts,
    effective_ui_constraints_from_ledger,
    load_effective_ui_constraints,
    merge_ui_constraint_lists,
    promote_applies_spatial_deletes,
    resolve_iteration_mode,
)
from .html_checks import (
    _html_files_distinct,
    _normalize_html_body,
    _replace_html_title,
    option_previews_are_distinct,
    stage_files_are_distinct,
)
from .intract_validation import ensure_intract_on_path, validate_intract_artifact
from .ledger import (
    _resolve_ledger_path,
    append_goal_ledger_entry,
    append_iteration_ledger_entry,
    append_policy_ledger_entry,
    load_goal_contract_lines,
)
from .llm_proposals import propose_llm_for_stage
from .option_previews import (
    enforce_deletes_on_option_previews,
    ensure_http_option_previews_from_stage0,
    ensure_option_previews_from_stages,
    sync_option_previews_from_workspace,
)
from .proposals import (
    _proposal_kind_and_element,
    normalize_proposals_for_ledger,
    propose_ui_delta_contract_dicts,
)
from .snapshot import (
    ManifestTarget,
    _intract_manifest_path,
    _VALID_TARGETS,
    apply_ledger_from_cinema,
    cinema_dir_for,
    cinema_model_label,
    load_policy_snapshot,
    manifest_paths_from_snapshot,
    normalize_manifest_target,
    policy_ledger_path,
    policy_snapshot_path,
    refresh_cinema_policy_snapshot,
    refresh_imported_policy_snapshot,
    reset_cinema_policy_ledger,
)
from .workspace_verify import verify_capsule_workspace

_OPTION_PREVIEW_FILES = _REPATCH_OPTION_PREVIEW_FILES

__all__ = [
    "ManifestTarget",
    "append_goal_ledger_entry",
    "append_iteration_ledger_entry",
    "append_policy_ledger_entry",
    "apply_ledger_from_cinema",
    "cinema_dir_for",
    "cinema_model_label",
    "effective_ui_constraints_from_ledger",
    "ensure_http_option_previews_from_stage0",
    "ensure_intract_on_path",
    "ensure_option_previews_from_stages",
    "enforce_deletes_on_option_previews",
    "load_effective_ui_constraints",
    "load_goal_contract_lines",
    "load_policy_snapshot",
    "manifest_paths_from_snapshot",
    "merge_ui_constraint_lists",
    "normalize_manifest_target",
    "normalize_proposals_for_ledger",
    "option_previews_are_distinct",
    "policy_ledger_path",
    "policy_snapshot_path",
    "promote_applies_spatial_deletes",
    "propose_llm_for_stage",
    "propose_ui_delta_contract_dicts",
    "refresh_cinema_policy_snapshot",
    "refresh_imported_policy_snapshot",
    "reset_cinema_policy_ledger",
    "resolve_iteration_mode",
    "stage_files_are_distinct",
    "sync_option_previews_from_workspace",
    "validate_intract_artifact",
    "verify_capsule_workspace",
]
