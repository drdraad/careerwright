"""A selected route's saved facts and calendar retain the computed result's identity."""

import uuid
from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import cast

import pytest
from icalendar import Calendar

from careerwright.api.routes_plans import export_data
from careerwright.capability.commands import CapabilityData
from careerwright.db import Tx
from careerwright.errors import CareerwrightError
from careerwright.identity.keyring import Keyring
from careerwright.money import Money
from careerwright.planning import plans, store
from careerwright.planning.calendar import calendar_text
from careerwright.planning.comparison import AccountingPayment, Gate, ReplanAccounting, route_detail
from careerwright.planning.compiler import compile_input
from careerwright.planning.plan_records import (
    PlanActivity,
    PlanEvent,
    PlanProgress,
    PlanSearch,
    PlanSnapshot,
    PlanSource,
    ProgressUpdate,
    events_for,
)
from careerwright.planning.plans import _next_action, _progress_for_revision, _stable_step_ids
from careerwright.planning.search import search_routes
from careerwright.planning.solves import ReplanPayment, _completed_for_replan
from tests.support.planning import trace_catalogue, trace_inputs, trace_readiness


def trace_b() -> PlanSnapshot:
    monthly = compile_input(trace_inputs(), trace_catalogue(), readiness=trace_readiness())
    result = search_routes(monthly)
    index = next(
        i for i, schedule in enumerate(result.schedules) if schedule.route == ["TRACE-01/B"]
    )
    route = route_detail(result, monthly, index)
    events = events_for(route)
    return PlanSnapshot(
        plan_id=uuid.UUID("11111111-1111-4111-8111-111111111111"),
        version=1,
        workspace_id=uuid.UUID("22222222-2222-4222-8222-222222222222"),
        selected_at=datetime(2026, 11, 3, 12, tzinfo=UTC),
        selected_by=uuid.UUID("33333333-3333-4333-8333-333333333333"),
        target_title=result.target_title,
        source=PlanSource(
            solve_run_id=uuid.UUID("44444444-4444-4444-8444-444444444444"),
            solve_id="solve:0123456789abcdef",
            schedule_index=index,
            profile_version=1,
            inputs_version=1,
            capability_version=1,
            input_version=result.input_version,
            matrix_version=result.matrix_version,
            definition_version=result.definition_version,
            algorithm_version=result.algorithm_version,
            pruning_version=result.pruning_version,
        ),
        search=PlanSearch(
            coverage=result.coverage,
            stop_reason=result.stop_reason,
            instance=result.instance,
            limits=result.limits,
        ),
        route=route,
        events=events,
        next_action=events[0],
    )


def test_changed_research_warns_that_a_saved_plan_needs_a_new_solve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = trace_b()
    changed = snapshot.route.label.model_copy(update={"research_fingerprint": "new-record"})
    monkeypatch.setattr(plans, "selected_plan", lambda *_: snapshot)
    monkeypatch.setattr(
        plans,
        "current_inputs",
        lambda *_: SimpleNamespace(version=1, profile_version=1),
    )
    monkeypatch.setattr(plans, "capability_view", lambda *_: SimpleNamespace(version=1))
    monkeypatch.setattr(
        plans,
        "_current_target_versions",
        lambda *_: (snapshot.source.matrix_version, snapshot.source.definition_version, changed),
    )

    warning = plans.plan_changes(
        cast(Tx, None), snapshot.workspace_id, cast(Keyring, None), cast(CapabilityData, None)
    )
    assert warning.option_pack is True
    assert warning.new_solve_needed is True


def test_unfinished_course_payment_cannot_erase_its_outcome_from_replan() -> None:
    snapshot = trace_b()
    payment = ReplanPayment(
        variant_id="TRACE-01/B",
        due=date(2027, 5, 1),
        amount=Money(minor_units=50000, currency="GBP"),
    )
    with pytest.raises(CareerwrightError) as refused:
        _completed_for_replan(snapshot, [payment])
    assert refused.value.details["reason"] == "ongoing_step_not_modelled"
    assert refused.value.details["variant_id"] == "TRACE-01/B"
    committed = snapshot.model_copy(update={"commitments": ["TRACE-01/B"]})
    with pytest.raises(CareerwrightError) as prepaid:
        _completed_for_replan(committed, [])
    assert prepaid.value.details["reason"] == "ongoing_step_not_modelled"
    assert prepaid.value.details["variant_id"] == "TRACE-01/B"
    reported = committed.model_copy(
        update={"progress": PlanProgress(completed_steps=["TRACE-01/B"])}
    )
    assert _completed_for_replan(reported, [payment]) == ["TRACE-01/B"]
    assert _completed_for_replan(reported, []) == ["TRACE-01/B"]


