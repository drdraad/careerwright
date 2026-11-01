# L0 assessment handover: changes to the specification and the development plan

- Date: 2026-10-28. Branch `l0-local-release`, assessed at commit `cfdae68`.
- For: the planning agent that maintains `Careerwright_Product_Specification.md` (v1.2) and
  `docs/plan/development-plan.md` (v1.0), and the sprint breakdown
  `docs/plan/l0-sprint-tasks.md`.
- Source: an altitude, lateral and depth assessment of the two documents against the
  repository as built (Sprints 0–2 complete). A second, independent assessment was
  compared; its points are adopted only where this document says so (section 7).
- Scope: **L0, the locally running release candidate.** Nothing here needs hosting, a
  cloud account or a public service. The local boundary in ADR 0001 stands.

## 0 What to do with this document

1. Read sections 1–6. Apply the changes in sections 3, 4 and 5 to the three documents.
2. Decisions in section 1 belong to the product owner. If a box is unticked when you
   start, apply the recommended option **as provisional** and record it in a new ADR 0008
   marked "provisional — needs product owner confirmation" (ruling R6).
3. Change documents only: the specification, the plan, the task file, ADR 0008 and the
   affected register rows. **Do not change code, tests, fixtures or configuration.**
4. Where a change below would contradict a non-deferrable invariant (spec section 1) or
   the L0 boundary (ADR 0001), stop and report the conflict instead of resolving it.
5. Finish with the checklist in section 9.

## 1 Decisions for the product owner

| # | Decision | Recommended | Default if unticked |
|---|---|---|---|
| D1 | Build a reviewed, dated England **option pack** for the five personas' targets as an immutable public evidence pack, with live research appending `proposed` records to the same catalogue (section 3, P2; section 4, S1) | Yes | Apply as provisional |
| D2 | **Re-order** the remaining work around the critical chain and split Sprint 6 (section 3, P3–P4; section 5) | Yes | Apply as provisional |
| D3 | Allow a **model-written, span-cited explanation** on each career suggestion, validated like a search proposal (section 4, S3) | Yes, one extra bounded call per slate | Leave ADR 0007 decision 6 as is; record D3 as open |

- [X] D1 confirmed  - [X] D2 confirmed  - [X] D3 confirmed  (product owner, date)

## 2 Verified state the changes rest on

| Fact | Value | Where |
|---|---|---|
| Sprints 0–2 elapsed | 16 hours wall clock (plan: 9–12 engineering days) | `git log` 2026-10-27 21:59 to 2026-10-28 14:18 |
| Code | backend 14,875 lines + 10,995 test lines; web 11,251 + 1,571 e2e | `backend/src/careerwright`, `backend/tests`, `apps/web/src`, `apps/web/e2e` |
| Register | 52 verified, 260 planned, 7 "not run — requires human", 1 open | `docs/requirements-register.md` |
| Real-source corpus | 0 of 20 jobs, 0 of 10 courses, 0 of 3 funding pages; rights (OI-07) and label review (OI-08) human, undated | `corpus/manifest.json`, `corpus/README.md` |
| Live model spend | 24 calls, $0.023 total, test model only | `docs/evidence/live-usage.md` |
| Fast checks on `cfdae68` | `make check` exit 0: 400 backend tests, mypy clean (175 files), 190 web tests, fixture validator passed | run 2026-10-28 |
| Numerical core | not started: the route preview replays fixture numbers and says so; `SignedMoney` deferred to the monthly compiler; `NO_ROUTE_IN_BOUNDED_MODEL` defined, no raise site | `apps/web/src/lib/fixtures/trace.ts`, `backend/src/careerwright/money.py`, `backend/src/careerwright/errors.py` |
| OPT-1 bound | 24 concepts × 2 starts, ≤ 6 selected = 10,161,633 selected sets; the 1,000,000-state cap is under 10% of that | computed; plan Sprint 6 coherence review states the same number |
| Adzuna | no credentials; live vacancy mode ships "unverified" | ruling R4, `docs/dependencies.md` |
| Fixture arithmetic | TRACE-01 and the A–I fixture re-derived by hand: fronts match the spec | `docs/evidence/fixture-hand-check.md`, re-checked in this assessment |

