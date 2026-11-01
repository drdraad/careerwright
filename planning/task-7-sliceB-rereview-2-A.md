# Task 7 slice 7B — re-review 2-A (fix round 2, item 1: re-review 1-A N1)

Scope: N1 only, as ruled in `task-7-sliceB-fix-round-2.md` item 1.

What I read:
- the implementer's "Fix round 2" section, treated as unverified claims;
- `review-044ef12..84dc858.diff`, one commit touching five files: three test files, ADR 0010
  and the register. No product code changed.

HEAD is `84dc858`, and the working tree is clean.

Checks I ran (read-only, with `.venv/bin/python`, no bytecode written; I did not re-run
`make check` or `make acceptance`):
- **The new synthetic sample, parsed** with the product parser. Exactly one percentile cell is
  published: 5231, E12000003 (Yorkshire), annual P90, 2,400,000 pence, CV 14.2. The
  bookkeepers' annual median parses to 2,400,050.
- **The real-file facts, from re-review 1-A.** The same parser on the pinned release found:
  - 0 published percentiles of 13,596 × 10 cells;
  - 5,091 published medians;
  - the mean published, in every period;
  - percentiles published in Table 15 (3).

## Verdict

**N1: fixed.**

| Check | Result | Where |
|---|---|---|
| ADR 0010 decision 4 states the fact | ✅ The decision now says: "no percentile at all (0 of 135,960 percentile cells, in any period); the median for 5,091 of 13,596 estimates, and the mean. Table 15 (3) … does publish percentiles; it is not imported". This matches the file. | `docs/adr/0010-reference-data-and-ai-evidence.md:79-82` |
| ADR 0010 decision 8 | ✅ It says the floor "never could with this release, a reviewed mapping or not". It says the rule is unchanged, and why. It says the statistic or geography is the product owner's R6 decision. One wording nit: Minor m2. | `:157-164` |
| R6 list | ✅ The status line tells the product owner the fact before they confirm decision 8. The consequences list repeats it. Ruling 6 in the report now says "always", not "often". | `:4-12`, `:215-219`; `task-7-sliceB-report.md` ruling 6 |
| DIV1-07 | ✅ The row says: 0 of 135,960; Table 15 (3) does publish; "can never remove a suggestion, with or without a reviewed mapping"; the rule is unchanged; the choice is the product owner's. | `docs/requirements-register.md:131` |
| The full-release test pins the counts | ✅ The test counts 135,960 percentile cells present, 0 published and 5,091 medians from the imported `figures`. The non-zero cell count keeps the zero from being vacuous. `LIKE 'p%%'` matches only p10–p90, never `mean` or `median`, and still works if the driver passes `%%` through unescaped. | `backend/tests/integration/test_reference_data.py:392-407` |
| The sample withholds four-digit percentiles like the real file | ✅ Every percentile is `x` except one labelled `SYNTHETIC EXCEPTION`, with a comment that the real Table 15 (4) never has it, and `P90_EXCEPTION` names it. The docstring is corrected. | `backend/tests/support/reference_data.py:1-14,118-131` |
| The mechanism test still uses the exception | ✅ The discovery floor test reviews the bicycle mechanic to 5231. Its answers' city is Leeds (E12000003), so its £24,000 P90 is still below the £26,000 floor. The test is unchanged. | `backend/tests/integration/test_discovery.py:39,197` |

### Are the two changed expectations justified, and not weakened?

**`test_reference_parsers.py:52-75`: justified, not weakened.**
- The data analysts' annual P90 now asserts withheld (`None`) with marker `x`. That is
  stricter than before.
- The P90's own CV is now asserted on the exception (14.2), beside its median's (8.4), so the
  "own CV" property is kept at parse level.
- The float-artefact case moves from a P90 to a median (`24000.49999999999` gives 2,400,050).
  That is the same property on a value the real file publishes.

**`test_reference_data.py:144-158`: justified, but one property is lost.**
- The data analysts' P90 is now asserted as the full withheld dict (amount, marker, `cv`
  null, band `unreliable`). That is exact for the new data.
- But the old assertion was the only check that a *published* percentile's band comes from
  its own CV, through `PayBenchmark.reliability(statistic)` and the API: "acceptable" from
  14.2, beside the median's "reasonably_precise".
- No test now covers that. See Minor m1.

## New issues

### Critical

None.

### Important

None.

### Minor

**m1. A published percentile's band from its own CV is no longer tested anywhere.**
- Where: `backend/tests/integration/test_reference_data.py:144-158`.
- What: this is a coverage loss from this round, for fix round 1 item 4 (A-M4). It is not a
  softened assertion: the replacement is exact for the new data.
- What the tests now cover:
  - the API test: only the median (published, its own CV) and withheld statistics;
  - the parser test: `AsheEstimate.cvs` only;
  - the band function: `ashe.reliability(cv)` on its own.
- What would survive every test: a change to `PayBenchmark.reliability` (`pay.py:179-185`)
  that bands every published statistic from the median's CV. The API's `cv` field is still
  guarded, because a withheld P90 must show `cv: null`.
- Fix (cheap, uses the labelled exception): assert through the evidence endpoint that the
  bicycle mechanic's 5231 benchmark for a Leeds workspace shows P90 `cv` "14.2" and
  `acceptable`, beside the median's "8.4" and `reasonably_precise`. A domain test of
  `PayBenchmark.reliability("p90")` would also do. This restores a check that existed, so it
  is not new hardening under R12.

**m2. Decision 8 names one reason where there are three.**
- Where: `docs/adr/0010-reference-data-and-ai-evidence.md:160-161`.
- What: "every occupation is kept, after a review as `not_published`" is exact for a year,
  week or hour floor with a city. With a reviewed mapping, a monthly floor gives
  `period_differs` and a profile with no city gives `no_work_area`
  (`pay.modelled_floor_verdict`, `modelled_pay`). "Kept" is true in every case.
- Fix: "kept, as `not_published` (or `period_differs` / `no_work_area`)". This is doc
  polish; it can go to the final-review list.

## Assessment

**N1:** fixed.

**New issues:** Critical 0, Important 0, Minor 2.

**Reasoning:** The fact is recorded exactly in ADR 0010 decisions 4 and 8, the R6 list and
DIV1-07. It is pinned against the real import with a non-vacuous count, and the sample
publishes only its one labelled exception. One cost of the data change was not paid back:
the band of a published percentile from its own CV lost its only test (m1).
