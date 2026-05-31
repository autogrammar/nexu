from __future__ import annotations

import json
from pathlib import Path

import yaml

from .blueprint import build_blueprint
from .capsule import load_capsule
from .diff import diff_capsule
from .intract import read_manifest_contracts
from .models import PromptExport, utc_now, write_yaml
from .paths import capsule_dir


def _cinema_policy_ledger_block(base: Path) -> str:
    ledger_path = base / "cinema" / "intract_policy_ledger.json"
    if not ledger_path.exists():
        return ""

    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""

    if not isinstance(ledger, list) or not ledger:
        return ""

    lines: list[str] = []
    for entry in ledger[-8:]:
        if not isinstance(entry, dict):
            continue
        status = entry.get("status", "")
        stage = entry.get("stage", "?")
        lines.append(f"- iteration S{stage} ({status})")
        for proposal in entry.get("proposed_contracts", []) or []:
            if isinstance(proposal, dict) and proposal.get("line"):
                lines.append(f"  - `{proposal['line']}`")

    if not lines:
        return ""

    return (
        "## Cinema policy ledger (proposed @intract.v1)\n\n"
        "These lines were generated from Cinema iterations. Preserve intent when evolving code;\n"
        "merge into `intract.yaml` with `intract manifest apply-ledger` or update manifests explicitly.\n\n"
        + "\n".join(lines)
        + "\n\n"
    )


def _latest_iteration(capsule) -> str:
    if capsule.iterations:
        return capsule.iterations[-1]
    return "S0"


def export_iteration_prompt(root: Path, name: str, *, iteration: str | None = None) -> PromptExport:
    capsule = load_capsule(root, name)
    selected_iteration = iteration or _latest_iteration(capsule)
    base = capsule_dir(root, name)
    contracts = read_manifest_contracts(base / capsule.contracts_manifest)
    blueprint = build_blueprint(root, name)
    diff = diff_capsule(root, name)

    contract_block = yaml.safe_dump(
        [
            {
                "id": contract.contract_id,
                "intent": contract.intent,
                "scope": contract.scope,
                "domain": contract.domain,
                "input": contract.input,
                "output": contract.output,
                "effect": contract.effect,
                "forbid": contract.forbid,
                "require": contract.require,
                "validate": contract.validate,
                "meaning": contract.meaning,
            }
            for contract in contracts
        ],
        sort_keys=False,
        allow_unicode=True,
    )
    blueprint_block = yaml.safe_dump(blueprint, sort_keys=False, allow_unicode=True)
    diff_block = yaml.safe_dump(diff.to_dict(), sort_keys=False, allow_unicode=True)
    cinema_ledger_block = _cinema_policy_ledger_block(base)

    prompt = f"""# nexu LLM iteration prompt

Capsule: `{name}`
Iteration: `{selected_iteration}`
Created at: {utc_now()}

## Mission

Evolve only the isolated capsule. Do not mutate the source project directly.
Every change must remain compatible with the Intract intent contracts.

## Hard rules

- Work only under `.nexu/capsules/{name}/src`.
- Preserve or explicitly update `intract.yaml` when intent changes.
- Do not violate `forbid` fields.
- For every declared `output`, add code, fixture, UI, API, or test evidence.
- After changing the capsule, run `nexu capsule verify {name}`.
- If the requested change needs writes, split preview and apply into separate contracts.

## Intract format for new or updated intent

When you add or change behavior, emit intent as `@intract.v1` lines (inline) or YAML manifest entries:

```text
@intract.v1 id:<unique> scope:function|ui|file intent:<action>:<object> priority:1-5 domain:<area> input:<csv> output:<csv> effect:<csv> forbid:<csv> require:<csv> validate:input_presence,output_presence,no_forbidden_effect meaning:"why"
```

Optional LLM-assisted proposals (requires `intract[llm]`):

```bash
intract propose llm --file <artifact> --goal "<goal>"
intract propose delta --delete <id> --keep <id> --stage 0 --capsule {name}
```

Validate deterministically (no LLM required for validation):

```bash
intract validate .
vallm validate --file <path> --intract
```

{cinema_ledger_block}## Intract contracts

```yaml
{contract_block}```

## Current blueprint

```yaml
{blueprint_block}```

## Current capsule diff from baseline

```yaml
{diff_block}```

## Expected response from the LLM/agent

1. Summary of changed files.
2. Why the change satisfies the intent.
3. Evidence for each output.
4. Any remaining risks or missing tests.
"""

    prompt_path = base / "prompts" / f"{selected_iteration}.llm.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt, encoding="utf-8")
    export = PromptExport(capsule=name, iteration=selected_iteration, path=str(prompt_path))
    write_yaml(base / "prompts" / f"{selected_iteration}.llm.yaml", export.to_dict())
    return export
