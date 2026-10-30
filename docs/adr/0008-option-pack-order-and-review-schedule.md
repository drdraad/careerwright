# ADR 0008: The England option pack, the order of the remaining work and the review schedule

- Status: Accepted. The three product-owner decisions it records (D1, D2, D3) were confirmed
  by the product owner on 2026-10-28, so nothing here is provisional (ruling R6 does not
  apply).
- Date: 2026-10-28
- Source: [`docs/plan/l0-assessment-handover.md`](../plan/l0-assessment-handover.md), an
  assessment of the specification and the plan against the repository at `cfdae68`, after
  Sprints 0–2. Applied as product specification v1.3, development plan v1.1, the task file
  (`docs/plan/l0-sprint-tasks.md`, rulings R4, R9 and R10, Tasks 6b, 6c, 7b, 7c, 13a and
  13b)
  and the register.
- Requirements: OPTN-08..10, TEST1-09, TEST1-13, TEST1-14, OUT1-10, OPT1-15, OPT1-16,
  REC1-11, H-01, H-06, H-07, H-12, H-13; spec sections 4 (REC-1), 10, 11, 12 (OPT-1) and
  18; ADR 0001; ADR 0005 decision 1; ADR 0007 decision 6

## Context

Sprints 0–2 (Tasks 1–6) took 16 hours of wall-clock time; the plan sized them at 9–12
engineering days. The assessment found four things that change what to do next:

- **Human review sets the pace.** The plan's review points assumed weeks between them.
  Three of the open human gates decide what gets built next, not merely whether it passes.
- **The numerical core would first meet real, reviewed options in Sprint 9.** None of the
  33 required corpus pages has been collected, its rights and label reviews are human and
  undated, and the specification calls course outcomes (OUT-1) "among the most
  error-prone inputs in the system". As planned, the checker and the solver would run on
  synthetic fixtures or unreviewed live extractions only.
- **At the OPT-1 bound, truncation is the expected outcome.** With 24 concepts, two starts
  each and at most six selected, the selection space holds Σ_{k=0..6} C(24,k)·2^k =
  10,161,633 selected sets; the 1,000,000-state cap cannot exhaust it unless sound pruning
  removes most of it.
- **Two requested surfaces do not feed the critical chain in L0.** There are no Adzuna
  credentials (ruling R4) and no accountable AI-resilience reviewer, so the dendrite has no
  live vacancy data and every role is unscored. Both surfaces stay in scope.

Separately, specification REC-1 asks the model to "explain plausible connections", while
ADR 0007 decision 6 chose explanations built from facts only, with no model prose.

## Decisions

1. **The required corpus becomes the England option pack (D1).** The 20 job postings, 10
   course pages and three funding pages are chosen for the five personas' targets (P01–P05)
   and delivered as a reviewed, versioned, dated pack of catalogue records in the
   specification section 18 shapes (LearningOption and Offering, FundingInstrument,
   SkillRequirement rows, `PlanAction.outcomes`), with SourceClaims, rights status,
   `review_state` and dates. It is an immutable public evidence pack (spec section 11):
   fetched and hash-checked like ESCO (ruling R7), or committed if it is small and its
   rights permit. Every record starts `proposed`; review session 2 (H-07) reviews it.
   - *Labelling (ruling R9).* Every surface that uses the pack shows its date and each
     record's review state. A pack record never fills a live field and is never shown as
     current. Synthetic data stays labelled synthetic and never enters the pack.
   - *Live research* (Meta search, Scrapling, Adzuna) writes the same catalogue contract
     with `review_state: proposed`, inside its own workspace. The handover's "the same
     catalogue" means the same record contract, not the shared pack: user research is never
     reused for other workspaces (spec section 11), and the pack is not a shared
     cross-tenant cache (still M1). A proposed record is explorable but never enters an
     unqualified "affordable and feasible" recommendation until reviewed, which is the
     option review checkpoint rule (spec section 10).
   - *Use.* Task 7b curates and labels the pack with the Task 7 pipeline and defines its
     file format; Tasks 9 and 11 load it; Task 11 runs the TRACE-01 checker on a real
     option set for P01's target from it. After session 2, Task 7c applies the product
     owner's H-07 record and publishes a new dated, versioned pack: accepted records carry
     `review_state: reviewed`, rejected ones are left out, every corrected value is
     span-cited, and undecided records stay `proposed`. Tasks 10 and 12 consume that
     reviewed version instead of curating pages, Task 8 consumes its job postings and Task
     13a solves on its instances. The live path, pointed at the same provider pages, is
     scored field by field against the reviewed values (correct, incorrect, missing,
     unsupported, with denominators) in Tasks 8, 10 and 12.

