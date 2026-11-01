# Task 7 slice 7B — re-review 1-A (fix round 1, items 1–9)

Scope: my findings I1 and M1–M8, as ruled in `task-7-sliceB-fix-round-1.md` items 1–9.

What I read:
- the implementer's "Fix round 1" section, treated as unverified claims;
- `review-04f95cf..044ef12.diff`, mainly `d1efff5` and `726686b`;
- the parts of `ca4cbea` and `044ef12` that touch my files.

HEAD is `044ef12`, and the working tree is clean.

Checks I ran (read-only, with `.venv/bin/python`, no bytecode written; I did not re-run `make
check` or `make acceptance`):
- **The I1 probes again**, through the real readers (`salary_from`, `pages._salary`) and
  `job_against_floor`, against a £26,000 a year floor.
- **The occupation rule, old against new.** I compared 04f95cf's `modelled_floor_verdict`
  with 044ef12's over a grid of 43,095 cases. The grid covered:
  - four floor periods and three floor amounts;
  - one to three regions;
  - P90 values of None, 1, £25,000, £25,999.99, £26,000, £26,000.01 and £90,000, in three
    ASHE periods;
  - region subsets, including none;
  - every `ModelledPayUnavailable`.

  There were 0 mismatches.
- **Per-statistic reliability** on the real pinned ASHE file.

## Verdicts

| # | Item | Verdict | Where |
|---|---|---|---|
| 1 | A-I1: open-ended pay is never below the floor | **Fixed** | `backend/src/nessa/catalogue/pay.py:281-310` (`_against`, `floor_verdict`), `backend/src/nessa/evidence/jobs.py:325-326`, `backend/src/nessa/evidence/extraction.py:335-337` |
| 2 | A-M6: modelled pay compared with the floor directly | **Fixed** | `backend/src/nessa/catalogue/pay.py:344`; test `backend/tests/domain/test_pay.py:197` |
| 3 | A-M5: `basis_unknown` | **Fixed** | `backend/src/nessa/catalogue/pay.py:251,317-318` |
| 4 | A-M4: each statistic keeps its own CV and band | **Fixed** | `backend/src/nessa/catalogue/ashe.py:174,253-260,281`; `pay.py:179-185`; `api/reference_schemas.py:86-87,121-122`; migration `r0028_ashe_statistic_cvs.py` |
| 5 | A-M3: pending before `all_below_salary_floor` | **Fixed** | `backend/src/nessa/evidence/acquisition.py:649-652` |
| 6 | A-M1: the hint says what L0 does | **Fixed** | `apps/web/src/lib/vocabulary.ts:177` |
| 7 | A-M7: the sentence gives `meets` | **Fixed** | `backend/src/nessa/api/discovery_schemas.py:352-356`; `backend/tests/api/test_floor_words.py` |
| 8 | A-M8: Storybook state with a floor | **Fixed** | `apps/web/src/stories/Conversation.stories.tsx:420` (`SlateWithSalaryFloor`) |
| 9 | A-M2: stale text | **Fixed** | `docs/requirements-register.md:130` (DIV1-06); `docs/adr/0007-conversation-discovery-and-support.md:64-67` (amendment note, history kept); `backend/tools/setup.py:1-3` |

### Evidence per item

**1. A-I1.** At 044ef12, against a £26,000 a year floor:
- `salary_from("From £24,000 per annum")`: (2,400,000, None, year), `unknown/no_upper_amount`.
- `salary_from("Minimum £24,000 a year")`: (2,400,000, None, year), `unknown/no_upper_amount`.
- `salary_from("£24,000+ per annum")`: (2,400,000, None, year), `unknown/no_upper_amount`.
  `£24k+ a year` reads the same.
- `pages._salary` with `minValue: 24000` alone: (2,400,000, None), `unknown/no_upper_amount`.

Controls, all correct:
- `From £27,000`: meets.
- `Up to £24,000`, a JSON-LD `maxValue` alone, a single `value: 24000`, `£24,000 per annum`
  and `£20,000 - £24,000`: below.
- One copy below and one open above: `no_upper_amount`. One copy below and one open but
  already meeting the floor: meets.
- `£24,000 + benefits per annum` (spaced `+`) still reads as a single base amount and is
  below. That is the right reading of base pay, and a deliberate R11 boundary (only the
  attached form was reproduced).

The test row that locked in the old reading is corrected (`pay(2_500_000, 2_500_000)` is the
single amount; `pay(2_500_000, None)` is `no_upper_amount`). The four reader cases are in
`test_jobs.py:356` (`test_open_ended_pay_as_the_readers_give_it_is_never_below_the_floor`),
built from the real readers, not hand-made `Salary` values.

**2. A-M6 (does the occupation rule still behave the same?).** Yes:
- `modelled_floor_verdict` no longer builds a `StatedPay`.
- My old-against-new comparison found 0 mismatches in 43,095 cases. Item 1's change to the
  advertised-pay rule did not reach the occupation rule.
- `test_the_occupation_rule_compares_ashe_s_90th_percentile_with_the_floor_itself` holds the
  boundary: £25,999.99 is below, £26,000 meets.

**3. A-M5.** Adzuna-shaped pay with `PayBasis.UNKNOWN` now gives `basis_unknown`, and no pay
at all still gives `no_pay` (probe).

