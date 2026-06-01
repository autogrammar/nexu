import sys
from pathlib import Path

try:
    from intract import (
        IntentContract,
        format_intract_v1_line,
        parse_intract_line,
        read_manifest_contracts,
        read_toon_manifest_contracts,
        scan_contracts_in_file,
        scan_contracts_in_text,
    )
except ImportError:
    # Dynamically find sibling intract repository and add to sys.path
    curr = Path(__file__).resolve()
    found = False
    for _ in range(6):
        for candidate in (curr / "intract" / "src", curr.parent / "intract" / "src"):
            if candidate.is_dir():
                sys.path.insert(0, str(candidate))
                found = True
                break
        if found:
            break
        curr = curr.parent

    from intract import (
        IntentContract,
        format_intract_v1_line,
        parse_intract_line,
        read_manifest_contracts,
        read_toon_manifest_contracts,
        scan_contracts_in_file,
        scan_contracts_in_text,
    )

__all__ = [
    "IntentContract",
    "format_intract_v1_line",
    "parse_intract_line",
    "read_manifest_contracts",
    "read_toon_manifest_contracts",
    "scan_contracts_in_file",
    "scan_contracts_in_text",
]
