import base64
import json
import pickle

from spikes.durable.leak_scan import Needle, scan


def test_plain_occurrence_is_found_and_reported_without_the_secret() -> None:
    findings = scan(
        [("dbos.workflow_inputs", '{"args": ["sk-live-0123456789abcdef"]}')],
        [Needle(label="api key", value="sk-live-0123456789abcdef")],
    )

    assert [(f.location, f.needle_label) for f in findings] == [("dbos.workflow_inputs", "api key")]
    assert "0123456789abcdef" not in repr(findings)


def test_fragment_of_a_secret_is_found() -> None:
    # An error message that echoes a truncated key is still a leak.
    findings = scan(
        [("dbos.operation_outputs", '{"message": "Incorrect key sk-live-012345678***"}')],
        [Needle(label="api key", value="sk-live-0123456789abcdef", fragment_length=12)],
    )

    assert len(findings) == 1


def test_value_inside_base64_pickle_is_found() -> None:
    pickled = base64.b64encode(pickle.dumps({"prompt": "PRIVATE-CV-SENTINEL-42"})).decode()
    row = json.dumps({"output": pickled})

    findings = scan([("dbos.operation_outputs", row)], [Needle("cv", "PRIVATE-CV-SENTINEL-42")])

    assert len(findings) == 1


def test_json_escaped_value_is_found() -> None:
    row = json.dumps({"output": json.dumps({"text": 'quote "PRIVATE-CV-SENTINEL-42"'})})

    findings = scan([("dbos.workflow_outputs", row)], [Needle("cv", "PRIVATE-CV-SENTINEL-42")])

    assert len(findings) == 1


def test_value_inside_postgres_bytea_hex_is_found() -> None:
    # row_to_json renders bytea as "\\x<hex>"; plaintext stored as bytes must not hide there.
    row = json.dumps({"ciphertext": "\\x" + b"PRIVATE-CV-SENTINEL-42".hex()})

    findings = scan([("public.private_payloads", row)], [Needle("cv", "PRIVATE-CV-SENTINEL-42")])

    assert [f.encoding for f in findings] == ["hex"]


def test_identifiers_only_journal_has_no_findings() -> None:
    row = json.dumps({"inputs": json.dumps({"positionalArgs": ["run-7f3a"]})})

    assert scan([("dbos.workflow_inputs", row)], [Needle("cv", "PRIVATE-CV-SENTINEL-42")]) == []
