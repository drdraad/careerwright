# Task 12b, backend half (12bA): report

Status: DONE_WITH_CONCERNS (concerns at the end). Worktree `/home/user/careerwright-wt/12b`,
branch `wt-12b`, rebased onto `claude/confident-ramanujan-ux3saw` (b22194a). Head `79bce14`.

Commits:
- `d9dbf8e` Options checkpoint facts and commands: pack 0.4.0 pinned, the person's figures,
  added options, expected entry, scope
- `6e11807` Integration: the stored inputs carry Task 12b's empty answers
- `ce17d60` Checkpoint: each option's planned outcomes with the person's decision; ADR lines
- `79bce14` Register rows (last commit, after the rebase)

## What I built (backend and API only; facts and codes, no sentences)

1. **Pack 0.4.0 pinned** (`capability/commands.py` `PACK_VERSION = "0.4.0"`). Settled the
   honest way without a new reference: pack 0.4.0's targets, skill rows, skill requirements and
   job postings are byte-for-byte 0.2.0's (checked), so reference 0.2.0 is *carried* unchanged.
   `capability/reference.py`: `CARRIED_TO = {"0.2.0": {"0.4.0"}}`; `check_reference` accepts the
   carry; `load_reference` refuses it unless `carried_changes` finds the four capability parts
   identical. The reference file and its pin are untouched; nothing invented. 0.3.0 is not
   carried (tested). ADR 0012 line and ADR 0011 amendment.
2. **The checkpoint's facts**: `GET /v1/workspaces/{id}/planning/checkpoint`
   (`planning/checkpoint.py`, `commands.checkpoint_view`). Per target: each option's
   `missing` facts (`start_date`, `finish_date`, `cost`, `weekly_hours`, `entry_confirmation`,
   `eligibility_confirmation`), `supplied` facts, stated intakes, entry requirements with the
   person's qualifications (Skills' rule), eligibility conditions with status, age rules
   (`applied: false`), planned outcomes with the person's accept/override, `left_out`; each
   scheme's age rules; `reviewed_options` count; `scope` with `retain_variants` and counts.
   Beside them: needs, both caps, `payment_cap_basis = payments_and_debt_repayments`, work
   status, baseline, continuation, `not_working`.
   **Where a supplied figure is stored (my ruling):** in the planning inputs document
   (`offering_figures`), through the existing PUT command (expected version, Idempotency-Key).
   No migration, no new table. A figure fills only a missing fact (one for a stated fact is
   refused `not_missing`, and never applied if a newer pack later states it); a stated intake
   must be one the page lists (`not_a_stated_intake`); a supplied start plus the page's one
   exact length gives the finish. Each supplied fact is named on the offering and the route
   carries `supplied_figures`.
3. **"Add an option yourself"** (`planning/own_options.py`, `planning/option_texts.py`):
   `POST .../planning/option-texts` keeps pasted text as the person's own input (Task 7's
   `pasted_text` route, contact details removed, sealed; the answer is ID and hash only, so no
   words sit in the plaintext receipt), `GET .../option-texts/{id}` reads it back in that
   workspace only. Options are stored in the inputs document (`own_options`), stamped with who
   and when (dated; re-dated when changed), `proposed`, citing the text (ID, hash, UTF-16
   offsets, excerpt) or "typed by the person". `GET .../planning/options` and the checkpoint
   read them beside the pack; a target outside the pack gets its own label (`own options`).
   Routes through one carry `own_options` and `proposed_records`. No run kind.
4. **Carried items** (checked against the code; all were already done, now each tested):
   - Stacking unresolved until confirmed: done by 12a (`stacking_unconfirmed`), tested in
     `test_planning_checks.py`.
   - The payment cap's meaning: the checker already applies D15 (`P_m + R_m <= M_m`) and names
     repayments alone (`repayments_above_payment_cap`, tested). New: the checkpoint serves the
     fact `payment_cap_basis` for the question's words (12bB).
   - The explicit "no" to entry requirements: its own finding by 12a, tested.
   - Ledger month rows never partial-as-known: done (null rows), tested.
   - Outcome accept/override at the checkpoint: the command is 12a's; new, the checkpoint
     shows each option's outcomes with the decision (tested).
