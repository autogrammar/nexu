from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class IntentContract:
    raw: str
    contract_id: str = ""
    scope: str = "block"
    intent: str = ""
    priority: int = 3
    domain: str = "general"
    input: list[str] = field(default_factory=list)
    output: list[str] = field(default_factory=list)
    effect: list[str] = field(default_factory=list)
    forbid: list[str] = field(default_factory=list)
    require: list[str] = field(default_factory=list)
    validate: list[str] = field(default_factory=list)
    meaning: str = ""
    source: str = ""
    line: int = 0

    @property
    def key(self) -> str:
        return self.contract_id or self.intent or self.raw


def format_intract_v1_line(contract: IntentContract) -> str:
    meaning = contract.meaning.replace('"', "'") if contract.meaning else ""
    meaning_part = f' meaning:"{meaning}"' if meaning else ""
    return (
        f"@intract.v1 id:{contract.contract_id} scope:{contract.scope} "
        f"intent:{contract.intent} priority:{contract.priority} domain:{contract.domain}"
        f"{meaning_part}"
    )


def _split_csv(value: str) -> list[str]:
    if value.lower() in {"", "none", "null", "-"}:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _tokenize_contract(line: str) -> dict[str, str]:
    # Small pragmatic tokenizer for @intract.v1 fields. Keeps quoted meaning text.
    payload = line.split("@intract.v1", 1)[1].strip()
    meaning = ""
    match = re.search(r'meaning:"([^"]*)"', payload)
    if match:
        meaning = match.group(1)
        payload = payload[: match.start()] + payload[match.end():]
    fields: dict[str, str] = {}
    for token in payload.split():
        if ":" not in token:
            continue
        key, value = token.split(":", 1)
        fields[key.strip()] = value.strip()
    if meaning:
        fields["meaning"] = meaning
    return fields


def parse_intract_line(
    line: str,
    *,
    source: str = "",
    line_number: int = 0,
) -> IntentContract | None:
    if "@intract.v1" not in line:
        return None
    fields = _tokenize_contract(line)
    raw = line.strip()
    return IntentContract(
        raw=raw,
        contract_id=fields.get("id", ""),
        scope=fields.get("scope", "block"),
        intent=fields.get("intent", ""),
        priority=int(fields.get("priority", "3") or "3"),
        domain=fields.get("domain", "general"),
        input=_split_csv(fields.get("input", "")),
        output=_split_csv(fields.get("output", "")),
        effect=_split_csv(fields.get("effect", "")),
        forbid=_split_csv(fields.get("forbid", "")),
        require=_split_csv(fields.get("require", "")),
        validate=_split_csv(fields.get("validate", "")),
        meaning=fields.get("meaning", ""),
        source=source,
        line=line_number,
    )


def scan_contracts_in_text(text: str, *, source: str = "") -> list[IntentContract]:
    contracts = []
    for index, line in enumerate(text.splitlines(), start=1):
        contract = parse_intract_line(line, source=source, line_number=index)
        if contract is not None:
            contracts.append(contract)
    return contracts


def scan_contracts_in_file(path: Path, root: Path | None = None) -> list[IntentContract]:
    source = path.relative_to(root).as_posix() if root else path.as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    return scan_contracts_in_text(text, source=source)


def read_manifest_contracts(path: Path) -> list[IntentContract]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    contracts: list[IntentContract] = []
    for item in data.get("contracts", []) or []:
        intent = str(item.get("intent", ""))
        contract = IntentContract(
            raw=f"manifest:{item.get('id', intent)}",
            contract_id=str(item.get("id", "")),
            scope=str(item.get("scope", "project")),
            intent=intent,
            priority=int(item.get("priority", 3) or 3),
            domain=str(item.get("domain", "general")),
            input=list(item.get("input", []) or []),
            output=list(item.get("output", []) or []),
            effect=list(item.get("effect", []) or []),
            forbid=list(item.get("forbid", []) or []),
            require=list(item.get("require", []) or []),
            validate=list(item.get("validate", []) or []),
            meaning=str(item.get("meaning", "")),
            source=str(path),
            line=0,
        )
        contracts.append(contract)
    return contracts