2. **The remaining work follows the critical chain, and Sprint 6 is split (D2).**
   - *Order.* After Tasks 6b and 6c: 7 → 7b → 9 → 11 → session 2 → 7c → 10 → 12 → 8 →
     13a → 13b → 14 → 15 → 16, with session 1 before Task 8. The Sprint 4 and 5 backends
     run before the Roles chapter UI. Task 16 waits for every other remaining task and for
     all three sessions, because release qualification needs all six chapters. The
     dependency rules are in the task file.
   - *Sequential execution* (controller ruling). One implementer runs at a time. Where the
     handover marks tasks as parallel ("10 and 12 may run in parallel with 8"), they have
     no dependency on each other and run one after the other, in either order. The
     handover's "7b ∥ 9" runs 7b first: Task 9 loads the pack in the format Task 7b
     defines.
   - *Sprint 3.* S3.6 delivers the assessment record model, its publication-state checks,
     the lower-bound filter and the unscored state, qualified with one labelled fixture
     record; the review pipeline is data entry through that record model; L0 publishes no
     reviewed real record unless an accountable reviewer exists (H-10), which spec section
     5 allows. The pinned evidence and mapping imports stay in S3.6: the register keeps
     them with Task 7 (AIR1-03, AIR1-07, AIR1-11, TAX1-07), and the exposure-only display
     needs them. S3.5, the Roles chapter, runs after Task 11.
   - *Sprint 6a* (Task 13a): the canonical enumerator, the independent route checker and
     Cartesian oracle, iterative peeling, the coverage flag, all gates and ledgers, complete
     coverage on TRACE-01, the A–I fixture and pack-scale instances, and the measured
     instance sizes at which complete coverage is reached. *Sprint 6b* (Task 13b): the
     disk-backed archive with atomic checkpoints, resume-or-restart, the 30 s / 1,000,000 /
     50,000 caps with stop reasons, the cancellable child process and the 50,000-point
     ranking benchmark. The exact-layer apparatus is built after the core is proven on
     instances that complete.

3. **Human review is scheduled (ruling R10).** Three fixed sessions, about five hours in
   all, each a dispatch precondition for the work after it. The controller does not
   dispatch a task whose precondition session has not happened; it records "blocked:
   awaiting session N".
   - *Session 1* (about 2 h; before Task 8 and before any page body is retained beyond the
     classes it permits): H-06 as a rights *policy* for the permitted source classes of the
     corpus and the pack, so agents can classify pages themselves, and the H-12 checklist in
     ADR 0007. D1–D3 were confirmed outside the session. The first task dispatched after
     the session transcribes its outcome (Task 8 at the latest). Ruling R2 still holds, and
     says so: a person sets the policy, an agent records the class and the terms it relied
     on for each page, and a page outside the permitted classes, or not clearly within one,
     stays "pending human rights review" for a person. Until session 1, ruling R3 governs
     retention.
   - *Session 2* (about 2 h; after Task 11): H-07 for Sprints 4–5 on the option pack and the
     TRACE-01 checker run on P01's real option set, and the formative comprehension session
     (decision 6, H-13). It precedes Task 7c, which publishes the reviewed pack, and through
     it Tasks 10, 12 and 8 (they score the live path against the reviewed values) and Task
     13a; it also precedes the start of Task 14.
   - *Session 3* (about 1 h; before Task 14 closes): the Sprint 7 design review (H-01)
     against what session 2 showed.
   - The other human gates (H-01 for Sprints 3 and 9, H-03, H-04, H-05, H-08, H-10) keep
     their places and are not dispatch preconditions.