5. **School leavers:** `BaselineKind.STAYING_IN_EDUCATION`; 0 hours/£0 is a stated figure
   (`not_working`), routes computed on it; an expected qualification makes the new unresolved
   finding `entry_requirements_expected`, never met even after a "yes"; age rules shown, never
   applied (no age is known); the tuition fee loan and Advanced Learner Loan stay 12c's
   `VariantInputs.tuition_fee_loan` command, unchanged.
6. **Never truncate silently:** `scope.code = retain_variants` with concept and start counts;
   `excluded_variants` stores what the person leaves out, the solve reads only the rest;
   `check_scope` now also names `size` beside `limit`.
7. **P01 at the API**: integration test with a real worker: without the facts each option is
   set aside naming `dates_unknown`, `cost_unknown`, `workload_unknown`, never "no route"; with
   C01's facts supplied, `routes_found`, the C01 route carrying `supplied_figures`.
8. No migration needed. Generated client regenerated. ADR lines: 0011, 0012, 0013, 0016.
   Register rows: OPTN-11, OPTN-13, OPTN-15, BND1-07, OUT1-09, and the T12b parts of OPTN-03
   and PROF-13, each "backend; screens in 12bB". Search: `entry_requirements_expected` joins
   rule 2, so `PRUNING_VERSION = sound-pruning-6`; DBOS `application_version` unchanged.

Other files touched: `evidence/acquisition.py` (`_reference_url` made public as
`reference_url`), `evidence/store.py` (`workspace_pasted_document`),
`capability/skills_commands.py` (`_qualifications` made public as `person_qualifications`),
`planning/catalogue.py`, `pack.py`, `inputs.py`, `compiler.py`, `checker.py`, `search.py`,
`solves.py`, `commands.py`, `api/routes_planning.py`.

## Rulings

- R-a: reference 0.2.0 carried to 0.4.0, checked in code (above). No human review needed:
  nothing in the reference changes or is newly written.
- R-b: the checkpoint's answers live in the planning inputs document, one command, no table.
- R-c: in an added option, *words* (title, provider, entry requirement) may be a span; *figures*
  (dates, hours, cost) are always typed, each optionally citing a span. Reading a date or an
  amount from words would be a new language rule (R11).
- R-d: an achieved qualification naming an entry requirement is shown, but does not confirm
  entry by itself; the person's own entry answer decides. An expected-only match forces
  unresolved.
- R-e: a supplied cost is the whole cost, due in the first month (D12's rule); it replaces only
  plans whose cost is not known.
- R-f: own options are capped at 24 across targets; left-out options at 200.

## Checks run

- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24), final, after the
  rebase: pass (backend 2202 passed, 9 skipped; web 472 passed; client matches).
- Focused integration under the lock, with the build shim (each one guarded command):
  1. checkpoint, options, inputs, capability, skills: 53 passed, 1 failed (the inputs
     round-trip test now sees the three new empty lists: expectation updated, intended change).
  2. inputs, route solves (incl. the new P01 test), migrations, targets: 60 passed.
  3. After the last code change: checkpoint, inputs, options: 28 passed.
- TDD: honestly, most tests were written right after the code, not before it. The new domain
  file is `tests/domain/test_option_checkpoint.py` (18 tests). Two tests failed on first run
  (a wrong UTF-16 offset in the test, and a school-leaver case whose living costs broke the
  reserve). Both were test fixes, not code fixes.
- `make acceptance`: not run, the controller runs it.
- Live calls: none. Cost $0.

## Concerns

- Pinning 0.4.0 changes what every chapter shows (the pack label is now 0.4.0, 62 reviewed / 67
  proposed; bookkeeping gains the T Level option C11). I updated the integration assertions
  that named 0.2.0. The web and e2e had no 0.2.0 strings, but the controller's acceptance run is
  the real check.
- `offering:C06`'s stated intakes (Feb and Mar 2026) are in the past. They are offered as
  stated, and choosing one gives an honest `starts_before_planning`.