## 3 Changes to the development plan (v1.0 → v1.1)

Apply all of P1–P8. Each row names the plan section, the change, and how you know it is done.

**P1. Human review is a scheduled resource.** Section 6 "Responsibility and sequencing" and
section 10.
- Change: add "Human review sessions" as a first-class schedule item. Three fixed sessions,
  each a dispatch precondition for the task after it:
  - Session 1, before Task 8: rights policy for the corpus and pack (H-06 as a *policy*
    for the permitted source classes, so agents can then classify pages themselves), the
    H-12 checklist in ADR 0007, and D1–D3 above. About 2 hours.
  - Session 2, after Task 11: H-07 for Sprints 4–5 on the option pack and the TRACE-01
    checker, plus the formative comprehension session (P5). About 2 hours.
  - Session 3, before Task 14 closes: the Sprint 7 design review (H-01) against what
    session 2 showed. About 1 hour.
- Change: add a "Human review hours" column to the sprint roadmap table (section 6), and
  state in "Delivery envelope" that with agent implementers engineering days are a sizing
  unit and elapsed time is set by human review hours.
- Why: Sprints 0–2 took 16 hours; the plan's review points assumed weeks between them.
  Three of the open gates decide what gets built next, not merely whether it passes.
- Done when: the roadmap table has the column, section 10 names the three sessions and
  the gates each closes, and each affected task card lists its session as a precondition.

**P2. The required corpus becomes the option pack (D1).** Section 9 "Required corpus" and
"Evaluation outputs"; Sprint 4 and Sprint 5 cards; section 11 traceability.
- Change: the same 20 job postings, 10 course pages and 3 funding pages are chosen for
  the five personas' targets, and the labelled result is delivered as a **reviewed,
  versioned, dated England option pack**: catalogue records in the spec section 18 shapes
  (LearningOption and Offering, FundingInstrument, SkillRequirement rows, PlanAction
  outcomes) with SourceClaims, rights status, `review_state` and dates. It is an
  immutable public evidence pack in the spec section 11 sense: fetched and hash-checked
  like ESCO (ruling R7), or committed if small and rights permit. Every surface shows its
  date and review state; it never fills a live field; synthetic remains labelled synthetic.
- Change: live research (Meta search, Scrapling, Adzuna) writes to the **same catalogue
  contract** with `review_state: proposed`. Proposed records are explorable but excluded
  from an unqualified "affordable and feasible" recommendation until reviewed, which is
  already the option-review-checkpoint rule (spec section 10).
- Change: Sprint 5 acceptance adds: the TRACE-01 checker runs on at least one real option
  set for P01's target from the pack, every consequential field span-cited and
  human-reviewed. Sprint 3–5 acceptance adds: the live path, pointed at the same provider
  pages, is scored field by field against the reviewed values (correct, incorrect,
  missing, unsupported, with denominators).
- Why: spec section 10 calls OUT-1 "among the most error-prone inputs in the system". As
  planned, the numerical core would be exercised on synthetic fixtures or unreviewed live
  extractions only, and nobody could judge either before Sprint 9.
- Done when: section 9 describes the pack and its labelling rules; Sprint 4 and 5 cards
  carry the new acceptance items; section 11 maps the pack to its evidence.

**P3. Order the remaining sprints around the critical chain (D2).** Section 6 roadmap and
"Responsibility and sequencing"; Sprint 3 card.
- Change: the backend slices of Sprints 4 and 5 run before the Roles chapter UI. In task
  terms: Task 7, then Tasks 9 and 11, then Task 8 (details in section 5). The plan already
  states that visual work can proceed alongside the chain; make the order explicit.
- Change: Sprint 3 S3.6 (AI resilience) delivers the record model, publication-state
  checks, lower-bound filter and the unscored state, qualified with one labelled fixture
  record. The review pipeline is data entry through the record model. L0 publishes no
  reviewed real record unless an accountable reviewer exists, which the spec already
  allows ("the beta can expose unscored roles and the functioning range filter").
