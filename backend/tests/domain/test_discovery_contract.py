"""The discovery contract (S2.4; REC-1, DIV-1): the model turns the confirmed profile into
search queries, a few title hypotheses and up to six "aim higher" title ideas (Task 6g slice
B); deterministic code checks that every query and idea rests on the person's own answers and
carries no inference about them. Semantic checks only."""

import json
import uuid
from typing import Any

import pytest

from careerwright.profile.dashes import DASH_RULE, EM_DASH, EN_DASH
from careerwright.profile.discovery import (
    EVIDENCE_FIELDS,
    INSTRUCTIONS,
    MAX_AIM_HIGHER,
    MAX_HYPOTHESES,
    MAX_PROMPT_BYTES,
    MAX_QUERIES,
    PROMPT_VERSION,
    SCHEMA_ALLOWANCE_TOKENS,
    DiscoveryInput,
    DiscoveryOutput,
    DiscoveryProposal,
    EvidenceItem,
    QueryChannel,
    check_discovery,
    evidence_of,
    input_of,
    prompt_bytes,
    render_prompt,
    worst_case_nano_usd,
)
from careerwright.profile.document import (
    FIELD_NAMES,
    ProfileInput,
    apply_profile_input,
    apply_updates,
    empty_profile,
    input_type,
)
from careerwright.profile.exploration import release_note, stays_current
from careerwright.profile.fixture_discovery import fixture_queries, prompt_context
from careerwright.profile.interview import ProfileField, ProposalOrigin
from careerwright.profile.slate_facts import ReleaseChanged

SOURCE = uuid.UUID("00000000-0000-4000-8000-0000000000aa")


def document(**fields: Any) -> Any:
    values: dict[str, Any] = {name: {"state": "unasked"} for name in FIELD_NAMES}
    values.update({k: {"state": "provided", "value": v} for k, v in fields.items()})
    return apply_profile_input(empty_profile(), ProfileInput.model_validate(values), SOURCE)


P02 = document(
    enjoyed_tasks=["repairing physical objects", "working outdoors"],
    work_style=["practical", "small team"],
    cities=["Leeds", "Manchester"],
    weekly_study_hours=12,
)


def context(doc: Any = P02) -> DiscoveryInput:
    return input_of(doc, profile_version=3)


def query(text: str, channel: str = "tasks", *based_on: str) -> dict[str, Any]:
    return {"text": text, "channel": channel, "based_on": list(based_on) or ["working outdoors"]}


def idea(title: str, *based_on: str) -> dict[str, Any]:
    return {"title": title, "based_on": list(based_on) or ["working outdoors"]}


def output(
    *queries: dict[str, Any],
    hypotheses: list[dict[str, Any]] | None = None,
    aim_higher: list[dict[str, Any]] | None = None,
) -> Any:
    return DiscoveryOutput.model_validate(
        {"queries": list(queries), "hypotheses": hypotheses or [], "aim_higher": aim_higher or []}
    )


# The synthetic school leaver (fixtures/synthetic/school-leaver.json): A-levels expected.
MAYA = document(
    enjoyed_tasks=[
        "doing practicals in the chemistry lab",
        "helping the younger girls with crafts",
    ],
    evidenced_tasks=["help run a Brownies group"],
    qualifications=[
        {"name": "A-level biology", "status": "expected"},
        {"name": "GCSE maths", "status": "achieved"},
    ],
)


def problems(out: DiscoveryOutput, ctx: DiscoveryInput | None = None) -> list[str]:
    proposal, found = check_discovery(out, ctx or context(), ProposalOrigin.MODEL)
    assert (proposal is None) == bool(found)
    return found


def answered(doc: Any, source: uuid.UUID, **fields: Any) -> Any:
    """The next document: these fields answered, citing `source`."""
    updates = {
        name: (input_type(name).model_validate({"state": "provided", "value": value}), source)
        for name, value in fields.items()
    }
    return apply_updates(doc, updates)[0]


@pytest.mark.req("STATE-10")
def test_a_slate_stays_current_while_only_targets_chosen_from_it_change() -> None:
    pinned = document(current_role="warehouse supervisor", cities=["Leeds"])
    chose, chose_again, typed = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    first = answered(pinned, chose, target_titles=["logistics manager"])
    second = answered(first, chose_again, target_titles=["logistics manager", "statistician"])
    choices = frozenset({chose, chose_again})

    assert stays_current([pinned], choices)  # nothing changed since
    assert stays_current([pinned, first, second], choices)
    # Any other change, or a target the person typed in, means the answers changed.
    assert not stays_current([pinned, first, answered(first, typed, cities=["York"])], choices)
    assert not stays_current(
        [pinned, answered(pinned, typed, target_titles=["statistician"])], choices
    )


