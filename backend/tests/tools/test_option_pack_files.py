"""The option pack's derived files (Task 7b fix round 1; ADR 0011): the session 2 package and
the JSON Schema are exactly what `tools.option_pack_files` writes from the pinned pack, so the
package's question numbers stay stable for Task 7c; and a pack is published only in its
canonical form, never with a problem."""

import json
import re
from pathlib import Path

import pytest

from nessa.catalogue.option_pack import PINS, SCHEMA_PATH, load_pack, pack_path
from tools.option_pack_files import (
    PACKAGE_PATH,
    PACKAGE_VERSION,
    TRACE_PERSONA,
    parts,
    publish,
    review_package,
    schema_text,
)


@pytest.mark.req("TEST1-09")
def test_the_committed_session_2_package_is_the_tool_s_output_for_the_pinned_pack() -> None:
    assert PACKAGE_PATH.read_text(encoding="utf-8") == review_package(load_pack(PACKAGE_VERSION))


@pytest.mark.req("OPTN-10")
def test_the_committed_schema_is_the_format_s_export() -> None:
    assert SCHEMA_PATH.read_text(encoding="utf-8") == schema_text()


@pytest.mark.req("TEST1-09", "OUT1-10")
def test_the_package_asks_every_entry_gate_and_every_pay_money_or_date_fact() -> None:
    # Reproduced in the first package (review I1): J06's first pay range, the courses' entry
    # requirements and the ungated essential credentials were never shown beside a span.
    pack = load_pack(PACKAGE_VERSION)
    text = review_package(pack)
    cited = set(re.findall(r"\(([JCF][0-9]{2}\.[a-z0-9_.]+), (?:offsets|pointer)", text))
    asked_records = set(re.findall(r"^\| Q[0-9]+ \| `([^`]+)`", text, flags=re.MULTILINE))

    entry = {c for o in pack.learning_options for c in o.entry_requirements}
    assert entry
    assert entry <= cited
    assert {"J06.salary", "J06.salary_conflict", "J01.salary_point", "C06.intakes_stated"} <= cited
    essential = {
        r.record_id
        for r in pack.skill_requirements
        if r.importance == "essential" and r.kind in ("credential", "eligibility")
    }
    assert {"req:J05.5", "req:J10.2", "req:J14.1", "req:J15.4", "req:J15.5"} <= essential
    assert essential <= asked_records
    assert {"F01.instrument_kind", "F02.instrument_kind"} <= cited


@pytest.mark.req("TEST1-09")
def test_a_stated_no_end_is_shown_as_one_a_reviewer_can_confirm() -> None:
    # Reproduced in the round 2 package (review R2-1): "Lifetime access" showed "unknown
    # (null)", a row the reviewer had to answer no.
    text = review_package(load_pack(PACKAGE_VERSION))
    [row] = [line for line in text.splitlines() if "(C03.access_period," in line]

    assert "| no end (lifetime) |" in row


@pytest.mark.req("TEST1-09")
def test_the_parts_follow_the_gates_and_keep_each_record_in_one_part() -> None:
    pack = load_pack(PACKAGE_VERSION)
    first, second, third = parts(pack)
    part_of: dict[str, set[int]] = {}
    for n, part in enumerate((first, second, third)):
        for _, rows in part.sections:
            for row in rows:
                part_of.setdefault(row.record_id, set()).add(n)

    assert all(len(found) == 1 for found in part_of.values())  # the partial-record rule
    trace = next(t.target_id for t in pack.targets if t.persona == TRACE_PERSONA)
    assert first.sections
    assert all(trace in heading for heading, _ in first.sections)
    jobs = {j.record_id for j in pack.job_postings}
    assert not jobs & {r.record_id for _, rows in second.sections for r in rows}
    assert {r.record_id for _, rows in third.sections for r in rows} <= jobs | {
        q.record_id for q in pack.skill_requirements
    }


@pytest.mark.req("OPTN-10")
def test_a_pack_is_published_in_canonical_form_and_never_with_a_problem(tmp_path: Path) -> None:
    committed = pack_path(PACKAGE_VERSION)
    data = json.loads(committed.read_text(encoding="utf-8"))
    source = tmp_path / "pack.json"
    source.write_text(json.dumps(data), encoding="utf-8")  # one line: not the canonical text

    written, digest = publish(source, packs_dir=tmp_path)

    assert written.read_bytes() == committed.read_bytes()
    assert digest == PINS[PACKAGE_VERSION]

    data["claims"][0]["value"] = {"title": "not text"}
    source.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(SystemExit, match=r"refused: J01\.title is not text"):
        publish(source, packs_dir=tmp_path)