- Why: the dendrite has no live vacancy data in L0 (no Adzuna credentials) and every role
  will be unscored; both surfaces are requested and stay in scope, but neither feeds the
  chain.
- Done when: the roadmap shows the order; the Sprint 3 card states the reduced S3.6
  deliverable and the deferred position of S3.5.

**P4. Split Sprint 6 (D2).** Sprint 6 card.
- Change: Sprint 6a: canonical enumerator, independent route checker, independent
  Cartesian oracle, iterative peeling, coverage flag, all gates and ledgers, complete
  coverage on TRACE-01, the A–I fixture and the pack-scale instances; report the measured
  instance sizes at which complete coverage is reached with the implemented sound pruning.
  Sprint 6b: the disk-backed archive with atomic checkpoints, resume-or-restart, the
  30 s / 1,000,000 / 50,000 caps with stop reasons, and the 50,000-point ranking benchmark.
- Why: at the model's bound the state cap cannot exhaust the selection space, so truncated
  is the expected coverage for large catalogues; the exact-layer apparatus should be built
  after the core is proven on instances that complete.
- Done when: two cards with their own acceptance; 6a's acceptance includes the measured
  coverage sizes.

**P5. One formative comprehension session after Sprint 5.** Section 5 "Accessibility and
local performance"; Sprint 5 card.
- Change: one person, 30 minutes, synthetic data, on the fixture route comparison and the
  TRACE-01 ledger (screenshots or Storybook are acceptable surfaces). They are asked to
  explain the cost shown, what "conditional readiness" means, and what is uncertain. Any
  dangerous misunderstanding is recorded as a Sprint 7 scope input. The five Sprint 9
  sessions are unchanged. This is formative, not statistical.
- Why: the only user contact in the plan is in Sprint 9, after the two most expensive UI
  sprints.
- Done when: section 5 and the Sprint 5 card name the session, its questions and its
  owner (product owner, session 2).

**P6. Adzuna (optional).** Sprint 3 card and ruling R4.
- Change: if developer credentials are registered and stored under `CAREERWRIGHT_HOME` before
  Task 7, S3.3 qualifies the live integration; otherwise the card is unchanged. External
  data, still a local run.

**P7. Risk register.** Section 12.
- Add two rows: "Human review becomes the bottleneck" (response: P1) and "The numerical
  core is unexercised on real, reviewed options before Sprint 9" (response: P2, P5).

**P8. Version and record.** Header and "How to use this plan".
- Bump to v1.1, dated, with a one-paragraph change note pointing at this document.

## 4 Changes to the specification (v1.2 → v1.3)

The specification is sound and remains the authority. Make only these three changes, each
a clarification or disclosure, and record them in section 22.

**S1. Option pack as an immutable public evidence pack (D1).** Section 11, first paragraph,
and the section 1 BND-1 table row "Research and caching".
- Add: a reviewed, versioned, dated option pack covering the qualification personas'
  targets is an immutable public evidence pack and a permitted common read-only input in
  M0. State its labelling rules (date and review state always shown; never fills a live
  field; never shown as current) and that live research writes to the same catalogue
  contract with `review_state: proposed`, excluded from unqualified recommendations until
  reviewed. This is consistent with section 10's option review checkpoint and section 18's
  `review_state`; it does not add a shared cross-tenant cache (still M1).

**S2. Disclose the consequence of the OPT-1 limits.** Section 12 "Solver architecture and
choice" and section 18 "API surface".
- Add: at the M0 upper bound the selection space alone holds 10,161,633 selected sets, so
  the 1,000,000-state cap cannot exhaust it unless sound pruning removes most of it.
  `budget_truncated` is therefore the expected coverage for large catalogues and
  `NO_ROUTE_IN_BOUNDED_MODEL` is correspondingly rare near the bound. Results, UI and
  exports treat truncation as the normal state: lead with "best trade-offs found", state
  the instance size, and say which narrowing (fewer concepts, one start, shorter horizon)
  would let the search complete. Sprint 6 reports the measured instance sizes at which
  complete coverage is reached. No rule changes: completeness semantics, the caps and the
  layer definitions stay as written.