def unanswered(doc: Any, source: uuid.UUID, name: str, state: str) -> Any:
    """The next document: this field answered `state` (Unknown, Skipped…), citing `source`."""
    update = (input_type(name).model_validate({"state": state}), source)
    return apply_updates(doc, {name: update})[0]


@pytest.mark.req("STATE-10")
def test_removing_a_target_or_putting_one_back_leaves_a_slate_current() -> None:
    # Session W2 (finding 2): removing a target asks the slate nothing new, so it never becomes
    # "based on your earlier answers" with Suggest again (paid) as the bright action. Removing
    # the last leaves the target roles Unknown (Task W2F's ruling); Undo puts back what was.
    pinned = document(current_role="warehouse supervisor", target_titles=["zoo keeper", "vet"])
    chose, removed_by, undone_by, typed = (uuid.uuid4() for _ in range(4))
    choices = frozenset({chose})
    one_left = answered(pinned, removed_by, target_titles=["vet"])
    none_left = unanswered(one_left, removed_by, "target_titles", "unknown")
    put_back = answered(none_left, undone_by, target_titles=["zoo keeper", "vet"])

    assert stays_current([pinned, one_left], choices)
    assert stays_current([pinned, one_left, none_left], choices)
    assert stays_current([pinned, one_left, none_left, put_back], choices)
    # A suggestion made a target, removed, then typed back is still one this slate suggested;
    # undoing the choice leaves the targets as the slate found them.
    chosen = answered(pinned, chose, target_titles=["zoo keeper", "vet", "statistician"])
    dropped = answered(chosen, removed_by, target_titles=["zoo keeper", "vet"])
    retyped = answered(dropped, typed, target_titles=["zoo keeper", "vet", "statistician"])
    assert stays_current([pinned, chosen, dropped, retyped], choices)
    assert stays_current(
        [pinned, chosen, answered(chosen, undone_by, target_titles=["zoo keeper", "vet"])], choices
    )
    # A target the slate wasn't made with, typed in after a removal, is still a change; so is
    # any other answer changed beside a removal.
    assert not stays_current(
        [pinned, one_left, answered(one_left, typed, target_titles=["vet", "astronaut"])], choices
    )
    assert not stays_current([pinned, answered(one_left, removed_by, cities=["York"])], choices)


@pytest.mark.req("STATE-10", "DIV1-16")
def test_a_title_idea_of_the_slate_made_a_target_leaves_it_current() -> None:
    # Task 6g slice B: a title idea only the UK job-title index lists is made a target through
    # the profile's one write path (a save of the targets, as a found role's is). It is a title
    # the slate itself suggested, so it asks the slate nothing new.
    pinned = document(current_role="Client onboarding assistant")
    saved = uuid.uuid4()
    ideas = frozenset({"Customer success manager"})
    idea = answered(pinned, saved, target_titles=["Customer success manager"])
    other = answered(pinned, saved, target_titles=["Customer success manager", "Astronaut"])

    assert stays_current([pinned, idea], frozenset(), ideas)
    assert not stays_current([pinned, idea], frozenset())  # not one of this slate's ideas
    assert not stays_current([pinned, other], frozenset(), ideas)  # another title typed in


@pytest.mark.req("STATE-10", "REC1-03")
def test_a_change_to_the_tasks_the_person_doesnt_enjoy_alone_leaves_a_slate_current() -> None:
    # Task W2F: no suggestion reads them, so changing them asks the slate nothing new.
    pinned = document(enjoyed_tasks=["repairing physical objects"])
    edited = uuid.uuid4()
    disliked = answered(pinned, edited, disliked_tasks=["filling in forms"])
    more = answered(disliked, edited, disliked_tasks=["filling in forms", "early starts"])
    skipped = unanswered(more, edited, "disliked_tasks", "skipped")

    assert stays_current([pinned, disliked, more, skipped], frozenset())
    # Beside another answer's change, the answers still changed.
    assert not stays_current(
        [pinned, answered(disliked, edited, enjoyed_tasks=["repairing bikes"])], frozenset()
    )


