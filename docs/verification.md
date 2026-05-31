# Verification model

nexu verifies whether the capsule still follows its declared intent contracts.

## Statuses

- `pass` — no fail/warn gates.
- `partial` — no hard failure, but warnings exist.
- `fail` — at least one hard gate failed.

## Current gates

| Gate | Meaning |
|---|---|
| `contracts_found` | Capsule has Intract-style contracts. |
| `source_files_found` | Capsule contains selected source files. |
| `baseline_lock` | Capsule has file hashes from creation time. |
| `no_forbidden_write` | No write-like pattern was found when write is forbidden. |
| `secret_leak_check` | No obvious secret-like value was found when `secret_leak` is forbidden. |
| `output_presence` | Declared outputs have textual evidence in capsule files. |
| `required_intents` | Required sub-intents are present or reported as missing. |
| `iteration_count` | Iterations are tracked. |
| `intract_policy_check` | Dynamic Intract validation passed when the adapter is available. |
| `intract_manifest_gap` | A manifest contract has not yet been reflected in capsule source files. |
| `intract_policy_warning` | Intract returned a partial or warning-level policy result. |
| `intract_policy_violation` | Intract returned a violation or failing policy result. |
| `intract_integration_fallback` | Intract was unavailable or failed, so nexu continued with a warning. |

## Dynamic Intract adapter

`verify_capsule` keeps the deterministic nexu gates local, then delegates optional Intract policy validation through `src/nexu/intract_adapter.py`. The adapter searches for a sibling `intract/src` package near the workspace and falls back to the installed import path. If that integration fails, verification records a warning instead of aborting the capsule report.

## Evidence files

Verification writes:

```text
.nexu/capsules/<name>/evidence/verification.yaml
```

Diff writes:

```text
.nexu/capsules/<name>/evidence/diff.yaml
```

Source drift writes:

```text
.nexu/capsules/<name>/evidence/source-drift.yaml
```