**S3. Model-written, span-cited explanations in REC-1 (D3).** Section 4 "Personality-informed
career suggestions".
- Add: a model-written "Why this could suit you" is permitted when it quotes only the
  person's confirmed answers and the grounded occupation record, each quotation verified
  server-side, and is validated like a search proposal (one repair, then invalid output).
  Deterministic provenance remains underneath and is what exports cite. If D3 is not
  confirmed, add nothing to the spec and leave ADR 0007 decision 6 in force.

**Section 22.** Add a "Version 1.3 review decisions" table with the three rows above, each
marked accepted or provisional per section 1, and bump the header to 1.3 with the date.

## 5 Changes to the sprint task file

**T1. New task: option pack curation.** Insert after Task 7 as "Task 7b". It fetches and
labels the 33 pages for P01–P05's targets under ruling R3 using the Task 7 pipeline,
assigns template families and splits, builds the pack with every record
`review_state: proposed`, and hands the review to session 2. Tasks 10 and 12 then consume
the pack instead of curating pages; Task 8 consumes the 20 job postings. Task 11's
acceptance gains the real option set (P2).

**T2. Dependency rules** (state them; then give the suggested order):
- Task 8 after Task 11. Task 13a after Task 11 and session 2. Task 13b after 13a.
- Task 14 starts after session 2's findings exist and closes only after session 3.
- Session 1 before Task 8 and before any page body is retained beyond the classes it
  permits.
- Suggested order: 7 → 7b ∥ 9 → 11 → session 2 → 10 → 12 → 8 → 13a → 13b → 14 →
  15 → 16. Tasks 10 and 12 may run in parallel with 8.

**T3. Dispatch preconditions in each brief.** Each task card lists the human gates it
depends on and the session that closes them. The controller does not dispatch a task whose
precondition session has not happened; it records "blocked: awaiting session N" instead.

**T4. Task 13 split** into 13a and 13b per P4, with the measured coverage sizes in 13a's
report.

**T5. Task 7 and Task 8 scope notes** per P3: S3.6 reduced deliverable; S3.5 after Task 11.

**T6. Standing rulings.** Add R9 (pack labelling: date and review state always shown,
proposed never enters an unqualified recommendation, synthetic stays labelled) and R10
(the three sessions and their gates). Update R4 if Adzuna credentials exist.

**T7. Register.** Add or amend rows for: the OPT-1 truncation disclosure and measured
coverage sizes (OPT1 family); pack labelling and the proposed-state rule (OPTN or ACQ
anchors); the live-versus-reviewed field scoring (TEST1 or a plan section 9 family); the
formative session as a human gate (new H-13); the three sessions as preconditions
(section 5 of the register). Keep IDs unique and never renumber.

## 6 Preserve: what must not change

- The non-deferrable invariants (spec section 1): unknown is never zero or ineligible;
  failure is never an empty success; truncated is never infeasible; nothing invented;
  the model never commits.
- The L0 boundary (ADR 0001) and the fixed stack. Local removes no isolation, secret,
  money, cancellation or deletion requirement.