4. **A model-written, span-cited "Why this could suit you" (D3; spec section 4, REC-1).**
   At most one bounded model call per slate. It may quote only the person's confirmed
   answers and the grounded occupation record; each quotation is verified server-side
   against its source; it is validated like a search proposal (one repair, then
   `invalid_model_output`) and adds no readiness or affordability claim. The deterministic
   provenance of ADR 0007 decision 6 stays underneath, is shown in every case and is what
   exports cite; a failed explanation is shown as unavailable, never hidden. This
   supersedes two parts of ADR 0007 decision 6: its title ("A suggestion's words come from
   facts, not model prose") and its last sentence ("Model-written explanations are not
   used in L0: grounding by construction was preferred to a second paid call whose prose
   would need its own checks."). Task 6b implements it and amends ADR 0007 to point here.
   Live calls use the test model with synthetic data only, budget-capped and ledgered
   (ruling R5).

5. **The OPT-1 limits are disclosed (spec sections 12 and 18).** `budget_truncated` is the
   expected coverage for large catalogues and `NO_ROUTE_IN_BOUNDED_MODEL` is
   correspondingly rare near the bound. Results, UI and exports treat truncation as the
   normal state: lead with "Best trade-offs found", state the instance size and say which
   narrowing (fewer concepts, one start, a shorter horizon) would let the search complete.
   Task 13a reports the measured sizes. No rule changes: completeness semantics, the caps
   and the layer definitions stay as written.

6. **One formative comprehension session after Sprint 5 (H-13).** One person, 30 minutes,
   synthetic data, on the fixture route comparison and the TRACE-01 ledger (screenshots or
   Storybook). They explain the cost shown, what "conditional readiness" means and what is
   uncertain; any dangerous misunderstanding becomes a Sprint 7 scope input. The product
   owner runs it at session 2. It is formative, not statistical; the five Sprint 9 sessions
   (H-05) are unchanged.

7. **Adzuna stays optional (ruling R4).** If developer credentials are registered and stored
   under `CAREERWRIGHT_HOME` before Task 7 is dispatched, S3.3 qualifies the live integration;
   otherwise it stays "unverified — no credentials". It is external data, still a local run.

8. **Three tasks added by the controller.** Task 6b implements decision 4. Task 6c is the
   visual-corrections batch (Sprint 1 findings V-01, V-03–V-06, V-09, V-10; Sprint 0 findings
   S0-V03, S0-V04, S0-V06 and the Routes part of S0-V07; the Sprint 0 compositions corrected
   and recaptured) and removes the `next` 16.4.1 `minimumReleaseAgeExclude` exception, which
   became eligible at 2026-10-28T17:43Z (ADR 0005 decision 1). The Roles app parts of
   S0-V05, S0-V07 and S0-V08 stay with Task 8. Task 7c, added after the plan update's
   review, publishes the reviewed option pack from session 2's record (decision 1).

## What does not change

The handover's section 6 list stands: the non-deferrable invariants (spec section 1); the
L0 boundary of ADR 0001 and the fixed stack; the durable core as built (streaming,
ownership before decryption and key rotation, spend reservation and reconciliation, database
ownership for worker access); `fixtures/m0` byte-identical, with fixture content only in the
labelled demo workspace; rulings R2 and R5; and the three requested features (the dendrite,
the three Pareto layers and the sliders). Order changes; scope does not. The proposals in
the handover's section 7 were considered and not adopted.

## Consequences

- Specification v1.3 (sections 1, 4, 11, 12, 18, 22), plan v1.1 (the preamble: header,
  "Delivery envelope" and "How to use this plan"; sections 5, 6, 9–12; and the Sprint 2, 3,
  4, 5, 6a, 6b, 7 and 8 cards), the task file and the register change together. No code, test, fixture or configuration changes with this ADR.
- Sprint reviews are written when a sprint's last task finishes, so `sprint-3.md` (Task 8)
  follows `sprint-4.md` (Task 10) and `sprint-5.md` (Task 12); `sprint-6.md` (Task 13b)
  covers 6a and 6b.
- Elapsed time now depends on when the sessions are held. A task waiting for one is
  recorded "blocked: awaiting session N", never started early or self-certified.
- The pack's file format is owned by Task 7b; Tasks 9 and 11 load it through their domain
  models, and a format change needs a pack version bump. In L0 the pack has at least two
  versions: Task 7b's, all `proposed`, and Task 7c's reviewed one, which every later task
  pins by version and hash.
- Live calls added: Task 6b's explanation checks and the live-versus-reviewed scoring in
  Tasks 8, 10 and 12. Each runs on the test model with synthetic or public inputs, behind
  an explicit cap, and is ledgered (R5).
- ADR 0007 decision 6 is superseded in part by decision 4; ADR 0005 decision 1's exception is
  removed by Task 6c.

## Amendment (2026-10-29, plan v1.2)

Source: an intermediate code review that the product owner supplied after Task 7 slice 7A
(`docs/reviews/intermediate-code-review-2026-10-29.md`). The product owner asked for the
plan to be changed where the controller concurs. The controller concurred with all four
points. Scope and architecture are unchanged.

1. **Task 7d, the cancellation lock order.** This is a focused correction with a concurrent
   regression test, run after Task 7 and before Task 7b. The existing lock pattern in ADR
   0009's open items is fixed there, not at the final review.
2. **Evidence before polish (ruling R12).** From Task 7b to session 2, the critical chain
   takes priority. That chain is the option pack, then the capability and outcome model, the
   monthly financial checker, and human review. Hardening that no failing check, reproduced
   defect or Global Constraint requires goes to the final-review list. Task 7b also reports
   an early, unreviewed accuracy read of the deterministic path on its development split.
3. **A boundary on language rules (ruling R11).** Linguistic rules grow only for a
   reproduced defect or an evaluation failure. A hypothetical form is recorded as a known
   limit, and a fail-safe outcome is preferred to a new pattern. Safeguards and accepted
   limitations stay as recorded.
4. **Session 2 grows to about 2½ hours (decision 3).** It also holds H-01 for Sprint 2: the
   design review of the You chapter and the slate, which tests scanning, understanding and
   choosing. Task 10 applies its findings first, and Tasks 10, 12 and 8 build to them. The
   three sessions now total about five and a half hours.

## Amendment (2026-10-29, plan v1.3)

The product owner added a final sprint, Sprint 10 (Task 17, after Task 16): an operator's
manual, written by doing every task it describes in the qualified candidate. Friction points
it finds are logged:
- those a small change smooths are fixed in the sprint, each with a test;
- a larger refactor for user experience is put to the product owner only when there is high
  conviction that its benefit outweighs its cost, and is built only on their decision;
- everything else is recorded as known friction, with the manual's workaround.

The changed candidate is re-qualified, and a new tag needs the product owner's approval. A
new human gate, H-14 (a person follows the manual), is prepared and is not a dispatch
precondition. The controller's final whole-branch review moves to after Task 17.