**4. A-M4.**
- CVs are read for every statistic in `_COLUMNS`.
- The store keeps them as decimal text (no float).
- `reliability(statistic)` uses the statistic's own CV, and a withheld `x` is unreliable.
- The API shows `cv` and `reliability` on each `PayStatisticOut`.
- The transformation is bumped to `nessa-ashe-import-2`, and migration 0028 empties the held
  import so it re-imports.
- My probe on the real file: the median's bands are spread across all five (943 precise,
  2,169 reasonably precise, 1,979 acceptable, 7,546 unreliable, 959 unknown), and each
  statistic gets its own. See N1 for what the same probe showed about P90.

**5. A-M3.** Pending is checked first. The integration test holds a slow source pending
while the only recorded job is below the floor.

**6. A-M1.** The hint now reads: "vacancies whose advertised pay in that period is below it,
and suggestions whose reviewed official pay is, are left out; Nessa says how many, and why
the rest were kept." It is true of L0. N1 bears on what "reviewed official pay" can ever do.

**7. A-M7.** The sentence now gives `0 meet it`. The test asserts every count and that they
add up to 10.

**8. A-M8.** The story is present. The Playwright story run with axe covering it is claimed,
and I did not verify it.

**9. A-M2.** All three texts are corrected as ruled.

## Regressions or new issues

No regression in items 1–9.

### Critical

None.

### Important

**N1. The occupation floor can never leave anything out with the pinned ASHE release.**
This is pre-existing, not from this round. I found it by probe while verifying item 4, and I
missed it in review A.
- **Where:**
  - `backend/src/nessa/catalogue/pay.py:39` (`FLOOR_STATISTIC = "p90"`);
  - `docs/adr/0010-reference-data-and-ai-evidence.md:4-5,140-145` (decision 8, and the status
    line asking for product-owner confirmation);
  - `docs/requirements-register.md:131` (DIV1-07);
  - `backend/tests/support/reference_data.py:104-110` (the synthetic sample).
- **What:** the pinned 2026 provisional Table 15 (4) publishes no percentile at all.
  - The product's own parser finds 0 of 13,596 estimates with a published P90, or any other
    percentile, in any period.
  - Raw cells confirm it: every 4-digit row in the Full-Time sheets of 15.1a, 15.5a and 15.7a
    has `x` (or blank) in all ten percentile columns, 45,320 cells per table.
  - Only the median (5,091) and the mean are ever published.
  - Table 15 (3), the 3-digit minor groups, does publish percentiles: 5,078 to 6,287 cells
    per table.
- **Consequence:** the occupation rule ("below only when P90 is below the floor in every
  region") answers `not_published` for every occupation, even after H-10 reviews a mapping.
  The slate floor is therefore structurally inert, not merely inert until a reviewer exists.
- **Runtime stays honest:** in L0 the sentence says "kept because no reviewed UK occupation
  code links them to pay data". After a review it would say "kept because the official
  figure is not published for your regions".
- **But the records do not say this:**
  - ADR 0010 decision 8 presents P90 as a working, conservative rule, and asks the product
    owner to confirm it under R6.
  - The implementer's ruling 6 says the figure is "often 'not published'". It is always
    unpublished.
  - The synthetic sample publishes P90s (for example "52000", CV 14.2) that the real file
    never has, although its docstring says the layouts "copy the real files". So
    `test_discovery.py`'s floor test and the round's new P90 CV assertions exercise a data
    shape the product cannot meet.
- **Why it matters:** "the salary floor applied once pay data exists" (carry-forward H-11
  item 4) cannot happen for suggestions with this release and this statistic. The product
  owner would be confirming decision 8 without knowing that. This is a reproduced defect
  (a probe on the pinned file), not hardening, so R12 does not defer it.
- **Fix:**
  1. Record the fact in ADR 0010 decisions 4 and 8, the DIV1-07 row and the R6 list: no
     percentile at region × unit group in this release; Table 15 (3) has them. Put the
     choice of statistic or geography to the product owner (R6).
  2. Do not change the rule without that decision. The median or mean would remove careers
     where many jobs pay more (DIV1-07). A minor-group figure would be a broad-SOC estimate,
     which spec section 5 lets in only with an explicit label.
  3. Pin the fact in the full-release test, as the count of published percentiles in Table 15
     (4), so it cannot drift silently.
  4. Make the sample's 4-digit percentiles withheld like the real file. Keep a published P90
     only as a labelled synthetic exception for the mechanism test.

### Minor

**N2. Migration 0028 drops the database check on CVs.**
- Where: `backend/src/nessa/migrations/versions/r0028_ashe_statistic_cvs.py:26-27`.
- What: dropping `median_cv` also drops its `CHECK (median_cv >= 0)`, and the new
  `cvs jsonb NOT NULL` column has no check (for example, `jsonb_typeof(cvs) = 'object'`).
  Nothing in the database now refuses a negative or non-numeric CV. The parser accepts a
  leading `-`, and `reliability()` would band a negative CV as "precise".
- No failing check or reproduced defect requires this, and the pinned file has none. Under
  R12 it goes to the final-review list, not this task.

## Assessment

**Items 1–9:** 9 fixed, 0 partly fixed, 0 not fixed.

**New issues:** Critical 0, Important 1 (N1, pre-existing, found while verifying item 4),
Minor 1 (N2, R12 final-review list).

**Reasoning:** Every finding of mine is fixed as ruled, and the probes confirm it. The
occupation rule is provably unchanged. But the real pinned ASHE release publishes no
percentile at the unit-group level, so the floor's occupation rule can never act. ADR 0010,
the register and the synthetic sample do not say so, and the product owner is asked to
confirm the rule without that fact.