- The durable core as built. Each part traces to an M0 line the local plan retains:
  streaming (spec section 4, "Stream natural conversation…"), ownership before decryption
  and key rotation (section 16, "Enforce ownership before decryption; test nonce/key
  rotation and revocation"), spend reservation and reconciliation (section 16), ownership
  enforced in the database for worker access (plan section 3). Cost tracking is the
  product owner's R5 instruction. No simplification before the solver exists, and none
  afterwards without a spec change.
- `fixtures/m0` byte-identical; fixture content only in the labelled demo workspace.
- Rulings R2 (human gates are never self-certified) and R5 (every live call ledgered).
- The three requested features: the dendrite, the three Pareto layers and the sliders.
  Order changes; scope does not.

## 7 Proposals considered and not adopted

Listed so they are not re-adopted from the other assessment.

| Proposal | Why not |
|---|---|
| "Kill-order": eliminate targets by pure pre-checks before research or search | Prefunding, payment cap and workload are per-schedule checks that need option costs, so they cannot run pre-research. A target-level "killed" verdict contradicts the invariants: a conservative monthly rejection or an unknown is never ineligibility, and P04 must remain "unresolved" or "out of model", never dead. The surviving part, a pure checker before the optimiser, is already the plan's order. |
| Simplify the durable core now (drop streaming partials, reduce permission checks, replace spend accounting) | Each part is an M0 requirement retained locally (section 6). The other assessment itself concluded "do nothing here until the solver lands". |
| Require the spec's 10–15 person concierge design for any comprehension study | That study is M1. L0's design is the plan's five formative sessions; P5 adds one earlier formative session, not a study. |
| Remove fixture numbers from the product path entirely | The demo workspace is fixture content by design, labelled. The rule is confinement, not removal. |
| A "quote pass" on the register, live usage, proxy and CSP | Done in this assessment: every FIN1, TIME1, OPT1 and RDY1 row is `planned`; 24 live entries; the forwarder is a pass-through, Host is checked against `CAREERWRIGHT_WEB_ALLOWED_HOSTS`, the CSP is `connect-src 'self'` plus the Auth emulator with `frame-ancestors 'none'`, tested. Nothing contradicted either assessment. |

## 8 Evidence pointers

- Pace: `git log --format='%ad %h %s' --date=iso` on `l0-local-release`.
- Register counts: `grep -c` over the Status column of `docs/requirements-register.md`;
  human gates in its section 5 (H-01 to H-12).
- Corpus: `corpus/manifest.json` `collected_samples` and `open_items` OI-07, OI-08.
- Spend: `docs/evidence/live-usage.md` rows 1–24, running total $0.023098.
- Fast checks: `make check` on `cfdae68`, exit 0.
- Numerical core absent: the module docstrings of `apps/web/src/lib/fixtures/trace.ts` and
  `backend/src/careerwright/money.py`; `NO_ROUTE_IN_BOUNDED_MODEL` referenced only in
  `backend/src/careerwright/errors.py` and `apps/web/src/lib/vocabulary.ts`.
- OPT-1 bound: Σ_{k=0..6} C(24,k)·2^k = 10,161,633, matching the plan's Sprint 6 coherence
  review.
- Spec lines relied on: section 4 streaming and validation (line 299); section 16 key
  handling (line 961); section 10 OUT-1 "most error-prone"; section 11 immutable packs;
  section 12 limits and coverage; section 20 P04 and P05 required results.
- Intent-versus-behaviour note: ADR 0007 decision 6 versus spec REC-1 "explain plausible
  connections"; Sprint 2 review visual finding 2.
- Not verified in this assessment: `make acceptance`, any live call, the app in a browser,
  Adzuna terms, the Scrapling licence fit. No user evidence exists in the repository; all
  value claims are hypotheses.

## 9 Done when

- [ ] `Careerwright_Product_Specification.md` is v1.3: S1–S3 applied as section 1 directs;
      section 22 has the v1.3 table; nothing else changed.
- [ ] `docs/plan/development-plan.md` is v1.1: P1–P8 applied; roadmap has the human review
      hours column; Sprint 3, 4, 5, 6a and 6b cards updated.
- [ ] `docs/plan/l0-sprint-tasks.md`: T1–T7 applied; dependency rules and the suggested
      order stated; preconditions in every remaining task card.
- [ ] `docs/adr/0008-option-pack-order-and-review-schedule.md` exists, marked provisional
      for any unticked decision in section 1, and links this document.
- [ ] Register rows added or amended per T7; IDs unique; no row relaxed.
- [ ] No change outside those documents; `git status` shows only them.
- [ ] A short report back: which decisions were applied as confirmed versus provisional,
      and any conflict found with an invariant or the L0 boundary (section 0, item 4).
