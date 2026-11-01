# Task A1, apply: write the approved plan changes into the documents

Careerwright L0, branch `l0-local-release`, main tree `/Users/darianraad/Code/careerpathoptimizer`
(HEAD fde8e7d). The product owner approved a whole-solution audit on 2026-10-31. Your job
is documents only: write its approved changes into the plan, the task file, the ADRs, the
register, the specification's revision record and `CLAUDE.md`, so that the next
implementers' briefs (extracted from `docs/plan/l0-sprint-tasks.md` by card) are complete
and correct. No product code changes.

## Read first
1. `.superpowers/sdd/l0-sprint-tasks/implementer-contract.md`. You work in the **main tree**
   while another implementer works in a separate worktree and a reviewer reads this tree:
   commit with a pathspec only.
2. `docs/reviews/l0-audit-2026-10-31.md`, **all of it**. It is the source of truth. Sections
   4 (the proposed order and sessions), 6 (review rules), 7 (document changes, with the exact
   `CLAUDE.md` wording) and 8 (rulings) are what you apply.
3. `docs/reviews/l0-audit-2026-10-31-summary.md`: the decisions the product owner approved.
4. Appendices in `docs/reviews/l0-audit-2026-10-31/`:
   - `D-plan.md` section 4 lists edit by edit for the plan, the task file, ADRs 0007, 0008 and
     0014, and the register. **Where it differs from the report, the report wins**:
     - The report's order puts the role space (steps 1 and 2) and live sessions ready before
       a short session W2.
     - The planning inputs and the route search core run during session W2.
     - "Add an option yourself" is in Options.
     - Option research comes after Plan.
     - Roles comes after the end-to-end session.
     - The moments come last before release.
   - `F-role-space.md` sections 5 and 6: the role-space steps, their acceptance tests and the
     documents they change (spec DIV-1 note, ADRs 0006, 0007, 0009, 0010, 0012, 0014, new ADR
     0015, `CLAUDE.md`).
   - `A-specification-map.md` sections 3 and 5: the drifts to assign and the register
     findings (28 orphaned rows, stale rows).
   - `E-person-path.md` section 2 (F1–F17): the person-facing problems that the "Finish the
     You chapter" card must list.
   - `B-code-coherence.md` sections 2 and 6: the target-record seam (F5), the planning-inputs
     split (F9), sizing the route search's durable add-ons (F10), prose-free APIs (F7).
   - `G-muse-wonder.md`: the live-sessions task.
   - `C-review-history.md` section 4: the review rules behind the report's section 6.
5. The current documents you edit: `docs/plan/development-plan.md` (v1.4),
   `docs/plan/l0-sprint-tasks.md`, `docs/adr/*`, `docs/requirements-register.md`,
   `Careerwright_Product_Specification.md` section 22, `CLAUDE.md`.
6. Controller notes for the cards (gitignored; read only, don't cite them as the requirement
   in a card): `.superpowers/sdd/l0-sprint-tasks/carry-forward-task-W2C.md`,
   `carry-forward-task-W2C2.md`, `carry-forward-task-W2D.md`, `carry-forward-task-8.md`,
   `carry-forward-task-10.md`, `carry-forward-task-12.md`.

## The product owner's words (quote these verbatim where the documents record direction)
- "The visuals are important, but they must be subservient to having a practical, useful
  product."
- "I want to check that the development plan is still sensible, and get us back on track with
  the sprints, even if we have to refactor some of them to ensure coherency and pragmatism."
- "One thing that is really important to me is that we aren't limited to a prefilled list of
  roles - the real world is much more complex than those standardised job lists, and I want to
  avoid the frustration of your ideal job not appearing as an option to select. This is where
  deep research and LLMs have a part to play to fill out the "role space" more fully. I want it
  to feel like you have an omniscient career coach who knows all possible jobs that could fit
  you."
- "We can also start being a bit more generous with token use in human testing - I would like
  to use muse wonder for this."
- Approval, 2026-10-31: "Approved - proceed. Where subagent work can be done cleanly in
  parallel, do so but coordinate well to avoid them causing conflicts. Yes, I have 5 people who
  can try the app before release."

## What to write