- Without evidence the readiness milestone can't be assessed, so P01 with figures and no
  evidence reads `unresolved`, not routes. The acceptance tests use synthetic evidence at the
  required level, as Task 13b's do.
- The checkpoint doesn't pair a loan scheme with a degree automatically. The tuition-fee-loan
  question for an option is 12c's existing input, and the screens decide where to ask it.

## Paths a reviewer can skip

`apps/web/src/generated/**` (regenerated client).

## Review

Reviewer: the one independent reviewer for 12bA (R16, R17). Read: env-cloud, the reviewer
contract, the brief's Task 12b card, the carried items, the dispatch, this report (as
unverified claims) and the package `review-b22194a..79bce14.diff` in four passes (API and
capability; planning sources; domain tests; integration tests, ADRs and register). Worktree
head checked: `79bce14`. Read-only apart from this section. No suites re-run; four focused
read-only Python checks on the committed packs (below). No web, no live calls, no Docker.

### Spec Compliance
- ❌ Issues found: one (I1, `planning/figures.py:178`). Everything else the dispatch asks for
  is present.
- ⚠️ Cannot verify from diff: `make acceptance` and the web and e2e journeys on pack 0.4.0
  (the controller runs them); the payment cap's question words, the "if you get your grades",
  "loan to repay" and "not working: 0 hours, £0" sentences, the plain line for a target with no
  reviewed options, and "pin" beside "exclude" (all 12bB); session 2's outcome record, the
  funding corpus and `docs/reviews/sprint-5.md` (12bB).

Checked, risk by risk:
1. **Reference 0.2.0 carried to 0.4.0.** The check is real: `load_reference` re-runs every
   rubric, gate and target check against 0.4.0 and refuses unless `carried_changes` finds
   targets, skill rows, skill requirements and postings equal; only 0.2.0 to 0.4.0 is allowed
   (0.3.0 refused, tested). I compared the parsed packs myself: those four parts are equal, and
   so are the 18 outcomes; none of 0.2.0's 464 claims or 33 sources changed (0.4.0 only adds
   claims and sources, one option, one offering (C11) and six funding instruments). So it is
   honest that nothing new needs a reference. The guard is not complete for later versions
   (M1).
2. **Supplied figures.** They are labelled per offering (`supplied`), carried to the compiled
   variant and turned into the `supplied_figures` qualification. The verdict reads
   `affordable_and_feasible_with_qualifications`, never unqualified (domain test). A figure for
   a fact the page states is refused (`not_missing`) and never applied. Without the facts,
   each set-aside option names `dates_unknown`, `cost_unknown` and `workload_unknown`, never
   "no route" (domain and API). `NO_ROUTE_IN_BOUNDED_MODEL`'s coverage rule is untouched. But
   a supplied cost changes an instalment plan's shape (I1).
3. **"Add an option yourself".** The option is `proposed`, dated (re-dated when changed) and
   cites its text ID, hash and UTF-16 span, or "typed by the person". It sits beside the pack,
   and its routes carry `own_options` and `proposed_records`. Words come from typing or spans;
   figures are always typed. No model and no run kind. The pasted text is redacted, sealed and
   read back only in its own workspace (the function joins on the owner, and the store query
   filters on `workspace_id` and `pasted_text`), and it is left out of the source-outcome
   counts (`route <> 'pasted_text'`).
4. **Carried items.** Stacking (`stacking_unconfirmed`), repayments
   (`repayments_above_payment_cap`), the explicit "no" (`entry_requirements_not_met`) and the
   ledgers' null month rows were all done by 12a and are tested there. The checkpoint adds
   `payment_cap_basis` and each option's outcomes with the decision (tested). Done.
5. **School leavers.** `staying_in_education` is in; `not_working` is derived only from a
   stated 0 hours and £0. An expected qualification is never met, even after a "yes", and the
   person's own "no" wins (tested). Age rules are shown with `applied: false`; no code reads an
   age. The fee loans are 12c's command, unchanged.
6. **Truncation.** `scope.code = retain_variants` with the counts. Exclusions are stored, and
   `check_scope` now gives `size` beside `limit`. Lists over their caps are refused with a 422,
   never cut.
