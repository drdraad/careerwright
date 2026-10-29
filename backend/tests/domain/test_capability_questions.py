"""The combined question graph (spec section 9, "Adaptive question budget"; S4.3; ASSESS-03;
ADR 0012): one graph across the active targets, shared answers reused, gates first, then a
decision-impact ordering; 8 to 12 initial prompts; stop or pause; coverage as counts."""

import pytest

from nessa.capability.evidence import Holding
from nessa.capability.matrix import Importance, Matrix, build_matrix
from nessa.capability.questions import QuestionReason, question_graph
from nessa.capability.reference import load_reference
from nessa.catalogue.option_pack import load_pack
from tests.support.capability import (
    gate_row,
    self_report,
    skill_row,
    statement,
    synthetic_matrix,
)

PACK = load_pack("0.1.0")
REFERENCE = load_reference("0.1.0", PACK)


def pack_matrix(target_id: str) -> Matrix:
    target = next(t for t in PACK.targets if t.target_id == target_id)
    return build_matrix(
        target.title,
        pack=PACK,
        reference=REFERENCE,
        pack_target=target,
        occupation=None,
        exemplars=0,
    )


@pytest.mark.req("ASSESS-03")
def test_one_graph_across_targets_asks_a_shared_subject_once_against_each_rubric() -> None:
    first = synthetic_matrix(
        "Target A",
        [skill_row("fixture:shared", 2, "rubric-a"), skill_row("fixture:a", 2, "rubric-a")],
    )
    second = synthetic_matrix("Target B", [skill_row("fixture:shared", 3, "rubric-b")])

    graph = question_graph([first, second], evidence=[], statements=[], evidence_version=0)

    shared = next(p for p in graph.prompts if p.subject == "fixture:shared")
    assert [(r.target_title, r.rubric_version, r.required_level) for r in shared.rows] == [
        ("Target A", "rubric-a", 2),
        ("Target B", "rubric-b", 3),
    ]
    assert shared.route_impact == 2
    alone = next(p for p in graph.prompts if p.subject == "fixture:a")
    assert shared.priority > alone.priority
    assert [p.subject for p in graph.prompts] == ["fixture:shared", "fixture:a"]


@pytest.mark.req("ASSESS-03")
def test_gates_are_asked_first_whatever_the_skills_score() -> None:
    gate = gate_row("fixture:registration")
    matrix = synthetic_matrix(
        "Target", [skill_row(f"fixture:s{n}", 2, "r") for n in range(3)] + [gate]
    )

    graph = question_graph([matrix], evidence=[], statements=[], evidence_version=0)

    assert graph.prompts[0].subject == gate.subject
    assert graph.prompts[0].kind == "requirement"
    assert graph.prompts[0].reason is QuestionReason.NOT_STATED


@pytest.mark.req("ASSESS-03")
def test_the_first_prompts_are_at_most_twelve_and_the_rest_wait() -> None:
    rows = [skill_row(f"fixture:s{n:02}", 2, "r") for n in range(15)]
    graph = question_graph(
        [synthetic_matrix("Target", rows)], evidence=[], statements=[], evidence_version=0
    )

    assert len(graph.prompts) == 15
    assert graph.initial == [p.prompt_id for p in graph.prompts[:12]]
    assert graph.state == "asking"


@pytest.mark.req("ASSESS-03")
def test_answered_rows_drop_out_and_weak_answers_say_why_they_are_asked_again() -> None:
    first = synthetic_matrix(
        "Target A",
        [skill_row("fixture:done", 2, "rubric-a"), skill_row("fixture:claimed", 2, "rubric-a")],
    )
    second = synthetic_matrix("Target B", [skill_row("fixture:done", 2, "rubric-b")])
    evidence = [
        self_report("fixture:done", 2, "rubric-a"),
        self_report("fixture:claimed", 3, "rubric-a", example=None, last_done=None),
    ]

    graph = question_graph([first, second], evidence=evidence, statements=[], evidence_version=2)

    reasons = {p.subject: p.reason for p in graph.prompts}
    assert reasons == {
        "fixture:done": QuestionReason.OTHER_RUBRIC,  # answered for A; B's rubric differs
        "fixture:claimed": QuestionReason.UNSUPPORTED_CLAIM,
    }
    done = next(p for p in graph.prompts if p.subject == "fixture:done")
    assert [r.target_title for r in done.rows] == ["Target B"]  # A's row needs nothing more
    assert done.reuse_evidence_ids == [evidence[0].evidence_id]


