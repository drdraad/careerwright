# Lean review, 1 November 2026

You asked whether Careerwright is over-engineered, and whether the documents and process
have grown too heavy. Short answer: the product code is heavy but mostly earns it. The
paperwork around it is where the fat is, and most of it can be archived without losing a
single rule.

Nothing was changed to write this. Sizes are bytes; tokens are about bytes ÷ 4.

---

## (a) The evidence

### 1. What every agent reads before it starts

| What | Size | Who reads it |
|---|---|---|
| `CLAUDE.md` | 289 lines, 22 KB (about 5,500 tokens) | Every agent, every time (loaded automatically) |
| Brief preamble (`make-brief.sh` copies lines 1–570 of `docs/plan/l0-sprint-tasks.md` into every brief) | 570 lines, 42 KB (about 10,500 tokens) | Every implementer and every reviewer |
| Development plan, the "always read" sections 1–5 and 7–10 | about 65 KB (about 16,000 tokens) | Every implementer |
| `planning/implementer-contract.md` / `reviewer-contract.md` | 5.5 KB / 4 KB | Every implementer / reviewer |
| The task's own card | 2–6 KB | Its implementer and reviewer |

So an agent reads about 32,000 tokens of standing documents before it reads its own task.
The record holds about 195 agent runs so far (37 implementer reports, 52 fix rounds, 106
reviews and re-reviews), so roughly 6 million tokens went on these standing documents.

**What in the brief preamble is history or controller-only, not a rule an implementer needs**
(about 20 KB of the 42 KB, nearly half):
- "Current position and next tasks": 9 KB. Who is running, what is done, the finished
  Sprint W hand-off table, the school-leaver placement table. Controller state.
- "Order, dependencies and dispatch preconditions": 6.8 KB. Rules 1–6 are marked "met";
  the old v1.1, v1.4 and v1.5 orders are kept as "History".
- The finished audit task's card (Task A1, approved 31 October): 2.3 KB.
- Superseded or overlapping rulings: R12 is replaced by R13; R15's "two implementers" was
  widened to three by R16 and to four by R17, and the implementer contract still says
  three. R14 and R16 restate parts of each other. Together R12–R17 are 6.8 KB.
- Stale facts: "Environment facts" says macOS and `/Users/darianraad/...`; the work now runs
  on Linux at `/home/user/careerwright`, so every dispatch adds a "This machine first"
  override. The reviewer contract is still titled "Nessa L0".

**The development plan** (1,087 lines, 153 KB): its "How to use this plan" section carries
every version note from v1.1 to v1.6 (8.5 KB), and section 6 stacks four "Order from here"
lists (v1.1, v1.4, v1.5, v1.6), only the last of which is live. Six sprints' cards are
finished. `docs/plan/l0-assessment-handover.md` (21 KB) was fully applied in plan v1.1.

**The sprint tasks file** (2,307 lines, 162 KB): 64% of the task-card text (77 KB of 120 KB)
is cards for finished tasks. Only the current card is copied into a brief, so this costs
reading time for the controller, not every agent.

**The specification** (208 KB) is read section by section on demand. It is the authority;
leave it alone.

### 2. The `planning/` folder

348 entries, 7.1 MB. 308 are in git.