def test_trace_b_snapshot_and_json_repeat_the_independent_ledger() -> None:
    snapshot = trace_b()
    saved = PlanSnapshot.model_validate_json(snapshot.model_dump_json())
    exported = export_data(saved, omit_financial_detail=False, omit_sensitive_detail=False)
    assert saved.route.basis.horizon_months == 6
    assert saved.route.schedule.months_to_readiness == 4
    direct = saved.route.costs.direct_cost
    economic = saved.route.costs.economic_cost
    peak = saved.route.costs.peak_monthly_payment
    minimum = saved.route.costs.minimum_prefunded_cash
    assert direct is not None
    assert direct.minor_units == 60000
    assert economic is not None
    assert economic.minor_units == 60000
    assert peak is not None
    assert peak.minor_units == 15000
    assert minimum is not None
    assert minimum.minor_units == 485000
    assert exported["plan_id"] == str(saved.plan_id)
    assert exported["route"]["costs"] == saved.route.costs.model_dump(mode="json")
    assert exported["route"]["schedule"]["route"] == ["TRACE-01/B"]


def test_calendar_uses_actual_all_day_dates_stable_ids_and_exclusive_ends() -> None:
    snapshot = trace_b()
    first = calendar_text(snapshot)
    assert first == calendar_text(PlanSnapshot.model_validate_json(snapshot.model_dump_json()))
    assert "DTSTART;VALUE=DATE:20270101\r\nDTEND;VALUE=DATE:20270102" in first
    assert "DTSTART;VALUE=DATE:20270430\r\nDTEND;VALUE=DATE:20270501" in first
    assert "X-WR-TIMEZONE:Europe/London" in first
    assert "SUMMARY:Synthetic demo: Proposed:" in first
    assert "DESCRIPTION:Synthetic demo data." in first
    assert "SEQUENCE:0" in first
    revised = snapshot.model_copy(update={"version": 2})
    assert "SEQUENCE:1" in calendar_text(revised)
    assert [line for line in first.splitlines() if line.startswith("UID:")] == [
        line for line in calendar_text(revised).splitlines() if line.startswith("UID:")
    ]

    live_route = snapshot.route.model_copy(
        update={
            "basis": snapshot.route.basis.model_copy(update={"synthetic": False}),
            "label": snapshot.route.label.model_copy(update={"synthetic": False}),
        }
    )
    assert "Synthetic demo" not in calendar_text(snapshot.model_copy(update={"route": live_route}))