@pytest.mark.req("ASSESS-03")
def test_asking_stops_when_gates_are_known_and_most_weighted_rows_have_evidence() -> None:
    gate = gate_row("fixture:registration")
    rows = [skill_row(f"fixture:s{n}", 2, "r") for n in range(5)]
    matrix = synthetic_matrix("Target", [gate, *rows])
    four = [self_report(f"fixture:s{n}", 2, "r") for n in range(4)]
    unresolved = [statement(gate.subject, Holding.UNKNOWN)]

    before = question_graph([matrix], evidence=four, statements=[], evidence_version=1)
    enough = question_graph([matrix], evidence=four, statements=unresolved, evidence_version=2)
    three = question_graph([matrix], evidence=four[:3], statements=unresolved, evidence_version=2)
    paused = question_graph([matrix], evidence=[], statements=[], evidence_version=0, stopped=True)

    assert before.state == "asking"  # a gate is neither known nor marked unresolved
    assert enough.state == "enough"  # gate marked unresolved; 4 of 5 weighted rows
    assert three.state == "asking"
    assert paused.state == "stopped"
    assert paused.prompts  # stopping keeps every open question, unasked
    coverage = enough.coverage
    assert (coverage.gates_known, coverage.gates) == (1, 1)
    assert (coverage.required_rows_with_usable_evidence, coverage.required_rows) == (4, 5)
    assert gate.subject in coverage.unresolved
    # Coverage is counts, never a percentage or an employability score.
    assert not any("percent" in key or "employab" in key for key in coverage.model_dump())


@pytest.mark.req("ASSESS-03")
def test_preferred_rows_weigh_less_than_essential_and_unmodelled_rows_are_not_asked() -> None:
    essential = skill_row("fixture:essential", 2, "r")
    preferred = skill_row("fixture:preferred", 2, "r", importance="preferred")
    unmodelled = skill_row("fixture:unmodelled", 2, "r").model_copy(
        update={"rubric": None, "required_level": None}
    )

    graph = question_graph(
        [synthetic_matrix("Target", [preferred, essential, unmodelled])],
        evidence=[],
        statements=[],
        evidence_version=0,
    )

    assert [p.subject for p in graph.prompts] == ["fixture:essential", "fixture:preferred"]
    assert graph.prompts[0].importance_weight > graph.prompts[1].importance_weight


@pytest.mark.req("ASSESS-03")
def test_the_pack_targets_ask_their_gate_first_and_carry_their_versions() -> None:
    it = pack_matrix("it-support-technician-bristol")
    data = pack_matrix("data-quality-analyst-manchester")

    graph = question_graph([data, it], evidence=[], statements=[], evidence_version=0)

    assert graph.prompts[0].subject == "gate:uk-right-to-work"
    assert len(graph.prompts) == 7  # one gate, six modelled rows
    assert all(p.rows[0].anchors for p in graph.prompts if p.kind == "skill")
    assert [(t.target_key, t.matrix_version, t.definition_version) for t in graph.targets] == [
        (m.target_key, m.matrix_version, m.definition_version) for m in (data, it)
    ]
    assert graph.evidence_version == 0
    importance = {p.subject: p.importance_weight for p in graph.prompts if p.kind == "skill"}
    disputed = next(r for r in data.rows if r.importance is Importance.DISPUTED)
    essential = next(r for r in data.rows if r.importance is Importance.ESSENTIAL)
    assert importance[essential.subject] > importance[disputed.subject]