### 1. `CLAUDE.md`
Apply the four edits in the report's section 7 **verbatim**, nothing else. The product owner
approved exactly that wording.

### 2. `docs/plan/development-plan.md` → v1.5 (31 October 2026)
- A "Version 1.5" paragraph in "How to use this plan": the directions (quoted) and the list of
  changes.
- The new order, the sessions, the release bar.
- Section 1's boundary table: roles beyond ESCO; options for any target marked not reviewed;
  the L0 deferrals the report lists.
- Section 4's practical-first paragraph and the restated phone rule.
- Section 5's rubric: scores are formative at session W2 and the end-to-end session; every
  category at least 4 at release.
- Section 6's roadmap rows and totals, from the report's agent-hour estimates and the
  sessions actually held.
- Sprint card changes: Sprint 2 gains the role space; Sprint 3 Roles moves after the path;
  Sprint 5 splits inputs from the chapter and gains "add an option yourself"; option research
  joins Sprint 3's evidence work; Sprint W closes at the You chapter; Sprints 7 and 8 lose the
  session 3 gate; a new moments sprint (M).
- Section 10's sessions table; section 11's traceability rows; section 12's risks
  (corrections and the two new risks).
- Use appendix D section 4.1 as your checklist, adjusted to the report's order.

### 3. `docs/plan/l0-sprint-tasks.md`
- **Header:** plan v1.5.
- **Global Constraint 11:** the practical-first sentence (appendix D 4.2 item 2, worded to
  match the `CLAUDE.md` edit).
- **R4:** correct it. The Adzuna credentials exist; the live qualification passed.
- **R10:** rewrite the sessions.
  - Held: 1, 2, W1.
  - Session W2: short (about 30 minutes, live, on Muse Wonder, about five questions, no score
    threshold).
  - The end-to-end session (about 1 hour, after Plan) replaces session 3.
  - Release checks: five participants are available for the task sessions (the product
    owner, 2026-10-31).
  - Keep "only the product owner's own record establishes an outcome".
  - Add that the product owner may rule that an AI check of rote items counts as their
    review; an agent never assumes it.
- **R11:** widen it to the slate's notes and matching rules. Add the sentence rule: a sentence
  the person reads says what Careerwright did or checked, never what a source or list contains;
  when exact and plain conflict, say less.
- **R12:** make it permanent for every remaining task. You may fold it into a new R13, "Path
  before polish".
- **R14, review rules:** the report's section 6, as rules the controller and reviewers follow.
- **R15, parallel work:** the product owner's approval words.
  - Up to two implementers at once: one in the main tree, one in a git worktree, on disjoint
    modules.
  - Shared documents change only in a task's last commit.
  - One `make acceptance` at a time, under a lock.
  - The controller integrates a worktree by fast-forwarding `l0-local-release` after the
    implementer rebases.
  - The task cards' **Parallel** line says which tasks may overlap.
