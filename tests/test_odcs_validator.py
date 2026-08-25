"""Behavior of the ODCS v3.1.0 contract validator shipped with ontology-forge."""

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

VALIDATOR = (
    Path(__file__).resolve().parents[1]
    / "plugins/ontology-forge/skills/write-contracts/scripts/validate_contract.py"
)

MINIMAL = """\
apiVersion: v3.1.0
kind: DataContract
id: 3f2a91c4-7b8e-4d21-9c33-1a5e6f0b7d42
name: crm_customer_export
version: 1.0.0
status: active
schema:
  - name: crm_customer
    logicalType: object
    description: One row per customer known to the CRM.
    properties:
      - name: customer_id
        logicalType: string
        physicalType: VARCHAR(36)
        required: true
        primaryKey: true
        primaryKeyPosition: 1
        description: Stable CRM identifier for the customer.
"""


def run(*args):
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), *args], capture_output=True, text=True, timeout=120
    )
    return result.returncode, result.stdout + result.stderr


def contract(tmp_path: Path, body: str, name: str = "c.odcs.yaml") -> Path:
    path = tmp_path / name
    path.write_text(textwrap.dedent(body))
    return path


def test_conformant_contract_passes(tmp_path):
    code, output = run(str(contract(tmp_path, MINIMAL)))
    assert code == 0, output
    assert "1/1 conformant" in output


@pytest.mark.parametrize("field", ["apiVersion", "kind", "id", "version", "status"])
def test_each_required_fundamental_is_enforced(tmp_path, field):
    body = "\n".join(line for line in MINIMAL.splitlines() if not line.startswith(f"{field}:"))
    code, output = run(str(contract(tmp_path, body)))
    assert code == 1
    assert field in output


def test_undefined_field_is_rejected_and_named(tmp_path):
    """v3.1.0's strictness: a field the standard does not define is an error, not an extension."""
    code, output = run(str(contract(tmp_path, MINIMAL + "        nullable: true\n")))
    assert code == 1
    assert "'nullable' was unexpected" in output
    # The inversion matters -- a mechanical rename to `required` flips the meaning.
    assert "inversion" in output


def test_invalid_logical_type_is_rejected(tmp_path):
    body = MINIMAL.replace("logicalType: string", "logicalType: datetime")
    code, output = run(str(contract(tmp_path, body)))
    assert code == 1
    assert "datetime" in output


def test_one_mistake_is_reported_once(tmp_path):
    """The schema composes subschemas, so an error can surface through several branches."""
    code, output = run(str(contract(tmp_path, MINIMAL + "        nullable: true\n")), "--json")
    assert code == 1
    errors = json.loads(output)["contracts"].popitem()[1]
    assert [e["location"] for e in errors].count("schema.0.properties.0") == 1


def test_directory_target_finds_contracts_recursively(tmp_path):
    (tmp_path / "inbound").mkdir()
    contract(tmp_path, MINIMAL, "inbound/a.odcs.yaml")
    contract(tmp_path, MINIMAL, "inbound/b.odcs.yaml")
    contract(tmp_path, "not: a contract\n", "inbound/notes.yaml")
    code, output = run(str(tmp_path))
    assert code == 0, output
    assert "2/2 conformant" in output


def test_unparseable_yaml_is_reported_not_raised(tmp_path):
    code, output = run(str(contract(tmp_path, "apiVersion: [unclosed\n")))
    assert code == 1
    assert "not valid YAML" in output


def test_unreadable_file_is_reported_as_a_finding(tmp_path):
    code, output = run(str(tmp_path / "nothing.odcs.yaml"))
    assert code == 1
    assert "cannot read" in output


def test_directory_with_no_contracts_is_a_usage_error(tmp_path):
    """Exit 2, not 0 -- an empty run must never read as "everything conformant"."""
    code, output = run(str(tmp_path))
    assert code == 2
    assert "no *.odcs.yaml files found" in output