def test_next_action_moves_past_expired_dates_without_rewriting_the_saved_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = trace_b()
    monkeypatch.setattr(plans, "visible_workspace", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(store, "plan", lambda *_args, **_kwargs: snapshot)
    tx = cast(Tx, object())
    before = plans.selected_plan(
        tx, snapshot.workspace_id, now=datetime(2027, 1, 1, 12, tzinfo=UTC)
    )
    after = plans.selected_plan(tx, snapshot.workspace_id, now=datetime(2027, 1, 2, 12, tzinfo=UTC))
    assert before.next_action is not None
    assert before.next_action.on == date(2027, 1, 1)
    assert after.next_action is not None
    assert after.next_action.on > date(2027, 1, 1)
    assert snapshot.next_action == snapshot.events[0]
    assert before.version == after.version == snapshot.version


def test_review_date_becomes_next_action_and_a_calendar_event() -> None:
    snapshot = trace_b()
    progress = PlanProgress(completed_steps=["TRACE-01/B"], review_on=date(2027, 2, 1))
    action = _next_action(snapshot.events, progress, datetime(2027, 1, 2, 12, tzinfo=UTC))
    assert action is not None
    assert action.kind == "review"
    assert action.on == date(2027, 2, 1)
    assert _next_action(snapshot.events, progress, datetime(2027, 2, 2, 12, tzinfo=UTC)) is None
    with_review = snapshot.model_copy(update={"progress": progress})
    exported = Calendar.from_ical(calendar_text(with_review))
    events = exported.walk("VEVENT")
    assert len(events) == 1
    review = next(
        event for event in events if str(event["SUMMARY"]) == "Synthetic demo: Review this plan"
    )
    assert review.decoded("DTSTART") == date(2027, 2, 1)
    assert review.decoded("DTEND") == date(2027, 2, 2)
    assert "no external calendar has changed" in str(review["DESCRIPTION"])
    assert "Synthetic demo data." in str(review["DESCRIPTION"])
    revised = Calendar.from_ical(calendar_text(with_review.model_copy(update={"version": 2})))
    revised_review = next(
        event
        for event in revised.walk("VEVENT")
        if str(event["SUMMARY"]) == "Synthetic demo: Review this plan"
    )
    assert str(review["UID"]) == str(revised_review["UID"])
    assert int(str(revised_review["SEQUENCE"])) == 1


def test_conditional_events_and_dst_dates_are_proposed_without_a_time_shift() -> None:
    snapshot = trace_b()
    gated = snapshot.route.model_copy(
        update={
            "gates": [
                Gate(
                    kind="application",
                    variant_id="TRACE-01/B",
                    instrument_id=None,
                    verification="confirm_application",
                    month="2027-01",
                )
            ]
        }
    )
    assert all(event.conditional for event in events_for(gated))
    events = [
        PlanEvent(
            key=f"test:{on}",
            kind="start",
            variant_id="test",
            title="Course, phase; 1",
            on=on,
            conditional=True,
        )
        for on in (date(2027, 3, 28), date(2027, 10, 31))
    ]
    calendar = calendar_text(snapshot.model_copy(update={"events": events}))
    assert "DTSTART;VALUE=DATE:20270328\r\nDTEND;VALUE=DATE:20270329" in calendar
    assert "DTSTART;VALUE=DATE:20271031\r\nDTEND;VALUE=DATE:20271101" in calendar
    synthetic_summary = r"SUMMARY:Synthetic demo: Proposed\, conditional: Course\, phase\; 1"
    assert calendar.count(synthetic_summary) == 2
    assert "\nDTSTART:" not in calendar  # no invented timed or UTC appointment


def test_independent_icalendar_parser_reads_conditional_dst_and_all_day_identity() -> None:
    snapshot = trace_b()
    dates = (date(2027, 3, 28), date(2027, 10, 31))
    events = [
        PlanEvent(
            key=f"dst:{on}",
            kind="start",
            variant_id="dst",
            title="Course, phase; 1",
            on=on,
            conditional=True,
        )
        for on in dates
    ]
    first = Calendar.from_ical(calendar_text(snapshot.model_copy(update={"events": events})))
    revised = Calendar.from_ical(
        calendar_text(snapshot.model_copy(update={"version": 2, "events": events}))
    )
    before = first.walk("VEVENT")
    after = revised.walk("VEVENT")
    assert len(before) == len(after) == 2
    assert [event.decoded("DTSTART") for event in before] == list(dates)
    assert [event.decoded("DTEND") for event in before] == [date(2027, 3, 29), date(2027, 11, 1)]
    assert all(type(event.decoded("DTSTART")) is date for event in before)
    assert [str(event["UID"]) for event in before] == [str(event["UID"]) for event in after]
    assert [int(str(event["SEQUENCE"])) for event in before] == [0, 0]
    assert [int(str(event["SEQUENCE"])) for event in after] == [1, 1]
    assert all("Proposed, conditional" in str(event["SUMMARY"]) for event in before)


def test_omission_removes_financial_figures_and_supplied_details_from_derivative() -> None:
    snapshot = trace_b()
    redacted = export_data(snapshot, omit_financial_detail=True, omit_sensitive_detail=True)
    text = str(redacted)
    assert "60000" not in text
    assert "15000" not in text
    assert "485000" not in text
    assert "costs" not in redacted["route"]
    assert "selected_by" not in redacted
    assert "supplied" not in redacted["route"]["steps"][0]
    direct = snapshot.route.costs.direct_cost
    assert direct is not None
    assert direct.minor_units == 60000


def test_sensitive_omission_removes_own_option_words_and_ids_everywhere() -> None:
    snapshot = trace_b()
    own_id = "own:private-slug"
    former_id = "own:former-private-slug"
    replan_only_id = "own:earlier-private-slug"
    [step] = snapshot.route.steps
    own_step = step.model_copy(
        update={
            "variant_id": own_id,
            "concept_id": own_id,
            "offering_id": own_id,
            "title": "Private course title",
            "provider": "Private provider",
            "prerequisites": ["Private prerequisite"],
            "added_by_person": True,
        }
    )
    route = snapshot.route.model_copy(
        update={
            "steps": [own_step],
            "schedule": snapshot.route.schedule.model_copy(update={"route": [own_id]}),
            "basis": snapshot.route.basis.model_copy(
                update={
                    "replan": ReplanAccounting(
                        from_plan_version=1,
                        completed_variants=[former_id],
                        excluded_variants=[former_id, replan_only_id],
                        sunk_paid=Money(minor_units=0, currency="GBP"),
                        remaining_payments=[
                            AccountingPayment(
                                variant_id=former_id,
                                due=date(2027, 2, 1),
                                amount=Money(minor_units=0, currency="GBP"),
                            )
                        ],
                    )
                }
            ),
        }
    )
    events = [
        event.model_copy(
            update={"key": f"{own_id}:{event.kind}", "variant_id": own_id, "title": own_step.title}
        )
        for event in snapshot.events
    ]
    snapshot = snapshot.model_copy(
        update={
            "route": route,
            "events": events,
            "next_action": events[0],
            "progress": PlanProgress(
                completed_steps=[own_id],
                activity=[
                    PlanActivity(
                        kind="step_completed",
                        variant_id=former_id,
                        until=None,
                        recorded_at=datetime(2026, 12, 1, tzinfo=UTC),
                        step_title="Former private course",
                    ),
                    PlanActivity(
                        kind="step_completed",
                        variant_id=own_id,
                        until=None,
                        recorded_at=datetime(2027, 1, 1, tzinfo=UTC),
                        step_title="Private course title",
                    ),
                ],
            ),
        }
    )
    full = export_data(snapshot, omit_financial_detail=False, omit_sensitive_detail=False)
    assert "Private course title" in str(full)
    assert former_id in str(full)
    assert replan_only_id in str(full)
    assert "Former private course" in str(full)
    for omit_financial in (False, True):
        redacted = export_data(
            snapshot, omit_financial_detail=omit_financial, omit_sensitive_detail=True
        )
        text = str(redacted)
        for private in (
            own_id,
            "Private course title",
            "Private provider",
            "Private prerequisite",
            former_id,
            replan_only_id,
            "Former private course",
        ):
            assert private not in text
        assert redacted["route"]["steps"][0]["title"] == "Your option"
        assert redacted["events"][0]["title"] == "Your option"
        assert redacted["next_action"]["title"] == "Your option"
        assert [activity["step_title"] for activity in redacted["progress"]["activity"]] == [
            "Your option",
            "Your option",
        ]
        assert redacted["route"]["schedule"]["route"] == ["redacted-option-1"]


def test_reported_progress_removes_calendar_proposals_without_awarding_evidence() -> None:
    snapshot = trace_b()
    finished = snapshot.model_copy(
        update={
            "version": 2,
            "progress": PlanProgress(completed_steps=["TRACE-01/B"]),
            "next_action": None,
        }
    )
    assert finished.route == snapshot.route
    assert finished.source == snapshot.source
    assert finished.progress.completed_steps == ["TRACE-01/B"]
    assert "BEGIN:VEVENT" not in calendar_text(finished)
    assert snapshot.route.schedule.qualifications == finished.route.schedule.qualifications


def test_revised_step_keeps_completion_report_but_never_marks_changed_work_complete() -> None:
    snapshot = trace_b()
    activity = PlanActivity(
        kind="step_completed",
        variant_id="TRACE-01/B",
        until=None,
        recorded_at=datetime(2027, 5, 2, tzinfo=UTC),
    )
    previous = snapshot.model_copy(
        update={
            "progress": PlanProgress(completed_steps=["TRACE-01/B"], activity=[activity]),
            "commitments": ["TRACE-01/B"],
        }
    )
    [step] = snapshot.route.steps
    changed = snapshot.route.model_copy(
        update={"steps": [step.model_copy(update={"finish_date": date(2027, 5, 1)})]}
    )
    assert _progress_for_revision(previous, snapshot.route).completed_steps == ["TRACE-01/B"]
    assert _stable_step_ids(previous, snapshot.route) == {"TRACE-01/B"}
    revised = _progress_for_revision(previous, changed)
    assert revised.completed_steps == []
    assert revised.activity == [activity]
    assert _stable_step_ids(previous, changed) == set()
    removed = _progress_for_revision(previous, snapshot.route.model_copy(update={"steps": []}))
    assert removed.completed_steps == []
    assert removed.activity == [activity]
    assert _stable_step_ids(previous, snapshot.route.model_copy(update={"steps": []})) == set()


def test_progress_requests_require_the_fields_for_their_kind() -> None:
    from pydantic import ValidationError

    for body in (
        {"expected_version": 1, "kind": "step_completed"},
        {"expected_version": 1, "kind": "rest"},
        {"expected_version": 1, "kind": "resume", "variant_id": "TRACE-01/B"},
    ):
        try:
            ProgressUpdate.model_validate(body)
        except ValidationError:
            pass
        else:
            raise AssertionError(f"accepted malformed progress: {body}")


@pytest.mark.parametrize("stage", ["first", "removed_original", "later"])
def test_replan_excludes_every_variant_of_a_completed_course(stage: str) -> None:
    from careerwright.planning.solves import _excluded_for_replan

    snapshot = trace_b()
    catalogue = trace_catalogue()
    original = next(v for v in catalogue.variants if v.variant_id == "TRACE-01/B")
    offering = next(o for o in catalogue.offerings if o.offering_id == original.offering_id)
    alternative_offering = offering.model_copy(
        update={"offering_id": "TRACE-01/B-part-time-offering"}
    )
    alternative = original.model_copy(
        update={
            "variant_id": "TRACE-01/B-alternative",
            "offering_id": alternative_offering.offering_id,
        }
    )
    catalogue = catalogue.model_copy(
        update={
            "offerings": [*catalogue.offerings, alternative_offering],
            "variants": [
                v
                for v in [*catalogue.variants, alternative]
                if stage != "removed_original" or v.variant_id != original.variant_id
            ],
        }
    )
    if stage == "later":
        snapshot = snapshot.model_copy(
            update={
                "route": snapshot.route.model_copy(
                    update={
                        "steps": [],
                        "basis": snapshot.route.basis.model_copy(
                            update={
                                "replan": ReplanAccounting(
                                    from_plan_version=1,
                                    completed_variants=[original.variant_id],
                                    excluded_variants=[original.variant_id, "retired-variant"],
                                    sunk_paid=Money(minor_units=0, currency="GBP"),
                                    remaining_payments=[],
                                )
                            }
                        ),
                    }
                )
            }
        )
    else:
        snapshot = snapshot.model_copy(
            update={"progress": PlanProgress(completed_steps=[original.variant_id])}
        )
    completed = _completed_for_replan(snapshot, [])
    excluded = _excluded_for_replan(snapshot, completed, catalogue)
    assert {original.variant_id, alternative.variant_id} <= set(excluded)
    if stage == "later":
        assert "retired-variant" in excluded
    readiness = trace_readiness()
    readiness = readiness.model_copy(
        update={
            "outcomes": [
                *readiness.outcomes,
                *[
                    outcome.model_copy(
                        update={
                            "outcome_id": f"{outcome.outcome_id}:alternative",
                            "offering_id": alternative_offering.offering_id,
                        }
                    )
                    for outcome in readiness.outcomes
                    if outcome.offering_id == original.offering_id
                ],
            ]
        }
    )
    before = search_routes(compile_input(trace_inputs(), catalogue, readiness=readiness))
    assert any(alternative.variant_id in schedule.route for schedule in before.schedules)
    remaining = catalogue.model_copy(
        update={"variants": [v for v in catalogue.variants if v.variant_id not in excluded]}
    )
    after = search_routes(compile_input(trace_inputs(), remaining, readiness=readiness))
    assert after.schedules
    assert not any(
        {original.variant_id, alternative.variant_id}.intersection(schedule.route)
        for schedule in after.schedules
    )
