"""The live evaluation's caps refuse before any call (ruling R5; MODEL-09). Offline: nothing
here contacts Meta."""

import pytest

from nessa.identity.model_choice import ModelChoice
from tools.evaluation import CaseKind, load_cases
from tools.live_eval import MAX_LIVE_CASES, authorise_eval, select
from tools.live_smoke import CapExceededError, ScopeBudget
from tools.usage_ledger import ScopeSpend

MODELS = ModelChoice.configure("muse-spark-1.3-contributor", "muse-spark-1.3", "test")
ROOMY = ScopeBudget("live-eval", max_calls=99, max_production_calls=0, max_cost_nano_usd=10**12)
NOTHING_SPENT = ScopeSpend(0, 0, 0)


@pytest.mark.req("MODEL-09", "TEST1-10")
def test_the_default_live_run_is_six_representative_cases_on_the_test_model() -> None:
    cases = select(load_cases(), None)

    plan = authorise_eval(MODELS, cases, budget=ROOMY, spent=NOTHING_SPENT)

    assert len(cases) == MAX_LIVE_CASES == 6
    assert {case.kind for case in cases} == {CaseKind.INTERVIEW, CaseKind.DISCOVERY}
    assert plan.model_id == "muse-spark-1.3-contributor"  # never the production model
    assert plan.calls == 12  # one attempt each, at most one validation repair
    # Five interview attempts at $0.0035 and one discovery at $0.003 (their reservations).
    assert plan.worst_case_nano_usd == 5 * 3_500_000 + 3_000_000


@pytest.mark.req("MODEL-09")
def test_more_cases_a_used_up_scope_or_a_non_model_case_are_refused() -> None:
    cases = load_cases()
    live = select(cases, None)
    with pytest.raises(CapExceededError, match="1-6 live cases"):
        authorise_eval(MODELS, [*live, live[0]], budget=ROOMY, spent=NOTHING_SPENT)
    with pytest.raises(CapExceededError, match="calls used"):
        authorise_eval(MODELS, live, budget=ROOMY, spent=ScopeSpend(90, 0, 0))
    tight = ScopeBudget("live-eval", 99, 0, max_cost_nano_usd=20_000_000)
    with pytest.raises(CapExceededError, match="committed"):
        authorise_eval(MODELS, live, budget=tight, spent=NOTHING_SPENT)
    with pytest.raises(CapExceededError, match="only interview and discovery"):
        select(cases, ["SUP-01"])
    with pytest.raises(CapExceededError, match="no such cases"):
        select(cases, ["NOPE-1"])


@pytest.mark.req("MODEL-09")
def test_a_test_model_that_is_the_production_model_is_refused() -> None:
    same = ModelChoice.configure("muse-spark-1.3", "muse-spark-1.3", "test")

    with pytest.raises(CapExceededError, match="production model"):
        authorise_eval(same, select(load_cases(), None), budget=ROOMY, spent=NOTHING_SPENT)
