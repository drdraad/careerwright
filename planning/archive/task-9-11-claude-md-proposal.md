# CLAUDE.md proposal from Tasks 9 and 11 (not applied; needs the user's yes)

Three changes. Each quotes the exact wording to add. They follow the Task 7 slice B and Task
7b proposals, and apply after them.

## 1. "Repository facts", Layout: after the `nessa/catalogue` entry, add

> `nessa/capability` (capability assessment: the pinned capability reference with rubrics,
> ESCO crosswalks and gate types; matrices, evidence, protected gates, OUT-1 outcomes,
> readiness, gaps and the question graph; `capability.store` is its only SQL), `nessa/planning`
> (the monthly planning model, pure: the planning catalogue and its pack adapter, the
> immutable monthly input, the direct-spend, income-difference, liquidity and debt ledgers,
> and the route checker),

## 2. "Commands": after the option pack's tool, add

> `uv run --locked python -m tools.session_2_files` (from `backend/`) rewrites session 2's T
> and R question sets.

## 3. "Non-obvious invariants": two new bullets

> - Capability (ADR 0012): a protected gate (legal practice, recognition, admission,
>   eligibility) is always required and never demoted (`PROTECTED_GATE`); held but unverified
>   is unresolved, and nothing finds a person ineligible. A level counts only against the
>   rubric it was chosen for; unknown is never level 0; ordinal levels take the maximum, never
>   a sum. A target with nothing modelled, or with eligibility alone, is
>   `insufficient_coverage`, never ready. A planned outcome counts only in a conditional
>   scenario and never changes current evidence. Every L0 readiness result is qualified, and
>   every derived result carries its `matrix_version` and `definition_version`.
> - Planning (ADR 0013): the checker lists every violation, each limit named apart
>   (direct-spend cap, monthly payment cap, reserve, deficit cap; an economic-cost cap is only
>   a preference), and a violation is "not feasible in this monthly model", never "cannot
>   afford". Unknown dates, cost, timetable or a hard limit leave a route unresolved, never
>   passed. Every readiness qualification qualifies the route. Only an approved award counts
>   unconditionally; a loan is never support. Readiness milestones come from
>   `nessa.capability.readiness.assess`, never from planning code, and Task 13a's oracle shares
>   no code with `nessa.planning.checker`.