@pytest.mark.req("REC1-01", "DIV1-10")
def test_the_evidence_is_the_confirmed_answers_that_describe_work_and_nothing_else() -> None:
    evidence = evidence_of(P02)

    assert [(item.field, item.text) for item in evidence] == [
        (ProfileField.ENJOYED_TASKS, "repairing physical objects"),
        (ProfileField.ENJOYED_TASKS, "working outdoors"),
        (ProfileField.WORK_STYLE, "practical"),
        (ProfileField.WORK_STYLE, "small team"),
    ]  # no cities, hours, money or name: they are limits, not descriptions of work
    prompt = render_prompt(context())
    assert "Leeds" not in prompt
    assert "12" not in prompt


@pytest.mark.req("REC1-03")
def test_tasks_the_person_doesnt_enjoy_inform_only_and_never_reach_discovery() -> None:
    # Task W2F: what the person doesn't enjoy is never a search, a filter or a ranking input.
    # Discovery, the slate, its written explanation and the strength all read `evidence_of`.
    disliking = document(
        enjoyed_tasks=["repairing physical objects"], disliked_tasks=["filling in forms"]
    )
    only_dislikes = document(disliked_tasks=["filling in forms"])

    assert ProfileField.DISLIKED_TASKS not in EVIDENCE_FIELDS
    assert [(item.field, item.text) for item in evidence_of(disliking)] == [
        (ProfileField.ENJOYED_TASKS, "repairing physical objects")
    ]
    assert "filling in forms" not in render_prompt(context(disliking))
    assert evidence_of(only_dislikes) == []  # so no discovery starts from dislikes alone


@pytest.mark.req("DIV1-02", "DIV1-10", "TEST1-10")
def test_a_valid_output_becomes_queries_that_cite_the_answers_they_come_from() -> None:
    out = output(
        query("machinery repair", "tasks", "repairing physical objects"),
        query("outdoor maintenance work", "environment", "working outdoors", "practical"),
        query("agricultural equipment", "less_familiar", "repairing physical objects"),
        hypotheses=[{"title": "Wind turbine technician", "based_on": ["working outdoors"]}],
    )

    proposal, found = check_discovery(out, context(), ProposalOrigin.MODEL)

    assert found == []
    assert proposal is not None
    assert [q.query_id for q in proposal.queries] == ["q1", "q2", "q3"]
    assert proposal.queries[1].channel is QueryChannel.ENVIRONMENT
    assert [(e.field, e.text) for e in proposal.queries[1].based_on] == [
        (ProfileField.ENJOYED_TASKS, "working outdoors"),
        (ProfileField.WORK_STYLE, "practical"),
    ]
    assert proposal.hypotheses[0].title == "Wind turbine technician"  # still a hypothesis
    assert proposal.profile_version == 3


@pytest.mark.req("REC1-02")
def test_a_search_may_name_who_the_work_serves_in_a_kindred_word() -> None:
    carer = document(enjoyed_tasks=["helping new mothers"])
    out = output(query("maternity support work for women", "tasks", "helping new mothers"))

    assert problems(out, context(carer)) == []


@pytest.mark.req("TAX1-01", "DIV1-04")
def test_the_searches_record_the_release_they_were_chosen_for_and_a_change_is_said() -> None:
    # Task 6 review A-M9: the slate is recomputed on each read, against the held release.
    pinned = context().model_copy(update={"release": "esco-v1.2.1-en-csv"})
    out = output(query("machinery repair", "tasks", "repairing physical objects"))

    proposal, _ = check_discovery(out, pinned, ProposalOrigin.MODEL)

    assert proposal is not None
    assert proposal.release == "esco-v1.2.1-en-csv"
    assert release_note("esco-v1.2.1-en-csv", "esco-v1.2.1-en-csv") is None
    assert release_note(None, "esco-v1.2.1-en-csv") is None  # chosen before it was recorded
    assert release_note("esco-v1.2.1-en-csv", "esco-v1.3.0-en-csv") == ReleaseChanged(
        searched="esco-v1.2.1-en-csv", held="esco-v1.3.0-en-csv"
    )


@pytest.mark.req("REC1-06", "DIV1-04")
def test_a_query_resting_on_something_the_person_never_said_is_refused() -> None:
    found = problems(output(query("forestry", "tasks", "loves trees")))

    assert any("based_on" in problem for problem in found)


@pytest.mark.req("REC1-09", "REC1-02")
@pytest.mark.parametrize(
    "text",
    ["jobs for older women", "work suited to ADHD", "roles for an ISTP", "female engineer"],
)
def test_a_query_using_demographics_health_or_a_type_the_person_never_gave_is_refused(
    text: str,
) -> None:
    assert any("did not mention" in p for p in problems(output(query(text))))