- **The order and dependency section:** the new dependency rules and suggested order (the
  report's table). Keep the v1.4 order as history.
- **"Current position and next tasks":** rewrite it.
  - A1 approved.
  - The new order.
  - What runs now: this task, Task 13a in a worktree, and the W2C part 1 re-review.
  - Replace "Remaining Task W2 work" with where each item went (appendix D 3.2, adjusted:
    W2C part 2's type-ahead question goes to Task 6d; the strength, ignition, rings and the
    target preview go to Task M; "usual in your role" goes to Task 10).
  - Keep the parked list.
- **New cards.** Each has a **Preconditions** line, a **Parallel** line, the scope as
  observable behaviour, the acceptance in plain observable terms, and the register rows it
  closes or opens:
  - **W2E**, Finish the You chapter: report task 1. It includes the W2C part 1 re-review's
    open findings (the controller passes them in the dispatch) and E's F1, F2, F5, F7, F8,
    F10's words, F14 and F17.
  - **6d**, Your title, recognised: F's step 1, its acceptance test, the target record stored
    once (B F5), optional seniority and industry, the research's three fixes, CV paste if
    small.
  - **3b**, Live sessions ready: report section 5, appendix G. The controller runs the live
    qualification calls itself; the card says so.
  - **6e**, Research this role: F's step 2.
  - **12a**, Planning inputs: carry-forward-task-12 items 1–7, plus work rights and remote
    working.
  - **12b**, Options, split from Task 12: the checkpoint, plus "add an option yourself".
  - **7e**, Find options for this role: live course and funding research as "not reviewed"
    records, through the existing fetcher and extraction pattern.
  - **M**, The moments.
- **Revised cards:** Tasks 8, 10, 13a (an order note only), 13b (scope sized from 13a's
  measurements; caps and truncation wording stay), 14, 15 (15A and 15B), 16 and 17
  (preconditions). Mark Task A1 approved on 2026-10-31.
- The card heading format must stay `## Task <ID>: …` exactly. The brief extractor matches
  `## Task <ID>:`.

### 4. ADRs
- Amend 0003, 0006, 0007, 0008, 0009, 0010, 0011, 0012, 0013 and 0014 where the report and
  appendices say. Each amendment is a dated section "Amendment, 2026-10-31 (the product
  owner's approval of the audit)", saying what changed and why.
  - 0011 and 0013: options from "add an option yourself" and from option research are
    workspace records marked proposed (not reviewed); the planning catalogue reads them beside
    the pack; a route built on one is qualified, never an unqualified "affordable and
    feasible".
- Add **ADR 0015, "The role space"**: the layers (ESCO, the ONS coding index, the person's
  own words, researched roles); the corroboration rule; the role record; per-role spend
  bounds; the model choice; what later chapters show for such roles (F section 5's table).
- Decisions the controller or a later task settles are marked "to be settled by Task <id>",
  never invented.

### 5. `Careerwright_Product_Specification.md`
Add one dated subsection to section 22 ("L0 build decisions, 2026-10-31, approved by the
product owner"):
- the ONS coding index as an authoritative occupational source for DIV-1, and "independent"
  defined;
- options for any target as proposed records with qualified routes;
- Muse Wonder brought forward for the product owner's live sessions;
- the L0 deferrals.

No other line of the specification changes, and no invariant is relaxed.

### 6. `docs/requirements-register.md`
- Header: plan v1.5.
- Reassign every open row whose owner tasks are complete to a remaining task, or record it as
  an L0 deferral (appendix A section 5).
- VIS1-02, AIR1-08 and UI-02: industry by glyph and label.
- H-13: session 2 part 1's result, transcribed from `docs/reviews/session-2-answers.md`.
- DIV1-04: the employer-evidence half was never built; now Task 6e.
- The sessions table: W1 held, W2 short, the end-to-end session, session 3 merged.
- H-05: five participants available.
- New rows for the new behaviour, in the register's ID conventions. Each new row's owner is
  its new task.

## Rules
- Documents only, and only the files listed above.
  - Never touch `fixtures/m0`, `apps/web/src/generated`, `apps/web/src/design`, `docs/design`,
    `docs/reviews` (except nothing: leave the audit files as committed) or product code.
  - Never stage `answers-2.md` or `esco_research.txt`.
- Use Edit/Write. No scripts that rewrite files.
- Keep each document's style. Plain words where the product owner reads (the "Talking to the
  user" rules in `CLAUDE.md`). No new requirement beyond what the report and its appendices
  say; if something is undecided, say who settles it.
- Commit in coherent pieces with explicit pathspecs. For example: `CLAUDE.md` alone; the plan;
  the task file; the ADRs; the register and the specification. Each message ends with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Never push.
- Verify:
  - `bash .superpowers/sdd/l0-sprint-tasks/make-brief.sh <id>` succeeds for every new and
    revised card. Delete the brief files it writes for cards you only tested.
  - Every `## Task` heading is unique.
  - Every card has a Preconditions line.
  - `make check` passes (some backend tests read the register; run it once at the end).
- No web requests, no live calls, no Docker, no browser, no subagents. Never read `.env`,
  `~/.careerwright` or `~/.nessa`.

## Report
Write to `.superpowers/sdd/l0-sprint-tasks/task-A1-apply-report.md`:
- each file changed and what;
- where you departed from appendix D, and why (the report wins);
- every undecided point you marked for a task;
- the checks run, with their output.

Then reply with the short contract (status, commits, one-line checks summary, concerns,
report path).
