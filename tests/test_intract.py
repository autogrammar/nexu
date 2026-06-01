from pathlib import Path
from nexu.intract import parse_intract_line, read_toon_manifest_contracts


def test_parse_intract_line():
    contract = parse_intract_line(
        '# @intract.v1 scope:function intent:query:user_list priority:2 domain:users input:filters output:user_list effect:read forbid:write validate:output_presence meaning:"list users"'
    )
    assert contract is not None
    assert contract.intent == "query:user_list"
    assert contract.domain == "users"
    assert "write" in contract.forbid


def test_parse_toon_manifest(tmp_path: Path):
    yaml_content = """
contracts:
  - id: toon-rule-01
    intent: forbid-writes
    priority: 1
    forbid: [destructive_write, write]
    target:
      file: "src/calculator.py"
      function: "add"
      line: 45
  - id: toon-rule-02
    intent: validate-xpath
    target:
      file: "index.html"
      xpath: "//div[@class='screen']"
"""
    manifest = tmp_path / "intract.toon.yaml"
    manifest.write_text(yaml_content, encoding="utf-8")
    contracts = read_toon_manifest_contracts(manifest)
    assert len(contracts) == 2
    
    c1 = contracts[0]
    assert c1.contract_id == "toon-rule-01"
    assert c1.intent == "forbid-writes"
    assert "destructive_write" in c1.forbid
    assert c1.target_file == "src/calculator.py"
    assert c1.target_function == "add"
    assert c1.target_line == 45
    
    c2 = contracts[1]
    assert c2.contract_id == "toon-rule-02"
    assert c2.target_xpath == "//div[@class='screen']"

