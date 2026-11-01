# Plan update report: L0 assessment handover applied

- Date: 2026-10-28. Branch `l0-local-release`, base `b543fd3`.
- Source: `docs/plan/l0-assessment-handover.md`. D1, D2 and D3 were ticked (product owner,
  2026-10-28) and are applied as **accepted**; nothing is provisional.
- Status: **DONE**. Documents only; no conflict with a non-deferrable invariant or ADR 0001.
  One interpretation needs the controller's confirmation (S3.6 imports, decision 1 below).

## Commits

| Commit | Files | Content |
|---|---|---|
| `3d2f377` | `Nessa_Product_Specification.md` | v1.3: S1, S2, S3 and the section 22 table |
| `9151d84` | `docs/plan/development-plan.md` | v1.1: P1–P8, plus S2.7 for D3 |
| `28a2a27` | `docs/plan/l0-sprint-tasks.md`, `docs/adr/0008-option-pack-order-and-review-schedule.md` | T1–T6, controller rulings (6b, 6c, sequential execution), ADR 0008 |
| `d676aee` | `docs/requirements-register.md` | T7 rows and owner amendments |

`git diff --stat b543fd3..HEAD`: the 5 files above only (767 insertions, 135 deletions).
`git status`: clean. No code, test, fixture, configuration or `CLAUDE.md` change. Not pushed.

## Specification (v1.2 → v1.3)

- Header (line 5): "Version 1.3 | 28 October 2026 | Research checked 26 October 2026".
- **S1 (D1).** Section 1 BND-1 table, "Research and caching" M0 cell (line 50): adds the
  reviewed, dated option pack as an immutable public evidence pack, with live research
  `proposed` until reviewed. Section 11: the first paragraph (line 628) now says the
  common read-only packs include the option pack; a new "M0 option pack" paragraph
  (line 630) covers the section 18 shapes, labelling rules (date and review state always
  shown, never fills a live field, never shown as current, synthetic stays labelled),
  live research writing the same catalogue contract "inside its own workspace" with
  `review_state: proposed`, its exclusion from unqualified recommendations, and that it
  is not a shared cross-tenant cache (still M1).
- **S2.** Section 12 OPT-1, new "Consequence of the M0 limits" paragraph (line 801):
  Σ C(24,k)·2^k = 10,161,633 (re-derived by hand), `budget_truncated` is the expected
  coverage, `NO_ROUTE_IN_BOUNDED_MODEL` is rare near the bound, results/UI/exports lead
  with "Best trade-offs found", state the instance size and name the narrowing; measured
  sizes are reported; no rule changes. Section 18 API surface (line 1177): one sentence
  saying the same for truncated results.
- **S3 (D3).** Section 4 REC-1, new paragraph after the controls paragraph (line 255):
  at most one bounded call per slate; quotes only confirmed answers and the grounded
  occupation record, each verified server-side; validated like a search proposal (one
  repair, then invalid output); no readiness or affordability claim; deterministic
  provenance underneath and cited by exports.
- **Section 22** (line 1294): "Version 1.3 review decisions" with one intro paragraph and
  three rows: D1 accepted (confirmed), S2 accepted as a disclosure, D3 accepted
  (confirmed). Nothing else in the specification changed.

## Development plan (v1.0 → v1.1)

- **P1 Human review sessions.** Delivery envelope (line 23): engineering days are a
  sizing unit; Sprints 0–2 (9–12 days) took 16 hours; elapsed time is set by human review
  hours. Roadmap (line 183): new "Human review hours" column. Section 6 "Human review
  sessions" paragraph (line 219). Section 10 "Human review sessions (v1.1)" (line 685):
  table naming sessions 1–3, when, the gates each closes, and what each is a precondition
  for; dependent work is "blocked: awaiting session N" otherwise. Session 1 covers H-06
  policy and the H-12 checklist; D1–D3 need no session time (controller ruling).
- **P2 Option pack (D1).** Section 9: new "The England option pack (v1.1, D1)" (line 635)
  with the section 18 shapes, the R7/commit rule, three labelling rules, and live research
  writing the same contract inside its own workspace as `proposed`. Evaluation outputs:
  new "Live versus reviewed" row (line 652). Sprint 3 acceptance (line 339), Sprint 4
  acceptance (line 375) and Sprint 5 (S5.2 line 393; acceptance line 409) carry the pack
  and live-versus-reviewed items; Sprint 5 adds the TRACE-01 checker on P01's real option
  set. Section 11: new "England option pack (D1)" traceability row (line 717).