def test_bounds_duplicates_and_empty_output_are_problems() -> None:
    many = [query(f"repair work {n}") for n in range(MAX_QUERIES + 1)]
    hypotheses = [{"title": f"Title {n}", "based_on": ["working outdoors"]} for n in range(4)]

    assert problems(output(*many))
    assert problems(output(query("Repair work"), query("repair  work")))
    assert problems(output())
    assert problems(output(query("x")))  # too short to search
    assert len(hypotheses) > MAX_HYPOTHESES
    assert problems(output(query("repair work"), hypotheses=hypotheses))


LAB = query("perform laboratory tests", "tasks", "doing practicals in the chemistry lab")


@pytest.mark.req("DIV1-16", "DIV1-04", "PROF-13")
def test_aim_higher_ideas_cite_the_answers_or_qualifications_they_come_from() -> None:
    # Task 6g slice B: the one discovery call also proposes up to six "aim higher" title
    # ideas, each quoting the answers it came from; the person's qualifications are among them.
    out = output(
        LAB,
        aim_higher=[
            idea("Clinical scientist", "doing practicals in the chemistry lab", "A-level biology"),
            idea("Play therapist", "helping the younger girls with crafts"),
        ],
    )

    proposal, found = check_discovery(out, context(MAYA), ProposalOrigin.MODEL)

    assert found == []
    assert proposal is not None
    assert [h.title for h in proposal.aim_higher] == ["Clinical scientist", "Play therapist"]
    assert [(e.field, e.text) for e in proposal.aim_higher[0].based_on] == [
        (ProfileField.ENJOYED_TASKS, "doing practicals in the chemistry lab"),
        (ProfileField.QUALIFICATIONS, "A-level biology"),
    ]
    assert proposal.hypotheses == []


@pytest.mark.req("DIV1-16", "REC1-02", "REC1-06")
def test_aim_higher_ideas_are_checked_as_title_ideas_are() -> None:
    ctx = context(MAYA)
    many = [idea(f"Scientist {n}", "A-level biology") for n in range(MAX_AIM_HIGHER + 1)]
    unsaid = [idea("Forensic scientist", "loves crime dramas")]
    dashed = [idea(f"Lab manager {EM_DASH} hospital", "A-level biology")]

    assert problems(output(LAB, aim_higher=many), ctx) == [f"aim_higher: at most {MAX_AIM_HIGHER}"]
    assert problems(output(LAB, aim_higher=unsaid), ctx) == [
        "aim_higher 1: based_on must quote 1-3 of the person's answer texts exactly"
    ]
    assert problems(output(LAB, aim_higher=dashed), ctx) == [
        "aim_higher 1: no em dash or spaced en dash; use a comma, colon or full stop"
    ]
    inferring = output(LAB, aim_higher=[idea("ADHD coach", "A-level biology")])
    assert any("did not mention" in p for p in problems(inferring, ctx))
    # One title once, whichever list it is in.
    twice = output(
        LAB,
        hypotheses=[idea("Clinical scientist", "A-level biology")],
        aim_higher=[idea("clinical  Scientist", "A-level biology")],
    )
    assert problems(twice, ctx) == ["title ideas: each title once"]


@pytest.mark.req("DIV1-16", "PROF-13")
def test_the_prompt_reads_qualifications_with_their_status_an_expected_one_never_held() -> None:
    answers = json.loads(render_prompt(context(MAYA)).partition("\n")[2])["answers"]

    assert {"field": "qualifications", "text": "A-level biology", "status": "expected"} in answers
    assert {"field": "qualifications", "text": "GCSE maths", "status": "achieved"} in answers
    assert all("status" not in a for a in answers if a["field"] != "qualifications")
    said = " ".join(INSTRUCTIONS.split())
    assert "never treat an expected one as achieved" in said
    assert f"up to {MAX_AIM_HIGHER} titles" in said
    assert "never for its pay or status" in said
    assert PROMPT_VERSION == "discovery-queries-5"
    # Qualifications inform: the answers that describe work still decide whether one starts.
    only = document(qualifications=[{"name": "GCSE maths", "status": "achieved"}])
    assert evidence_of(only) == []


@pytest.mark.req("DIV1-16")
def test_a_proposal_sealed_before_aim_higher_ideas_has_none() -> None:
    sealed = {
        "origin": "model",
        "prompt_version": "discovery-queries-3",
        "profile_version": 2,
        "queries": [],
        "hypotheses": [],
    }

    assert DiscoveryProposal.model_validate_json(json.dumps(sealed)).aim_higher == []
    sealed_input = {"profile_version": 1, "evidence": []}
    assert DiscoveryInput.model_validate(sealed_input).qualifications == []