| Kind | Count | Size | Status |
|---|---|---|---|
| Task files of finished tasks (briefs, dispatches, reports, reviews, fix rounds) | 274 | 3.7 MB | History |
| Audit lenses, session 1 transcription files, the old handovers, plan-update files, carry-forward notes for finished tasks | 28 | 0.36 MB | History |
| Review diffs (`review-*.diff`, gitignored, rebuilt any time by `review-pkg.sh`) | 8 | 1.9 MB | Throwaway |
| The ledger `progress.md` | 1 | 1,154 lines, 328 KB (about 82,000 tokens); lines up to 1,208 characters | Live, but mostly history |
| Live: the two contracts, `make-brief.sh`, `review-pkg.sh`, `env-cloud.md`, `cloud-build-images.sh`, `answers-2.md` and `esco_research.txt` (the product owner's notes, never moved), `childline-checked-2026-11-01.md`, `claude-memory/`, `audit-no-job-yet.md` (the remaining cards cite it), carry-forward notes for Tasks 8, 10, 12 and W2D, `handover-2026-11-01.md`, and the files of tasks in flight (7f, 10A, 10, e2e-fix) | about 30 | — | Live |

The handover tells the controller to read the ledger's last 150 lines: 59 KB, about 15,000
tokens, each session. The older `next-session-handover.md` still says "read the ledger in
full" and points at a folder that no longer exists. Parked "final review" items are spread
over at least 20 ledger lines, so the final review has to dig them out.

### 3. `docs/`

- **ADRs:** 16 files, 459 KB. The long ones carry amendment chains: 0007 (conversation and
  support) is 1,100 lines and 91 KB with two dated amendments and six "superseded / no
  longer" notes; 0009 is 57 KB; 0015, 0012 and 0016 are 34–36 KB each, 0015 with 14
  amendment references. An agent touching discovery reads 23,000 tokens for one ADR.
- **The requirements register:** 769 lines, 386 KB (about 96,000 tokens), 486 rows, single
  rows up to 7.3 KB of narrative history. Implementers edit it in every task; 25 of the last
  160 commits touch it. Reviews found register or document over-claims in 20 of 21 reviewed
  pieces (about 86 findings): the register generates its own review work.
- **Reviews:** 21 MB, mostly 181 committed screenshots. Records: keep. Agents don't read the
  images, so they cost nothing in context.
- **Evidence:** 120 KB. Records: keep.
- **The same rule in many places:** "unknown is never zero" appears in 7 documents; "not
  run — requires human" in 8; the tuition fee loan rule in 7; the sentence rule in 4; the
  acceptance lock and commit-by-pathspec rules in both the tasks file and the implementer
  contract; most of the 13 Global Constraints restate `CLAUDE.md`. Each copy can drift, and
  reviewers then raise the drift as a finding.
- **The design mirror:** `docs/design` and its byte-identical copy `apps/web/src/design`
  (792 KB) are kept in step by a check. The plan already rules that a built chapter's
  stories replace its composition. `spikes/world` (380 KB) is still there although Task 10's
  card says to delete it.

### 4. The process

From the ledger and `planning/audit-lens-C-review-history.md`:

- **Before the speed rules (to 31 October):** 46 fix rounds over 21 reviewed pieces and 83
  reviewer passes. Three pieces hit the five-round limit (the conversation, evidence
  acquisition's first slice and the slate matching) and took 15 rounds between them, a
  third of the total. One slice ran 6 fix rounds and 12 re-reviews. About 22% of rounds
  chased wording and pattern tails that each fix re-opened, and about 30% of all findings
  were things only a reviewer would notice (register wording, tests, tidiness).
- **What the late rounds caught:** mostly wording, new escape forms and register wording.
  The truth defects nearly always surfaced in round 1.
- **Since the speed rules (1 November):** eight reviewed pieces (6e, 6f, 12c, 7f, 10A, the
  fetch proxy, the Linux stack, 3b) took one fix round each and at most one re-review.
  Every first review still found a real problem: a grant that pushed spending below £0 and
  hid a feasible route (12c, Critical); "You said" shown for answers never given and a
  failed GCSE read as passed (6f); one advert counted as two sources, and an empty jobs
  state that could lie (6e); a loan's age rule missing and a bursary called a grant (7f);
  stored words the person didn't choose (10A); a "$5 a session" cap with no session total
  (3b). **One review per piece is high value; repeat reviews were not.**
- **Rituals that cost time and caught little:** the two-half review (design and code) before
  the speed rules; fresh re-reviewers each round, each opening new kinds of finding; register
  edits in every task; "CLAUDE.md proposal" files per task; four to nine paper files per
  piece (dispatch, brief, report, review dispatch, review, fix round, re-review).
- **The full checks:** `make acceptance` runs 10–45 minutes. The ledger mentions acceptance
  85 times and hangs or flaky runs 132 times. Several runs failed on the machine, not the
  code (a bound port, a database password on Linux, a Chromium version). The speed rules
  already cut this to once per batch.

### 5. The code

Backend 51,000 lines (tests 47,000), web 26,500 lines without generated files, 46
migrations, 248 row-security statements, 8 Compose services (database, sign-in emulator,
migration job, API, worker, restricted fetch worker, edge relay, web).

Heavier than a one-person local app strictly needs, with an honest cost and benefit:

| Machinery | Where | Cost | Benefit | Verdict |
|---|---|---|---|---|
| Multi-user sign-in, row-level security, sealed keys, an edge relay | `identity/`, `docker/auth`, `compose.yaml`, ADR 0004 | Stack start-up, the Linux secrets task, long acceptance runs | The spec asks for it. Five testers' data and real API keys. Ownership checks caught real bugs | Keep, add nothing |
| A separate fetch worker with no database or keys | `careerwright/acquisition.py`, `evidence/fetcher.py` | One more service | It keeps web pages away from keys. The address check is what caught the cloud proxy problem | Keep |
| The route search, its checker (1,301 lines) and an independent oracle (697 lines) | `planning/checker.py`, `planning/search.py`, `tests/support/route_oracle.py` | Two copies of the rules to change for each new rule (12c changed both) | Found "no route" when a route existed (13a), wrong cash (12a), and the oracle disagreeing exposed bugs | Keep; it is where the money truth lives |
| A durable workflow for a pure, keyless route solve | `planning/workflow.py`, `planning/solve_runs.py` | One more run kind with cancel and lock rules | Survives restarts; cancel works | Built; don't add more workflows for pure computation |
| Expected version and idempotency on every write | `profile/commands.py` pattern | Boilerplate per command | Stops lost and doubled input | Keep |
| Language word lists (support words, redaction, quote checks) | `profile/safety.py`, `evidence/redaction.py` | Most of the old fix-round tails | The support panel and contact-detail removal | Keep; R11 already freezes growth |

I found no layer that is pure ceremony. The overweight is in what surrounds the code: the
documents each change has to update and the checks each change has to pass.

---

## (b) Proposals

Ordered by value. "Archive" means `git mv` into an `archive/` folder: git keeps everything,
and agents stop reading it. No safety or truth rule is weakened by any of these.

**1. Stop copying controller state and history into every brief.**
Move "Order…", "Current position…" and the finished audit card out of the preamble into
`planning/controller-state.md` (the controller reads it; implementers don't), and change
`make-brief.sh` to stop at "## Order". Keep "Always read", the Global Constraints and the
standing rulings.
- Saves: about 20 KB (5,000 tokens) per agent run, about half the preamble; about 275,000
  tokens over the 55 or so remaining runs. Less stale text to misread.
- Risk: low. No rule moves; the controller still enforces order and session gates.
- Effort: 30 minutes.

**2. Merge the process rulings R12–R17 into one current block.**
One "How we build and review" ruling with today's numbers (four implementers, one review,
one fix round, full checks once per batch, the backend and screens halves), keeping every
live clause word for word. Put the old R12–R17 text under a "superseded" heading in the
controller file. Update both contracts to match.
- Saves: about 4 KB per run, and three conflicting statements of how many implementers may
  run.
- Risk: low. It restates your approvals; nothing is dropped. One review.
- Effort: 1 hour.

**3. Bring the contracts and "Environment facts" up to date.**
The Linux machine, `/home/user` paths, the product's name, the current check commands, so
dispatches stop carrying "This machine first" overrides.
- Saves: about 1,000 tokens per dispatch and wrong-path mistakes.
- Risk: low. Effort: 30 minutes.

**4. Split the ledger: a short live ledger plus an archive.**
Archive `progress.md` as it stands. Start a live ledger of under 150 lines: one row per task
(status and commits), open rulings, open questions for you, what is running, and one
**final-review list** gathering every parked item now spread over 20+ lines.
- Saves: about 12,000 tokens every controller session (15,000 down to about 3,000), and no
  parked item lost at the final review.
- Risk: low; the full ledger stays in the archive and git.
- Effort: 2 hours.

**5. Archive finished work in `planning/`.**
Move the 274 finished task files and the 28 old audit, session 1, handover, plan-update and
carry-forward files to `planning/archive/`. Delete the 8 gitignored review diffs once their
task is in (`review-pkg.sh` rebuilds them). Never move `answers-2.md` or
`esco_research.txt`.
- Saves: `planning/` goes from 348 entries to about 30; searches and globs stop hitting 4 MB
  of history.
- Risk: low; old links point into history only.
- Effort: 30 minutes.

**6. One paper file per piece of work.**
The implementer writes the report; the review and the fix round are appended to that same
file. No separate review dispatch, re-review or "CLAUDE.md proposal" files: the controller
keeps proposals in its own notes.
- Saves: controller time and 4–9 files per piece down to 1–2.
- Risk: low; the same content, one place.
- Effort: none, a habit change.

**7. Strip history out of the plan's "always read" sections.**
Move the v1.1–v1.6 version notes and the three old "Order from here" lists to a "Revision
history" appendix at the end of the plan. Archive `docs/plan/l0-assessment-handover.md`.
Narrow "Always read" to sections 1, 3, 4 and 7 plus the card; section 5 for screen work;
sections 8–10 for the task that closes a sprint.
- Saves: about 8 KB of history from every implementer's reading; up to 25 KB (6,000 tokens)
  with the narrower list.
- Risk: medium-low; an implementer could miss a section-9 rule. The card names the sections
  it needs.
- Effort: 1 hour.

**8. Slim the requirements register and move its upkeep to the controller.**
Each row keeps its ID, requirement, test IDs, owner and status, plus one line pointing to the
evidence. Move the narrative (rows up to 7 KB) to an archived snapshot. The controller
updates rows once per batch; implementers only tag tests with the ID.
- Saves: about 70,000 tokens whenever the register is read whole; removes the biggest source
  of "register over-claims" findings (about 86 so far) and a shared file every worktree
  fights over.
- Risk: medium. The register is the trace from requirement to test; keep the IDs and the
  status exactly, and have one review check the conversion.
- Effort: half a day, mostly scripted.

**9. Put a one-page "what holds now" at the top of each long ADR.**
For 0007, 0009, 0012, 0015 and 0016: a short list of the decisions in force today, then
the full text below as the record. Tell agents to read only the summary unless they change
that area.
- Saves: up to 20,000 tokens for an agent touching discovery (0007 alone is 91 KB).
- Risk: low; the full ADR text stays. A wrong summary is the risk, so one review.
- Effort: 3 hours.

**10. Say each rule in one place, and point to it everywhere else.**
`CLAUDE.md` holds the rules; ADRs hold the reasons; the tasks file and the plan point to
them instead of restating them. Start with the Global Constraints that repeat `CLAUDE.md`,
and the acceptance lock text that sits in both the tasks file and the contract.
- Saves: a few KB per run, and the "two copies disagree" findings.
- Risk: low, if done by pointing and not by rewording a rule.
- Effort: 2 hours, best done with proposals 2 and 7.

**11. Retire the design mirror for built chapters, and archive the world spike.**
The plan already says a built chapter's stories become its reference. Do it for the You
chapter now and archive `spikes/world`, as Task 10's card already asks.
- Saves: 792 KB of mirrored files and their drift check, and one less place for reviewers to
  look.
- Risk: low. Effort: 1 hour, in Task 10's first commit.

**12. Freeze the infrastructure: no new services, workflows or run kinds in L0.**
The remaining tasks (Skills, Options, Routes, Plan, Roles, moments, release) build on what
exists. New pure computation runs in-process. Keep `make acceptance` once per batch, and use
the focused stack test for the files a piece touched in between.
- Saves: no new 20-minute failure sources; review time stays on what the person sees.
- Risk: low; any genuine need comes to you as a one-line question.
- Effort: none, a ruling.

---

## (c) Verdict

The product code is heavier than a one-person local app strictly needs, but it is not
over-engineered in the way that matters: almost every heavy part is something the
specification asked for, and the review record shows those parts catching real,
decision-changing mistakes (wrong cash, a hidden feasible route, words the person never
said). The real overkill was process and paper: repeated re-review rounds (now fixed by your
speed rules), and documents that keep every past version in the text agents read, so about
half of every brief and most of the ledger is history. Archiving that history and keeping
one review per piece should save roughly a third of each agent's standing reading and hours
of controller time, with no loss of quality, because no truth or safety rule moves.