7. **Writes.** Both writes go through `run_idempotent` with an `Idempotency-Key`; the inputs
   write has its expected version. The pasted-text receipt holds the ID and hash only. Errors
   carry field and reason codes. No migration and no new table.
8. **R11.** The API serves codes and numbers. There are two new composed reason strings (M3).
9. **P01's synthetic evidence.** It is labelled ("Synthetic evidence ...", synthetic
   workspace). The test proves what the card asks: with the figures, a computed C01 route
   qualified `supplied_figures`; without them, the missing facts named.
10. **Tests written after the code.** They mostly assert real behaviour and would catch
    removing the qualification, letting a figure override the page, or meeting an expected
    entry. Gaps are in M4.

### Strengths
- The figure model is conservative: a figure only fills a gap, the page wins, and a stored
  figure is ignored once a newer pack states the fact.
- The reference carry is checked in code at load, not just asserted in an ADR.
- Spans reuse 10A's UTF-16 rule, including the emoji boundary case, in both domain and API
  tests.

### Issues
#### Critical
None.

#### Important
- **I1 (truth). `backend/src/careerwright/planning/figures.py:178-184` (with `compiler.py:383`,
  `figures.py:144`).** A supplied cost turns a stated instalment plan into one payment in month
  0, and keeps the plan's "instalments" ID and label. I checked this on pack 0.4.0: C04's
  `instalments` plan ("from £69.52/month", count unknown) plus a supplied £3,336.72 becomes one
  £3,336.72 payment at offset 0. `refused` accepts this because not every plan's cost is known.
  D12's rule is for "a total with no stated schedule"; this plan states a monthly schedule.
  The person would see the instalments route broken by their monthly payment cap ("not
  feasible in this monthly model") when real instalments might fit. That is exactly the
  question the carried item names for C04 ("whether the fee falls as a single payment").
  Second effect: `supplied` is set on the offering, so the sibling `pay-in-full` variant, whose
  £2,995 the page states, is also qualified `supplied_figures` though it rests on no figure.
  Fix: key a supplied cost to the plan (the variant) and refuse it where the plan states a
  schedule, or keep the stated monthly amount and supply only the count or total. Then put
  `supplied` on the variant, not the offering. Add a test on C04.

#### Minor
- **M1 (list). `capability/reference.py:303`.** `carried_changes` compares four parts, not
  the `outcomes` (rubric levels) nor the claims and sources those parts cite. Everything is
  identical today (checked), so the carry is honest now; a future `CARRIED_TO` entry would
  not be fully guarded. Add `outcomes`, and the cited claims and sources.
- **M2 (truth, conservative).** On an offering whose page fee is an eligible learner's (C01),
  a supplied cost is still treated as that fee: `eligibility_confirmation` stays missing and
  the route stays unresolved (`checker.py:727`). Someone who is not eligible and gives their own
  price can never get a computed route. Never falsely feasible. Question for the product
  owner's session: does a supplied whole cost replace the eligible-learner condition?
- **M3 (list). `figures.py:171` and `own_options.py:57`.** "the dates given do not fit" and
  "not given yet" are composed reason strings, not codes. This follows pack.py's existing
  reasons, but R11 prefers codes.
- **M4 (list).** No API-level test that a solve applies expected entry: the wiring at
  `solves.py:136` is right by reading, but nothing fails if it is dropped. The first
  checkpoint integration test gives an expected GCSE and asserts nothing about it.
  `excluded_variants` reaching a real solve is tested only at the domain level.
- **M5 (list). `planning/option_texts.py:52`.** No cap on how many option texts a workspace
  may paste (exemplars have three). This affects storage only.
- **M6 (list). `own_options.py:172-180`.** If an option's text were ever missing, every
  options, checkpoint and solve read for the workspace would return INTERNAL_ERROR. Today no
  path removes these texts, so this holds; worth a test or a note if one is added.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The facts, commands, own options, the reference carry and P01's acceptance are
sound and honestly qualified. One truth defect needs fixing before the Options chapter shows
C04: a supplied cost recasts a stated instalment plan as a lump in month 0 and
over-qualifies the page-priced variant.

Counts: Critical 0, Important 1, Minor 6.