@pytest.mark.req("DIV1-10")
def test_the_fixture_proposer_reads_the_live_prompt_and_passes_the_same_check() -> None:
    ctx = context()

    out = fixture_queries(prompt_context(render_prompt(ctx)))
    proposal, found = check_discovery(out, ctx, ProposalOrigin.FIXTURE)

    assert found == []
    assert proposal is not None
    assert {q.text for q in proposal.queries} >= {"repairing physical objects", "working outdoors"}
    channels = {q.channel for q in proposal.queries}
    assert QueryChannel.ENVIRONMENT in channels  # the work style informs the search
    assert fixture_queries(prompt_context(render_prompt(ctx))) == out  # deterministic
    # It never invents a title: no hypothesis and no aim higher idea, and a qualification is
    # never searched (Task 6g slice B).
    maya = context(MAYA)
    demo = fixture_queries(prompt_context(render_prompt(maya)))
    assert (demo.hypotheses, demo.aim_higher) == ([], [])
    assert "A-level biology" not in {q.text for q in demo.queries}


def test_the_prompt_and_schema_fit_the_bounds_the_reservation_assumes() -> None:
    long_items = [f"{'a' * 100} {n}" for n in range(8)]
    busy = document(
        current_role="Warehouse shift supervisor",
        target_titles=["Data quality analyst", "Facilities technician", "Gardener"],
        enjoyed_tasks=long_items,
        confident_tasks=long_items,
        evidenced_tasks=long_items,
        work_style=long_items,
        # Task 6g slice B: the qualifications too, at their bound (eight of 120 characters).
        qualifications=[{"name": f"{'q' * 118} {n}", "status": "expected"} for n in range(8)],
    )
    assert prompt_bytes(context(busy)) <= MAX_PROMPT_BYTES
    schema = json.dumps(DiscoveryOutput.model_json_schema())
    assert len(schema.encode()) <= SCHEMA_ALLOWANCE_TOKENS
    for keyword in ("minLength", "maxLength", "maxItems", "minItems", "pattern", "format"):
        assert keyword not in schema
    assert "never use it to exclude" in INSTRUCTIONS


# Task W2F slice E (the product owner, 3 November 2026: "Em-dashes are outlawed!"): a query
# and a title idea are shown to the person in the model's words.
@pytest.mark.req("DIV1-01")
def test_a_query_or_title_idea_with_an_em_dash_is_refused_unless_it_is_the_person_s_own() -> None:
    role = f"Mechanic {EM_DASH} road bikes"
    own = document(current_role=role, enjoyed_tasks=["working outdoors"])
    dashed = output(
        query(f"repair bicycles {EM_DASH} road", "tasks", "working outdoors"),
        query(role, "transferable", role),  # the person's own title, their dash
        hypotheses=[{"title": f"cycle courier {EN_DASH} city", "based_on": ["working outdoors"]}],
    )

    assert problems(dashed, context(own)) == [
        "query 1: no em dash or spaced en dash; use a comma, colon or full stop",
        "hypothesis 1: no em dash or spaced en dash; use a comma, colon or full stop",
    ]
    # Version 4 brought the rule (slice E); version 5 keeps it (Task 6g slice B).
    assert PROMPT_VERSION in ("discovery-queries-4", "discovery-queries-5")
    assert DASH_RULE in INSTRUCTIONS


@pytest.mark.req("MODEL-08")
def test_an_attempt_reserves_both_requests_at_their_bounds() -> None:
    # Task 6g slice B: up to six more title ideas out, the qualifications in.
    # Input bound 10,000 + 1,500 + 2,000 + 1,000 = 14,500 tokens, output 2,000, two requests.
    # Contributor: (14,500 x 100 + 2,000 x 200) x 2 = 3,700,000 nano-USD ($0.0037).
    # Standard: (14,500 x 1,250 + 2,000 x 4,250) x 2 = 53,250,000 nano-USD ($0.05325).
    # Muse Wonder: (14,500 x 4,000 + 2,000 x 20,000) x 2 = 196,000,000 nano-USD ($0.196).
    assert worst_case_nano_usd("muse-spark-1.3-contributor") == 3_700_000
    assert worst_case_nano_usd("muse-spark-1.3") == 53_250_000
    assert worst_case_nano_usd("muse-wonder-1.0") == 196_000_000
    assert worst_case_nano_usd("careerwright-fixture-discovery-1") == 0


def test_evidence_items_are_plain_answer_texts() -> None:
    item = EvidenceItem(field=ProfileField.CURRENT_ROLE, text="Shift supervisor")

    assert item.model_dump() == {"field": "current_role", "text": "Shift supervisor"}
