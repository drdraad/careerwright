# Controller state (for the controller, not for implementers)

Moved here from `docs/plan/l0-sprint-tasks.md` on 1 November 2026 (the lean clean-up, the
product owner's yes), word for word, so briefs stop carrying controller state and history.
`planning/make-brief.sh` never copies this file into a brief. It holds:
- "Order, dependencies and dispatch preconditions": the dependency rules (cards cite them as
  "rule N") and the suggested order.
- "Current position and next tasks", as it stood on 1 November 2026. The live ledger,
  `planning/progress.md`, is newer where they differ.
- Task A1's card (finished: approved 2026-10-31).
- "Superseded rulings": the process wording that "R12–R17 How we build and review (current)"
  in the sprint tasks file replaced.

Since the move: the plan's v1.1 to v1.5 orders ("Order from here (v1.5)" and the rest) are in
its "Revision history" appendix; only the v1.6 order stays in its section 6. Superseded
numbers in the text below (two implementers, R15) read as R12–R17's current rules. The only
edit to the moved text is one link to the archived assessment handover.

## Order, dependencies and dispatch preconditions (plan v1.6, ADR 0008)

Execution: from plan v1.5, up to two implementers at once, on disjoint modules (R15). Each
remaining card's **Parallel** line names the tasks it may overlap. Until v1.5 the
controller ran one implementer at a time; where the assessment handover
(`docs/plan/archive/l0-assessment-handover.md`) marked tasks as parallel (∥), they ran one after the
other.

Dependency rules (rules 1–6 are met; rules 7, 9–13 and 15 are as amended in plan v1.5, and
rules 7, 11, 13, 15 and 16 again in plan v1.6; rules 16–18 came with v1.5, and rules 19 and
20 with v1.6):

1. Task 6b after Task 6 (it extends Task 6's discovery). By controller ruling, Task 6c
   follows 6b and Task 7 follows 6c; neither depends on 6b's code.
2. Task 7d after Task 7, and Task 7b after Task 7d. Task 7b uses the Task 7 acquisition
   pipeline; Task 7d fixes its cancellation lock order before the pipeline runs further
   (plan v1.2).
3. Task 9 after Tasks 7 and 7b: its outcome mappings cite Task 7's SourceClaim spans, and it
   loads the pack in the format Task 7b defines. The handover's "7b ∥ 9" therefore runs 7b
   first.
4. Task 11 after Tasks 9 and 7b (its acceptance runs on the pack's P01 option set).
5. Session 2 after Task 11.
6. Task 7c after session 2 (it applies the product owner's H-07 record to the pack).
7. Task 10 after Task 7c, Task 6d and session W2 (and Task 6f, which comes before session W2,
   plan v1.6). Task 12 is split in plan v1.5: Task 12a (the stored planning inputs,
   backend) after Task 7c and after Task 13a is integrated (rule 10); Task 12b (the Options
   chapter) after Tasks 12a and 10 and session W2, and from plan v1.6 after Tasks 12c and 7f
   (the tuition fee loan, and the school-leaver option pack it reads; rules 19 and 20).
8. Session 1 before Task 8, and before any page body is retained beyond the classes it
   permits (held 2026-10-28).
9. Task 8 after Task 7c, session 1, Task 15 and the end-to-end session (plan v1.5: Roles
   comes after the decision path, and the end-to-end session may still reshape L0).
10. Task 13a after Task 7c (the reviewed pack's instances). Task 13b after Task 13a, its
    scope sized from Task 13a's measured sizes, and after Task 12a is integrated. The
    worktree track (plan v1.5): Tasks 13a, then 12a, then 13b, one at a time in the
    worktree, each started after the last is integrated. Task 12a changes the planning
    rules that 13a's oracle and 13b's solver read, so none of the three overlaps another.
11. Task 14 after Tasks 13b, 12b and 12c (plan v1.6) and session W2, with session 2's H-13
    record as a scope input; it closes on its own checks (session 3 is merged into the
    end-to-end session).
12. Task 15 after Task 14: slice 15A first, then 15B.
13. Task 16 after every remaining task (W2E, 6d, 3b, 6e, 12a, 13a, 13b, 10, 12b, 14, 15,
    7e, 8 and M, and from plan v1.6 6f, 12c and 7f) and after sessions 1, 2, W1, W2, the
    school-leaver pack session and the end-to-end session: release qualification needs all
    six chapters.
14. Task 17 after Task 16 (plan v1.3): the manual describes the qualified candidate, and its
    small fixes are re-qualified on top of it.
15. The world (plan v1.4, amended in v1.5 and v1.6): Tasks W1 and W2's slices W2A, W2B and
    W2C part 1 are done; Task W2E closes Task W2 and Sprint W. Session W2 after Tasks W2E,
    6d, 3b, 6f and 6e. The interface tasks (10, 12b, 14, 15, 8 and M) wait for session W2;
    the backend tasks (12a, 13a, 13b, 12c) never wait for a session.
16. The role space and live sessions (plan v1.5, amended in v1.6): Task 6d after Task W2E.
    Task 3b has no task dependency. Task 6f after Task 6d (plan v1.6: it changes the same
    first question). Task 6e after Tasks 6f and 3b.
17. Options for any target (plan v1.5): Task 7e after Tasks 15 and 12b; it may start
    while the end-to-end session is awaited.
18. The end-to-end session after Task 15. Task M after the end-to-end session and Task 8.
19. The tuition fee loan (plan v1.6): Task 12c after Tasks 12a and 13b are integrated. It
    never waits for a session. It runs in the worktree before Tasks 7f, 12b and 14, and
    never beside 12b or 14: all three change `careerwright/planning`.
20. The school-leaver option pack (plan v1.6): Task 7f after Task 12c, in the worktree. Its
    second half (publishing the reviewed version) after the school-leaver pack session.
    Task 12b after Task 7f.

Suggested order (plan v1.6; the plan's section 6 "Order from here (v1.5)" gives each
remaining v1.5 step's scope and agent hours, and "Order from here (v1.6)" the new steps), in
two tracks (R15):
- The main tree: 6d (its last slice) → 6f → 6e → session W2 → 10 → 12b → 14 → 15 (15A,
  then 15B) → the end-to-end session → 7e → 8 → M → 16 → 17 → the final review.
- The worktree, beside it: 12c → 7f (its first half, the school-leaver pack session, then
  its second half), each started after the last is integrated. Task 12c may overlap 6f, 6e
  and 10; Task 7f may overlap 6f, 6e and 10. Tasks 12b and 14 never overlap 12c: all three
  change `careerwright/planning`. Task 12b starts after 7f is integrated.
Backend tasks fill any wait for a session.

From 2 and 3 November 2026 (the product owner): Task W2F (the You chapter, fixed from session
W2) comes before 10B, 12bB and 14B; the world's role names become clickable after those three
screens. **A design system pass** (the product owner, 3 November 2026: "you seem to lack a
coherent, consistent design system"): consult the `frontend-design:frontend-design` skill for
one coherent, consistent design system across every chapter. It MUST come after every chapter
module in the current plan is built (10B, 12bB, 14B, 15, 7e and 8), and before Task M, whose
moments build on it. Not before.

**V1, the product owner's yes (3 November 2026):** "Make V1 the five screens the demo shows
(You, Skills, Options, Routes, Plan), and build the Roles map, option research for any role,
and the moments animation straight after V1 instead of before it?" Yes. The order from here:
10B and 12bB (in parallel) → 14B (after 12bB's shared parts) → 15 (Plan) → the end-to-end
session → the design system pass (on the five V1 screens) → Task 16's release qualification
for V1 (five chapters; Roles is after V1, so rule 13's "all six chapters" reads as the five V1
chapters for V1) → 17 (the manual) → V1. Then, after V1: 7e → 8 (Roles) → M → Task 16 again
for the full L0 → the final review. Nothing is dropped, only moved later.

History: the v1.5 order was, in the main tree, Task A1's documents and the W2C part 1
re-review → W2E → 6d and 3b → 6e → session W2 → 10 → 12b → 14 → 15 → the end-to-end session
→ 7e → 8 → M → 16 → 17 → the final review, and in the worktree 13a → 12a → 13b (all three
done by plan v1.6). The v1.4 order (after session 2) was W1 → session W1 → 7c → W2 →
session W2 → 10 → 12 → 8 → 13a → 13b → 14 (closes after session 3) → 15 → 16 → 17, with backend tasks (7c,
13a, 13b) running while a session was awaited and interface tasks waiting for session W2.
The v1.1 order was 6b → 6c → 7 → 7d → 7b → 9 → 11 → session 2 → 7c → 10 → 12 → 8 → 13a →
13b → 14 (closes after session 3) → 15 → 16 → 17. Session 1 could be held at any point before
Task 8; holding it before Task 7b let 7b classify the pack's rights itself instead of leaving
every page "pending human rights review".

Dispatch preconditions: every remaining task card starts with a **Preconditions** line
naming the tasks and the human sessions it waits for (R10). A session that has not happened
blocks dispatch; it is never assumed, worked around or self-certified (R2).

Sprint reviews follow the order: the task that finishes a sprint writes its review, so
`docs/reviews/sprint-3.md` (Task 8) comes after `sprint-4.md` (Task 10) and `sprint-5.md`
(Task 12b), and `sprint-6.md` (Task 13b) covers 6a and 6b. From plan v1.5, `sprint-w.md`
is Task W2E's and `sprint-m.md` Task M's. Each review states the order it ran in.

## Current position and next tasks (2026-11-01, plan v1.6)

**Complete and reviewed:** Tasks 1–6, 6b, 6c, 7, 7d, 7b, 9, 11, 7c and W1; Task W2 (slices
W2A, W2B and W2C part 1) and Task W2E, which closed Sprint W (`docs/reviews/sprint-w.md`);
Task A1's approved changes, applied to the documents; the worktree track, Tasks 13a (the
route search core), 12a (the stored planning inputs) and 13b (the search as a bounded run),
each integrated; Task 3b (live sessions ready on Muse Wonder), integrated; and Task 6d's
slices A (facts instead of sentences; each target stored once) and B (the title flow over
ESCO and the ONS index). **Held:** sessions 1, 2 and W1. The ledger
(`planning/progress.md`) has every commit range and ruling.

**Finishing:** Task 6d slice C (seniority and industry, ESCO's list named as ESCO's, "not
part of my job", pasted CV text deferred), in the main tree, built to dc68d79; its last
commit and its review follow. Task 3b's first live run of the real-data path waits for the
product owner to paste their own key into the app; it joins session W2's preparation (Task
6e).

**Approved:** Task A1, the whole-solution audit (`docs/reviews/l0-audit-2026-10-31.md`; the
decisions page `docs/reviews/l0-audit-2026-10-31-summary.md`), by the product owner on
2026-10-31: "Approved - proceed. Where subagent work can be done cleanly in parallel, do so
but coordinate well to avoid them causing conflicts. Yes, I have 5 people who can try the
app before release." Its decisions 1 to 8 are all yes.

**The product owner's direction (2026-10-31), in their words:**
- "The visuals are important, but they must be subservient to having a practical, useful
  product."
- "I want to check that the development plan is still sensible, and get us back on track
  with the sprints, even if we have to refactor some of them to ensure coherency and
  pragmatism."
- "One thing that is really important to me is that we aren't limited to a prefilled list
  of roles - the real world is much more complex than those standardised job lists, and I
  want to avoid the frustration of your ideal job not appearing as an option to select.
  This is where deep research and LLMs have a part to play to fill out the "role space"
  more fully. I want it to feel like you have an omniscient career coach who knows all
  possible jobs that could fit you."
- "We can also start being a bit more generous with token use in human testing - I would
  like to use muse wonder for this."

**The product owner's decisions since plan v1.5:**
- 31 October 2026: leave the route search's disk-backed archive and its separate child
  process out of L0, on Task 13a's measurements (Task 13b's card; specification section 22).
- 1 November 2026: the unexpected connection is "Always a plain line": shared skills are a
  plain fact about two roles, never a discovery moment (ADR 0015). Task M picks or drops the
  Roles chapter's moment.
- 1 November 2026, in their words: "NB: I don't want to over-rely on existing skills in the
  process. Many users will be final year school students who have never had a job before."
  A walk through the whole path as a Year 13 student with no job (the controller's
  `planning/audit-no-job-yet.md`) found eight problems and ten
  decisions. They answered "A and B, not #10" (yes to decisions 1–9, no to 10) and approved
  where each fits ("go"). Plan v1.6 applies them: below, and in the specification's section
  22.
- 1 November 2026: the root folder moves to `/Users/darianraad/Code/careerwright`, and the
  worktrees to `/Users/darianraad/Code/careerwright-wt/<id>`, at a clean point with no agent
  running (the product owner's request; the ledger's ruling).

**Where the school-leaver decisions go** (plan v1.6):

| Decision | Goes to |
|---|---|
| 1. School students aged 17 and 18 are in scope | The specification's section 22; Task 16 checks the rules for young people's data before any real student uses Careerwright (H-15) |
| 2. "I haven't had a job yet" beside "Skip for now" at the first question | New Task 6f |
| 3. Two optional answers: what you're doing now, and qualifications (achieved or expected) | Task 6f; Tasks 10 and 12b read them as entry facts, an expected grade never met |
| 4. An opening question that works without a job | Task 6f, with the walk's word pass; the final words are the product owner's at session W2 |
| 5. A synthetic school leaver and 4–6 evaluation cases | Task 6e; she is one of session W2's people |
| 6. A tuition fee loan paid straight to the university is a loan to repay, not the student's own money | New Task 12c (the checker, the independent oracle written fresh, the search's rules); Tasks 12b and 14 show it |
| 7. A degree longer than the 24-month model | Task 14: words only, no planning change |
| 8. A reviewed school-leaver option pack | New Task 7f, with one short review session (R10); Task 12b reads it |
| 9. Childline in the calm support panel | Task 6f |
| 10. Hours that change on a date ("free from September") | No: a known L0 limit (plan section 1; specification section 22) |

The walk's other lines, approved with the placement: Task 10 shows no empty "usual in your
role" panel without a role; Task 12b's checkpoint works for someone not working and shows
each scheme's age rule; Task M answers a person with no job (the strength's horizon, the
first answer's ignition); Task 7e's research names apprenticeships, degrees and their
funding; Task 8 marks apprenticeship listings and takes a pasted apprenticeship advert.

**Running now** (R15):
- Task 6d slice C, finishing (main tree).
- This plan update, plan v1.6 (documents only, in the worktree `wt-plan`).

**Next, in order** (the suggested order above): in the main tree, 6d slice C's review → 6f →
6e → session W2 → 10 → 12b → 14 → 15 → the end-to-end session → 7e → 8 → M → 16 → 17 → the
final review; in the worktree, 12c (it may start beside 6f) → 7f (its first half, the
school-leaver pack session, then its second half), each after the last is integrated. Tasks
6f and 12c start after the folder rename (the ledger's ruling).

**Where the remaining Task W2 work went** (plan v1.5; all of Task W2E's rows are done):

| Item | Goes to |
|---|---|
| W2C part 1's scoped re-review | Done; its open findings went to Task W2E |
| On a phone, the world band puts a long view's first decision a scroll away | Task W2E: on a phone the decision comes first |
| "Help me explore instead" drops keyboard focus | Task W2E |
| The moving-and-still identical-words test covers only the fixture workspace | Task W2E |
| The first answer's ignition | Task M |
| The type-ahead's closest titles, asked as "Careerwright couldn't match that title in ESCO. Is it one of these?" | Task 6d, with "None of these is my job" leading to the person's own words |
| The unexpected connection lit in the world | Dropped (the product owner, 1 November 2026: "Always a plain line"); shared skills in words on each suggestion → Task W2E, done |
| The overlooked strength's proposal and confirm step; `held_back` on a support turn; its destinations on the horizon | Task M, all together |
| "Usual in your role, not confirmed yet" | Task 10 |
| Suggestions drawn as rings; "Make this a target" previewing its destination | Task M |
| The world's requirement family in the register; the Sprint W acceptance | Task W2E; the frame part → Tasks M and 16 |
| The frame re-measure (warn the product owner first: it opens a window) | Task M, then Task 16 |
| Plain phrases for the route preview's "Economic cost" and "Direct spending" | No longer needed: the demo route preview leaves the person's path (Task W2E); Task 14 writes plain words for real routes |
| ADR 0014 decision 7's strip wording | Task W2E |
| The phone openings list one per line, with stale and unknown captures | Task 8 |
| Session W2's package and sheet; `docs/reviews/sprint-w.md` | The short session's package → Task 6e (R10); `sprint-w.md` → Task W2E |
| Session W2's old sheet: the slate's provisional rules, the work-style and too-general rules, main names and hyphens, the specificity order and each note's words | Replaced by the five questions (R10): the slate's word rules are frozen (R11) and judged on real examples |
| The discovery prompts, untested live | Task 3b's first live run through the app, then session W2 |
| Typography and colour (Source Sans 3; leaf green beside destination orange) | Two of session W2's five questions |
| Layout: the tablet strip; Send as the bright action | Task W2E; the helper lines, the sketch's disclosure and the tabs are judged by session W2's first question |

**Parked for the final review** (unchanged): the earlier parked items (ledger lines starting
"Parked"). Two of them are now Task 6d's design input: titles that ESCO writes with "&" or
accents don't match their plain spelling (`concept_key`, a migration-defined key), and the
three chosen-occupation normalisations, which one stored target record replaces.

## Task A1: whole-solution audit, coherence and pragmatism (the product owner's request, 2026-10-31)

**Status: approved by the product owner on 2026-10-31** ("Approved - proceed"). The report
is `docs/reviews/l0-audit-2026-10-31.md`, with its appendices and the decisions page. Its
approved changes are applied in plan v1.5, this file, ADRs 0003 and 0006–0014, the new ADR
0015, the register, the specification's revision record (section 22) and `CLAUDE.md`.

**Preconditions:** none. Read-only on product code. It writes a report and proposes changes
to the development plan, this file and, where needed, the specification and `CLAUDE.md`. Each
change waits for the product owner's approval.

Answer four questions, with evidence:
1. **Intent:** does the solution as built and planned still deliver the original design's
   intended functionality? Map each specification capability, end to end, to built, planned
   or drifted, and name each drift.
2. **Coherence and pragmatism:** is it one clear product? Check that complexity earns its
   keep, that the honesty invariants are applied in proportion, and that the world serves the
   work, not the other way round (the product owner's direction above). Use the review
   history as evidence: where fix rounds went, and what they bought the person.
3. **The plan:** is the development plan still sensible? Propose re-ordering, merging,
   cutting or refactoring sprints and tasks so the practical, useful product comes first.
   Include the Sprint W gate (session W2 before Tasks 10, 12, 8, 14 and 15) and the remaining
   W2 work above.
4. **Muse Wonder for human testing:** `muse-wonder-1.0` is in
   `identity/model_registry.py`, and ADR 0003 left it unselected. Say where it is used, the
   budget per session, how each call is ledgered (R5), and what ADR 0003, the plan, the
   register and the test-model safeguards need.

Deliver:
- `docs/reviews/l0-audit-2026-10-31.md`: findings, each with evidence and a recommendation.
- The proposed plan changes.
- A one-page plain-words summary for the product owner. List only the decisions that are
  theirs, one sentence each, saying what "yes" does.

Nothing in the plan changes until they approve.

Acceptance: every specification capability is mapped. Every recommendation cites evidence.
The product owner has the summary.

## Superseded rulings

Moved from the sprint tasks file's standing rulings on 1 November 2026, when R12 to R17 were
merged into "R12–R17 How we build and review (current)". Every clause of R12 to R17 that
still holds stays there word for word; only what is below was superseded, each with what
replaced it.

- R12 Evidence before polish (plan v1.2). From Task 7b to session 2 (Tasks 7b, 9 and 11)
  the critical chain took priority. A refactor or hardening that no failing check, reproduced
  defect or Global Constraint requires went to the final-review list in the progress ledger,
  never into those tasks. From plan v1.5 it is permanent, as R13.
  *Replaced by R13 (kept word for word in the current ruling).*
- From R14 (Review rules):
  - Bound loops by kind of finding. When one kind comes back in two re-reviews in a row,
    the next step is a rule, a fail-safe or a one-line question to the product owner, never
    another patch. Wording, matching and visual work stop at three rounds; security, money
    and data keep five.
  *Replaced by R16's "One fix round at most" (a second review runs only for a Critical
  finding).*
- From R15 (Parallel work), its first sentence:
  - Up to two implementers at once: one in the main tree, one in a git worktree
    (`/Users/darianraad/Code/careerwright-wt/<id>`, branch `wt-<id>`), on disjoint
    modules.
  *Widened to three by R16 and to four by R17. The worktree path was
  `/home/user/careerwright-wt/<id>` in the cloud (1–2 November) and is this one again on
  the Mac from 2 November.*
- From R15, its last clause as first written (the branch name only changed since):
  - The controller integrates a worktree by fast-forwarding `l0-local-release` after the
    implementer rebases onto it; an implementer never moves `l0-local-release`.
  *`l0-local-release` was merged into `main` on GitHub; the integration branch is now
  `claude/confident-ramanujan-ux3saw`.*
- From R16 (Speed):
  - **Full checks once per piece.** Implementers run `make check` after each change and
    `make acceptance` once, at the end of the piece (after its fix round, if any).
  *Replaced by R17's "`make acceptance` runs once per batch of integrated halves": the
  controller runs it once per batch, and implementers never start Docker. R16's "A flaky failure is re-run once; a second failure is a
  finding." stays.*
  - **Up to three implementers at once,** on disjoint modules: one in the main tree and up to
    two in worktrees. This widens R15's two; R15's other rules stand. Each card's
    **Parallel** line still decides what may overlap.
  *Widened to four by R17. R15's Parallel-line rule stays.*

