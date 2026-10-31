"""The live evaluation's caps refuse before any call (ruling R5; MODEL-09). Offline: nothing
here contacts Meta."""

from pathlib import Path

import pytest

from careerwright.identity.model_choice import ModelChoice
from tools.evaluation import CaseKind, load_cases
from tools.live_eval import (
    MAX_LIVE_CASES,
    SCOPE_MAX_CALLS,
    SCOPE_MAX_COST_NANO_USD,
    WONDER_MAX_COST_NANO_USD,
    Plan,
    authorise_eval,
    select,
    write_results,
)
from tools.live_smoke import WONDER_BUDGET, CapExceededError, ScopeBudget
from tools.localenv import check_permissions
from tools.usage_ledger import ScopeSpend

MODELS = ModelChoice.configure("muse-spark-1.3-contributor", "muse-spark-1.3", "test")
ROOMY = ScopeBudget("live-eval", max_calls=99, max_production_calls=0, max_cost_nano_usd=10**12)
NOTHING_SPENT = ScopeSpend(0, 0, 0)


@pytest.mark.req("MODEL-09", "TEST1-10")
def test_the_default_live_run_is_four_representative_cases_on_the_test_model() -> None:
    cases = select(load_cases(), None)

    plan = authorise_eval(MODELS, cases, budget=ROOMY, spent=NOTHING_SPENT)

    assert [case.id for case in cases] == ["INT-01", "INT-02", "INT-03", "DSC-01"]
    assert len(cases) <= MAX_LIVE_CASES == 6
    assert {case.kind for case in cases} == {CaseKind.INTERVIEW, CaseKind.DISCOVERY}
    assert plan.model_id == "muse-spark-1.3-contributor"  # never the production model
    assert plan.calls == 8  # one attempt each, at most one validation repair
    # Three interview attempts at $0.0035 and one discovery at $0.003 (their reservations).
    assert plan.worst_case_nano_usd == 3 * 3_500_000 + 3_000_000


@pytest.mark.req("MODEL-09")
def test_a_scope_holds_one_default_run_within_the_controller_s_nine_requests() -> None:
    # Task 6 review A-M10: the per-scope request cap is the controller's 9 (R5).
    cases = select(load_cases(), None)
    default = ScopeBudget("live-eval", SCOPE_MAX_CALLS, 0, SCOPE_MAX_COST_NANO_USD)

    plan = authorise_eval(MODELS, cases, budget=default, spent=NOTHING_SPENT)

    assert SCOPE_MAX_CALLS == 9
    with pytest.raises(CapExceededError, match="calls used"):
        authorise_eval(MODELS, cases, budget=default, spent=ScopeSpend(plan.calls, 0, 0))


@pytest.mark.req("MODEL-09")
def test_more_cases_a_used_up_scope_or_a_non_model_case_are_refused() -> None:
    cases = load_cases()
    live = select(cases, None)
    with pytest.raises(CapExceededError, match="1-6 live cases"):
        authorise_eval(MODELS, [*live, *live[:3]], budget=ROOMY, spent=NOTHING_SPENT)
    with pytest.raises(CapExceededError, match="calls used"):
        authorise_eval(MODELS, live, budget=ROOMY, spent=ScopeSpend(95, 0, 0))
    tight = ScopeBudget("live-eval", 99, 0, max_cost_nano_usd=10_000_000)
    with pytest.raises(CapExceededError, match="committed"):
        authorise_eval(MODELS, live, budget=tight, spent=NOTHING_SPENT)
    with pytest.raises(CapExceededError, match="only interview, discovery and explanation"):
        select(cases, ["SUP-01"])
    with pytest.raises(CapExceededError, match="no such cases"):
        select(cases, ["NOPE-1"])


@pytest.mark.req("MODEL-09", "REC1-11")
def test_the_explanation_case_runs_only_when_named_within_the_controller_s_cap() -> None:
    # Task 6b: a discovery then its slate's explanation, two runs of one attempt each.
    cases = select(load_cases(), ["EXP-01"])
    cap = ScopeBudget("live-eval-6b", SCOPE_MAX_CALLS, 0, 300_000_000)

    plan = authorise_eval(MODELS, cases, budget=cap, spent=NOTHING_SPENT)

    assert "EXP-01" not in [case.id for case in select(load_cases(), None)]
    assert plan.calls == 4  # two runs, each the call and at most one repair
    # Each run reserved at the larger worst case: the explanation's $0.0034.
    assert plan.worst_case_nano_usd == 2 * 3_400_000
    with pytest.raises(CapExceededError, match="calls used"):
        authorise_eval(MODELS, cases, budget=cap, spent=ScopeSpend(6, 0, 0))


@pytest.mark.req("MODEL-11", "TEST1-10")
def test_wonder_cases_run_on_the_production_model_within_their_own_caps() -> None:
    wonder = ModelChoice.configure("muse-spark-1.3-contributor", "muse-wonder-1.0", "production")
    two = select(load_cases(), ["INT-01", "DSC-01"])

    plan = authorise_eval(wonder, two, budget=WONDER_BUDGET, spent=NOTHING_SPENT, production=True)

    assert (plan.model_id, plan.production, plan.calls) == ("muse-wonder-1.0", True, 4)
    # An interview attempt ($0.176 on Wonder: two requests) and a discovery ($0.156).
    assert plan.worst_case_nano_usd == 176_000_000 + 156_000_000 <= WONDER_MAX_COST_NANO_USD
    four = select(load_cases(), None)
    with pytest.raises(CapExceededError, match="exceeds the cap"):
        authorise_eval(wonder, four, budget=WONDER_BUDGET, spent=NOTHING_SPENT, production=True)
    with pytest.raises(CapExceededError, match="committed"):  # $0.50 in all, the pair included
        authorise_eval(
            wonder, two, budget=WONDER_BUDGET, spent=ScopeSpend(2, 2, 200_000_000), production=True
        )
    with pytest.raises(CapExceededError, match="production calls used"):
        authorise_eval(
            wonder, two, budget=WONDER_BUDGET, spent=ScopeSpend(2, 12, 0), production=True
        )
    # Without the flag the same configuration runs the test model, as before.
    assert authorise_eval(wonder, two, budget=ROOMY, spent=NOTHING_SPENT).model_id == (
        "muse-spark-1.3-contributor"
    )


@pytest.mark.req("MODEL-09")
def test_a_test_model_that_is_the_production_model_is_refused() -> None:
    same = ModelChoice.configure("muse-spark-1.3", "muse-spark-1.3", "test")

    with pytest.raises(CapExceededError, match="production model"):
        authorise_eval(same, select(load_cases(), None), budget=ROOMY, spent=NOTHING_SPENT)


@pytest.mark.req("MODEL-09")
def test_the_private_observations_file_is_owner_only_so_setup_still_starts(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir(mode=0o700)
    observations = home / "evidence" / "live-eval.jsonl"
    plan = Plan("muse-spark-1.3-contributor", [], calls=0, worst_case_nano_usd=0)

    write_results(tmp_path / "results.md", observations, plan, [], {}, [], "live-eval")

    assert observations.stat().st_mode & 0o777 == 0o600
    check_permissions(home)  # `make setup` and `make demo` refuse a file others can read
