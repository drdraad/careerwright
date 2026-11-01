# Task 7 slice 7B: proposed CLAUDE.md wording (consolidated by the controller)

## 1. Commands: in the `make setup` bullet

Replace "the pinned ESCO release fetched into the gitignored `var/datasets/` and
hash-checked" with:

> the pinned ESCO release and reference datasets (ONS ASHE and the SOC 2020 coding index,
> the ILO and Anthropic AI evidence, the ESCO to O*NET crosswalk) fetched into the
> gitignored `var/datasets/` and hash-checked

## 2. Layout: replace `nessa/catalogue`'s description

> `nessa/catalogue` (the ESCO taxonomy, the English city list, the pinned reference data,
> the UK SOC mapping, modelled pay and the salary floor, and the AI Resilience record model
> with its packs in `catalogue/packs/`, ADR 0010)

## 3. Invariants: a new bullet after the Evidence bullet

> Pay and AI evidence (ADR 0010): ASHE is regional, never a city's; modelled pay exists only
> through an accountable reviewer's UK SOC mapping (none in L0). The salary floor leaves out
> only pay whose stated top, in its own period, is below it, never unknown, predicted,
> open-ended or other-period pay, and says what it left out. The AI Resilience Score is a
> reviewed range or unscored, never computed; exposure evidence alone never publishes one,
> and a model's proposal never publishes.

## 4. Invariants, the Evidence bullet: correct its last sentence (Task 7d review)

Replace "Lock order: a run's cancellation lock first, then `lock_workspace_records`, then
rows." with:

> Lock order (ADR 0009 decision 15): a run's cancellation lock first (the cancel; a
> model-readable recording, before `lock_workspace_records`). Only the worker locks a run's
> row `FOR UPDATE`, and only as its transaction's first lock; a cancel records its requests
> (key shares on the runs' rows) before it locks the workspace's row.