- **P3 Order (D2).** Section 6 "Order of the remaining work (v1.1)" (line 206): eight
  ordered steps, session 1 placement, sprint reviews written out of numeric order,
  sequential execution. Sprint 3 card: S3.5 deferred position (line 333); S3.6 reduced
  deliverable (line 335).
- **P4 Sprint 6 split (D2).** "Sprint 6a" (line 417) with S6.1, S6.2, S6.5 (peeling),
  S6.6 and new S6.7 (coverage and measured sizes), acceptance including the measured
  sizes (line 443). "Sprint 6b" (line 449) with S6.3, S6.4 (adds truncation disclosure),
  new S6.8 (efficient ranking qualified against 6a's peeling), own acceptance and
  coherence review. Roadmap rows 6a/6b share the original 5–7 days (no new estimate
  invented).
- **P5 Formative session.** Section 5 (line 177) and Sprint 5 card (line 411): one
  person, 30 minutes, synthetic data, fixture route comparison and TRACE-01 ledger, the
  three questions, dangerous misunderstandings as Sprint 7 scope input, product owner at
  session 2, formative, Sprint 9 sessions unchanged.
- **P6 Adzuna.** Sprint 3 S3.3 (line 329): optional, conditional on credentials under
  `NESSA_HOME` before the acquisition backend starts.
- **P7 Risks.** Section 12 (lines 766–767): "Human review becomes the bottleneck" and
  "The numerical core is unexercised on real, reviewed options before Sprint 9".
- **P8 Version.** Header (line 5) v1.1 dated 28 October 2026, based on spec 1.3; change
  note in "How to use this plan" (line 31); section 12 names spec 1.3 as the authority
  (line 740).
- Consequential edits, for coherence with S2/P1: Sprint 7 entry (line 475: session 2
  findings; closes after session 3), S7.1 truncation lead (line 483), Sprint 7 acceptance
  (line 501: session 3 is the human part), S8.5 (line 525: coverage and pack dates in
  exports), section 11 OPT-1 row (line 720), TIME-1 row sprint list "6a".

## Task file

- **T1 Task 7b** (line 479): curation of the 33 pages for P01–P05 under R3 with the Task 7
  pipeline, labels, template families and splits (OI-09), pack build with every record
  `proposed`, file format and validator, the session 2 package. Tasks 10 (line 581) and 12
  (line 636) consume the pack; Task 8 (line 526) consumes the 20 postings; Task 11's
  acceptance gains the real option set (line 623, TEST1-14).
- **T2 Dependency rules and suggested order** (line 166 section): 11 rules, the suggested
  order "6b → 6c → 7 → 7b → 9 → 11 → session 2 → 10 → 12 → 8 → 13a → 13b → 14 → 15 → 16",
  session 1 placement, sequential execution of the "∥" pairs, sprint reviews in run order.
- **T3 Preconditions**: a `**Preconditions:**` line on all 14 remaining cards (6b, 6c, 7,
  7b, 8, 9, 10, 11, 12, 13a, 13b, 14, 15, 16); R10 states the "blocked: awaiting session N"
  rule.
- **T4 Task 13 split**: `## Task 13a:` (line 657, measured coverage sizes in its report,
  OPT1-16) and `## Task 13b:` (line 684, writes `sprint-6.md` for 6a and 6b).
- **T5 Scope notes**: Task 7 (line 447: reduced S3.6, S3.5 is Task 8, corpus moves to 7b,
  OI-09 moves to 7b, R9); Task 8 (line 534: after Task 11, consumes the pack).
- **T6 Rulings**: R4 amended (line 107; credentials still absent, conditional added), R9
  (line 140), R10 (line 149).
- **Controller rulings**: Task 6b (line 344) per S3; Task 6c (line 384) with V-01, V-03,
  V-04, V-05, V-06, V-09, V-10, S0-V03, S0-V04, S0-V06, S0-V07 (Routes), composition
  corrections and recapture, and the `next` exception removal; parallel marks run
  sequentially; headings keep `## Task <id>:`. Checked with the `make-brief.sh` awk
  logic (run to stdout, nothing written): every ID 6b, 6c, 7, 7b, 8–12, 13a, 13b, 14–16
  extracts its own card, "13" extracts nothing, and the shared preamble still ends at
  `## Task 1:`.

## ADR 0008

`docs/adr/0008-option-pack-order-and-review-schedule.md`: status Accepted (D1–D3
confirmed 2026-10-28); links the handover; eight decisions (pack, order and split,
sessions, D3, OPT-1 disclosure, formative session, Adzuna, the two controller tasks); "What
does not change" (handover section 6); consequences. It states that decision 4 supersedes
the last two sentences of ADR 0007 decision 6, and that Task 6b amends ADR 0007 (not
edited here, per the rules).

## Register (T7)

- New rows: OPT1-15 (truncation disclosure), OPT1-16 (measured coverage sizes, T13a);
  OPTN-08 (pack labelling), OPTN-09 (proposed-state rule), OPTN-10 (the pack); TEST1-13
  (live versus reviewed scoring), TEST1-14 (checker on P01's real option set); REC1-11
  (D3, T6b); H-13 (formative session, session 2); "Human review sessions" table in
  section 6 (line 645).
- Amended: H-01 (Sprint 7 at session 3), H-06 (session 1 policy plus a person for pages
  outside the classes), H-07 (Sprints 4–5 at session 2), H-12 (held at session 1);
  TEST1-09 and OUT1-10 owners (T7b for labels); every T13 owner cell now names T13a or
  T13b (41 cells); owners table gains T6b, T6c, T7b, T13a, T13b and keeps T13 as a
  "split" note; the authority line names spec v1.3 and plan v1.1.
- Checks: 366 ID rows, no duplicate ID (scripted); no ID renumbered; statuses only from
  the allowed set; no requirement text relaxed.

## Section 9 checklist

- [x] Spec v1.3: S1–S3 applied as section 1 directs (D1, D3 confirmed); section 22 has the
      v1.3 table; nothing else changed. Evidence: spec lines 5, 50, 255, 628, 630, 801,
      1177, 1294; `git show 3d2f377 --stat` = 1 file, 20+/4−.
- [x] Plan v1.1: P1–P8 applied; roadmap has the "Human review hours" column (line 183);
      Sprint 3 (329–339), 4 (375), 5 (383–411), 6a (417) and 6b (449) cards updated.
- [x] Task file: T1–T7 applied (T7 in the register); dependency rules and suggested order
      stated (line 166 section); preconditions in every remaining card (14 cards).
- [x] ADR 0008 exists, marked Accepted because no decision was unticked, and links the
      handover.
- [x] Register rows added or amended per T7; IDs unique (366 rows, 0 duplicates); no row
      relaxed (see decision 4 on H-06).
- [x] No change outside those documents; `git status` clean apart from the four commits.
- [x] This report: D1, D2, D3 applied as confirmed; no conflict found (below).

## Conflicts (handover section 0, item 4)

None found. Checked each change against the section 1 invariants and ADR 0001:
- The pack is a permitted immutable public evidence pack (spec section 11 already allows
  these); live research stays workspace-private, so "no personal data crosses
  workspaces" holds; nothing fills a live field; unknown stays unknown.
- S2 strengthens "a truncated search is not infeasibility"; no rule changes.
- D3's explanation commits nothing, quotes only verified spans, makes no readiness or
  affordability claim, and failure stays observable.
- Order and the Sprint 6 split change sequence only; the dendrite, layers and sliders stay.

Watch item, resolved by interpretation rather than reported as a conflict: read
literally, the handover's reduced S3.6 list leaves out the pinned AI-evidence imports.
Dropping them would leave register rows AIR1-03, AIR1-07, AIR1-11 and TAX1-07 without an
owner and would be an L0 adaptation ADR 0001 does not list. The reading I applied keeps
them; see decision 1.

## Decisions I made

1. **S3.6 keeps the pinned AI-evidence and mapping imports.** The reduction applies to
   the assessment pipeline: records are entered as data, a model proposal can only be a
   `proposed` record (AIR1-04), and nothing real publishes without a reviewer (H-10).
   Plan line 335, Task 7 scope notes, ADR 0008 decision 2. **Controller to confirm.** If
   the intent was to drop the imports, that relaxes four register rows and needs an ADR
   0001 adaptation.
2. **"The same catalogue" (D1) means the same record contract, workspace-private, never
   the shared pack.** This keeps spec section 11 ("user research is not reused for other
   testers") and the cross-workspace invariant. Recorded in spec section 11, plan section
   9, R9, OPTN-09 and ADR 0008 decision 1.
3. **Session 2 also precedes Tasks 10, 12 and 8.** Their live-versus-reviewed scoring
   needs reviewed values, which only exist after session 2. The handover's suggested order
   already places them after session 2; I made it an explicit dependency rule.
4. **H-06 form change.** Per P1, H-06 becomes a session 1 rights policy against which
   agents classify pages. To keep R2, a person still reviews any page outside the
   permitted classes or not clearly within one. This is the one gate whose form changes,
   as P1 directs. R2's text is unchanged.
5. **Plan S2.7 added for D3.** The task file may only slice the plan, so Task 6b needs a
   plan deliverable to slice. Sprint 2 gains S2.7 (plan line 303).
6. **Session package and recording owners.** Task 7b and Task 11 prepare the session 2
   package. Tasks 10, 12, 8 and 14 transcribe the product owner's own record of the
   sessions into their reviews. R10 says only that record establishes an outcome.
7. **Sprint 6a/6b estimates.** The rows share the original 5–7 days. No per-part estimate
   is invented. Human review hours for Sprints 0–2 are "done, not timed"; Sprints 8–9 are
   "not estimated".
8. **13a/13b ownership split.** T13a owns enumeration, pruning, peeled layers, coverage,
   oracle, determinism of complete runs and measured sizes. T13b owns the disk archive,
   caps, child process, cancellation, efficient ranking and the benchmark. Rows that span
   both name both.
9. **The handover's "section 5 of the register"** is the human-gates section, which is
   numbered 6 in the register. The sessions table went there.
10. **Register header authority line updated** to spec v1.3 / plan v1.1. It is one line
    and not a row, changed so the register does not cite superseded versions.
11. **Task 6c's `CLAUDE.md` step** is phrased as "propose the edit for the user's approval",
    because `CLAUDE.md` line 109 names the exception and past `CLAUDE.md` changes were
    user-approved.

## Not verified

- No checks were run beyond the document checks above (`make check` is not affected by
  documents-only changes and was not run). No live calls, no subagents.
- Adzuna credentials were not inspected in `NESSA_HOME` (not reading secrets). R4 relies
  on the handover's verified state that none exist.

## Fix round 1

Source: `plan-update-review.md` (Important 1–2, Minor 1–6) and the controller's rulings.
Commit `f360a86` on `l0-local-release` changes 4 files: the task file, ADR 0008, the plan
and the register. The spec is unchanged. Not pushed; `git status` is clean. Line numbers
below are after the fix.

| Finding | Change | Location |
|---|---|---|
| I1: no task turns session 2's review into a reviewed pack | New `## Task 7c: Sprints 3–5 — publish the reviewed option pack`. It applies the product owner's H-07 record, transcription only: accepted → `review_state: reviewed` with reviewer and date; rejected left out; corrections span-cited; undecided stay `proposed`. It publishes a new dated, versioned pack validated by the 7b validator, keeps the earlier version unchanged, updates OI-08 and each page's `label_review`, and hands the version and hash to Tasks 10, 12, 8 and 13a. Dependency rules 6, 7, 9 and 10. Suggested order now "… 11 → session 2 → 7c → 10 → 12 → 8 → 13a …". Preconditions of Tasks 8, 10, 12 and 13a now name Task 7c, and their bodies say "the reviewed version Task 7c published". Task 7b hands its answers to 7c. R10's session 2 bullet names 7c. ADR 0008 updates decision 1 *Use*, decision 2 *Order*, decision 3 session 2, decision 8 and the consequences (two pack versions). Plan updates order step 5, the section 9 pack paragraph and the section 10 session 2 row. Register adds a T7c owner row and updates OPTN-10 (reviewed version: text extended, owner T7c), TEST1-09, TEST1-13, OUT1-10, OPT1-16, H-07 and the session 2 row of the sessions table | tasks:537–567, 188–201, 526, 571, 634, 689, 713, 729; tasks:166; adr0008:59–70, 72–76, 103–107, 154–160, 181–185; plan:212, 637, 692; reg:70, 194, 263, 325, 329, 490, 638, 656 |
| I2: Task 16 does not wait for Tasks 8, 10, 12 | Rule 13: Task 16 after 6b, 6c, 7, 7b, 7c, 8, 9, 10, 11, 12, 13a, 13b, 14 and 15, and after sessions 1–3. Task 16's Preconditions say the same. The ADR 0008 order bullet and the register sessions intro also say it | tasks:198–199, 809–812; adr0008:72–76; reg:651 |
| M1: Task 9 independent of 7b, yet loads its format | Rule 3: Task 9 after Tasks 7 and 7b; the handover's "7b ∥ 9" runs 7b first. Task 9's Preconditions name 7b's format. ADR 0008 decision 2 says why | tasks:183–185, 607–608; adr0008:77–80 |
| M2: Task 6b's "last two sentences" | Task 6b names the ADR 0007 decision 6 title and its last sentence, each by quotation, and keeps the `replaces` sentence. ADR 0008 decision 4 quotes the same two parts | tasks:390–394; adr0008:128–131 |
| M3: S0-V05 misattributed; Roles findings not in Task 8 | Task 6c: the Roles app parts of S0-V05, S0-V07 and S0-V08 are Task 8's. The composition note now says Task 6 fixed S0-V01, S0-V02 and S0-V08 in You and applied S0-V05's lesson to the slate. Task 8's deliverables list S0-V05, S0-V07 (Roles) and S0-V08 (failed Roles). ADR 0008 decision 8 notes it | tasks:430, 432–434, 590–595; adr0008:158–159 |
| M4: no owner transcribes H-12 | R10, session 1: the first task dispatched after session 1 transcribes H-06 (register, `corpus/README.md`) and H-12 (ADR 0007 checklist, register), Task 8 at the latest. Task 8 does it if no earlier task has. Register H-12 and the session 1 row say so; ADR 0008 decision 3 too | tasks:161–163, 600–602; reg:643, 655; adr0008:105–106 |
| M5: R2 lacks the R10 cross-reference | R2 adds "(after session 1, agents classify pages against the person's rights policy; a page outside it stays with a person; R10)"; the rest of R2 is unchanged in substance and was reflowed | tasks:95–102 |
| M6: ADR 0008 names plan "section 1" | Consequences now read "the preamble: header, 'Delivery envelope' and 'How to use this plan'; sections 5, 6, 9–12; …" | adr0008:174–176 |

Checks run after the fix:
- An awk replica of `make-brief.sh`, run to stdout only, extracts each of 6b, 6c, 7, 7b,
  7c, 8–12, 13a, 13b and 14–16 with exactly one Preconditions line each (16 cards
  including Task 6, which has none). "Task 7" does not swallow "Task 7c".
- Register: 366 ID rows, 0 duplicate IDs. No ID renumbered, no status changed, no
  requirement relaxed. OPTN-10's text is extended only.
- `git status` is clean after `f360a86`.

### Section 9 checklist (re-ticked after fix round 1)

- [x] Spec v1.3: S1–S3 applied as section 1 directs; section 22 has the v1.3 table; nothing
      else changed. Untouched in fix round 1.
- [x] Plan v1.1: P1–P8 applied; roadmap has the human review hours column; Sprint 3, 4, 5,
      6a and 6b cards updated. The fix adds only the reviewed-pack publication (plan:212,
      637, 692).
- [x] Task file: T1–T7 applied; dependency rules (now 13) and suggested order stated;
      preconditions in every remaining card (15 cards, Task 7c included).
- [x] ADR 0008 exists, Accepted (no unticked decision), links the handover; updated for 7c,
      the release dependency, the 7b-then-9 order and the ADR 0007 quotation.
- [x] Register rows added or amended per T7 and the fix; IDs unique (366, 0 duplicates); no
      row relaxed.
- [x] No change outside those documents; `git status` clean after commit `f360a86`.
- [x] Report: D1, D2, D3 applied as confirmed. Still no conflict with an invariant or
      ADR 0001; the S3.6 reading (decision 1) was accepted by the controller.
