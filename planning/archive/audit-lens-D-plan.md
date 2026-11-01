# Audit lens D: the plan and its sprints (Task A1)

Read-only lens. HEAD 8e78060, branch `l0-local-release`, 2026-10-31.
Question: is the development plan still sensible, and what order puts the practical, useful
product first ("The visuals are important, but they must be subservient to having a practical,
useful product")? Includes the product owner's new requirement, given mid-audit, that the
role space must not stop at a prefilled list ("an omniscient career coach who knows all
possible jobs that could fit you"). Another lens designs that capability; this lens only
places it in the plan.

## 0. The answer in five lines

1. After about 58 hours of agent work, a person can use one chapter (You). Skills, Options,
   Routes and Plan show "not built yet". The decision path the specification calls "a complete
   M0 session" does not exist yet in the app.
2. Session W2's gate (every review score at least 4 before any other chapter is built) puts
   the whole decision path behind finishing the world's spectacle in the You chapter.
3. The world is already good enough to build on. Design references for all six places exist,
   and they are plain glass panels over a simple world. What's left of Task W2 is mostly
   spectacle that can come later.
4. Recommendation: build the decision path first (shape B). Skills, then Options, then
   computed routes, then the plan, each drawn plainly in the world as it stands. The open role
   space goes early, in discovery, before Skills. The chapters' special moments come after the
   path works, then Roles, then release.
5. Total effort barely changes. What changes is how soon a person gets value: a printable plan
   after about 45–50 agent hours, instead of about 55 or more. Backend work no longer waits for
   any session.

---

## 1. Assessment of the current plan

### 1.1 What the history says (agent wall-clock hours from commit timestamps, review and fix rounds included)

| Work | From → to (commits) | Hours | Fix rounds | Plan size (eng. days) |
|---|---|---|---|---|
| Sprints 0–2 (Tasks 1–6) | 324b2ab 10-27 22:03 → b543fd3 10-28 17:08 | ~19 | 1,1,3,2,2,5 | 9–12 |
| 6b, session 1 transcription, 6c | f360a86 17:53 → 8276485 22:46 | ~5 | 3,1,1 | — |
| Sprint 3 backend + 7d + pack + Sprint 4 and 5 backends (7A, 7B, 7d, 7b, 9, 11) | 8276485 22:46 → 594843c 10-29 17:58 | ~19 | 5,2,1,3,3,1 | ~12–14 |
| Session 2 to plan v1.4 (human-gated) | d9ff303 10-29 18:17 → da25020 10-30 13:59 | ~20 elapsed | — | — |
| Sprint W so far (W1, W2A, W2B, W2C part 1; 7c excluded) | da25020 13:59 → f179d0f 10-31 08:12 | ~16.5 | 2,2,5,1 (+re-review pending) | 7–10 |

- The backend averaged about 1.4 hours per sized day. Sprint W is running at about 2.5 hours
  per sized day (about 70% done for about 16.5 h). So world work costs about 1.8 times as much
  per planned day. Confidence: medium (estimated from commit times; slices overlap a little).
- The tasks that hit the five-round breaker were Task 6 (support-screen wording), slice 7A
  (redaction) and W2B (slate matching and the wording of its notes). Ledger lines 174, 405 and
  721. W2B's loop ended with a rule, not a fourth rewording (line 714). The rule: "every note
  describes what the search did … never what ESCO contains".
- Human review hasn't been the bottleneck. Every session was held within hours. Agent build
  and review loops set the pace. That contradicts the plan's risk entry (`development-plan.md:949`).

### 1.2 Findings

| # | Finding | Evidence | Why it matters | Recommendation | Conf. |
|---|---|---|---|---|---|
| D1 | Only the You chapter is built. The others are placeholder cards. | `apps/web/src/components/ChapterView.tsx:35-63` (`PLANNED` roles, skills, options, plan; "Skills checking isn't ready yet"); `ChapterView.tsx:218-249`; Routes shows only the labelled fixture preview (`:220`) | The spec's "complete M0 session" (sure/unsure entry, through skills, options and route comparison, to a printable plan; spec line ~44) isn't reachable. The product isn't practical yet. | Put the decision path first (section 2) | high |
| D2 | Session W2's gate blocks all five remaining chapter interfaces, behind a threshold of at least 4 in every rubric category | `l0-sprint-tasks.md:225-228` (rule 15), `:777-779`; `development-plan.md:233`, `:538`, `:873` | 11 categories in total, 3 of them about the world's ambition. Session 2 scores were 2,4,4,3,3,4,2 (`session-2-answers.md`). One low score triggers a fix round before any Skills work starts. Visual taste ends up gating usefulness, which is the opposite of the product owner's direction. | Keep at least 4 as the release gate (plan section 5 already has it). Make session W2 a short first look. | high |
| D3 | Design references for every chapter already exist, and they're plain | `docs/design/screenshots/skills--default--1440x900.png`, `routes--default--1440x900.png` (a glass panel with a list or scatter, one bright action, a simple trail drawing); W2A delivered "the six places at the three viewports" (`task-W2-slices.md:20-25`) | The "world" a chapter needs to be built in is already decided. The spec's M0 interface is "List/table, cost-time points, sliders, static focused Gantt, simple SVG city/company dendrite" (spec BND-1 table), and the references match it. | Build each chapter to its reference now. Add its moment later. | high |
| D4 | Most of what's left of Task W2 is spectacle | `l0-sprint-tasks.md:283-303`: ignition, connection "lit in the world", rings, target preview, frame re-measure | These items add wonder to one chapter while four chapters don't exist | Sort each item (section 3.2): keep the truth and usability ones, move the spectacle to a moments task | high |
| D5 | Backend work isn't gated by session W2, yet it sits after the interface tasks in the order | Task 13a needs only Task 7c (`l0-sprint-tasks.md:957-958`). Task 12's planning inputs are backend (`carry-forward-task-12.md:3-11`; `routes_planning.py` docstring: "What has no store yet is every input the person supplies"). The suggested order puts 13a after 10, 12 and 8 (`l0-sprint-tasks.md:230-231`). | The solver is the critical chain's riskiest link. Running it first costs nothing under any shape. | Run 12a (planning inputs) and 13a now, while the plan changes are approved | high |
| D6 | Task 12 hides a backend task inside an interface card | `carry-forward-task-12.md`: persist ADR 0013 decision 11's whole input list, outcome accept/override persistence, D12–D17, funding stacking, null month rows | Routes for a real person need these inputs, not just fixtures. As one card it's too big and gated by the interface rules. | Split it: 12a backend (no session), 12b the Options chapter | high |
| D7 | Task 14 and Task 15 are the largest interface tasks, and each closes behind its own human step | Task 14 closes only after session 3 (`l0-sprint-tasks.md:1003-1006`); Task 15 waits for Task 14 to close (`:1033`) | Two extra waits on the path to a plan | Merge session 3 into one end-to-end session after Task 15 | medium |
| D8 | On a phone, the world band pushes the first decision a scroll away | `l0-sprint-tasks.md:278-279` ("the band of world above the console (about 300 px) puts a long view's first decision a scroll away"). The plan itself says "On a phone the world is the backdrop behind focused views, with the console and cards in sheets" (`development-plan.md:208`). | A concrete case of the visuals costing the person usability, against the plan's own phone rule | Fix it when closing W2: on a phone, the decision comes first | high |
| D9 | The product owner's sessions work when they're short and hands-on. Long question sets get handed off. | Session 2: phone review skipped ("a waste of time until we've fixed this mess"). Q16–Q344, T and R were checked by an AI, then ruled to count (`session-2-answers.md`, "Decisions the product owner added at the end"). Session W1: Q2, Q3, Q6 unanswered (`session-w1-answers.md`). | Session W2's planned sheet has about 25 items (`carry-forward-task-W2D.md:7-12`), mostly matching parameters and wording | About 5 questions per session. Ask about outcomes, not parameters. Rote checks go to an AI if the product owner says so. | high |
| D10 | ADR 0008's reason for putting Roles last no longer holds | ADR 0008 context: "There are no Adzuna credentials … so the dendrite has no live vacancy data" (`0008…md:33-35`). The credentials now exist and the live qualification passed (ledger line 394; `carry-forward-task-8.md:11`). R4 is stale (`l0-sprint-tasks.md:111-116`). | The order is still right (Roles doesn't feed the planning chain), but for a different reason | Restate the reason. Correct R4. | high |
| D11 | The register and the plan have drifted | Register sessions table lists only sessions 1–3 (`requirements-register.md:646-657`). H-13 is still "not run" although session 2 part 1 was held and marked (`:644`; `session-2-answers.md` part 1). Plan table row 7 lacks v1.4's extra day, which the total includes (`development-plan.md:274` vs `:280`). | Small, but the release report reads these | Fix in the plan-update commit | high |
| D12 | The open role space has no slot in the plan, though the spec already asks for it | Spec: "A library of common role templates is a cache accelerator, never the universe of recommendable careers … emerging roles absent from older taxonomies" (spec line 261). "LLM-generated titles are search hypotheses until corroborated" (line 263). The build narrowed discovery to ESCO: CLAUDE.md line 133 ("the slate is deterministic code over ESCO"); ADR 0007 decisions 5 and 13. Person-verified titles outside ESCO exist as provisional concepts (`profile/concepts.py:1-12`), but model titles are never corroborated. | The product owner's new requirement is a top priority. Discovery is where a person first meets it. Today a role outside ESCO gets "No ESCO record, so no requirement list yet" (`carry-forward-task-W2C.md:15`). | A new task early on the path, before Skills (section 3.4) | high |
| D13 | Wording and matching loops are the main cost risk, and the review set-up multiplies them | 15 of about 40 review cycles were fix rounds on wording or language rules (Task 6, 6b, 7A, W2B). R11 caps language rules but not UI notes. W2B needed a rule after three rounds. | The open role space and the Skills notes are the same kind of work | Make W2B's rule a standing ruling for every line the UI shows. The product owner judges suggestion quality. Reviewers don't loop on it (ledger line 698 precedent). | medium |

### 1.3 What is sound (keep)

- The critical chain and its integrity rules (`development-plan.md:288`; Global Constraints
  1–13). The deterministic checker (Task 11), the capability model (Task 9) and the reviewed
  pack 0.2.0 (Task 7c) are the right foundations for Skills, Options and the solver.
- The Sprint 6 split (6a on instances that complete, 6b at full scale): ADR 0008 decision 2.
- One implementer at a time, reviewed slices, the five-round breaker with adjudication.
- Agents never self-certify human gates (R2), and sessions are recorded word for word.
- The world's truth contract (ADR 0014 decisions 1–8): everything that varies has a computed
  meaning, a still version, an exact DOM layer. Nothing in this lens proposes weakening it.
- Sprint 10's manual is the product owner's own request (v1.3). Keep it after release.

---

## 2. Three plan shapes

Constraints that differ: (A) the world leads; every chapter is born with its moment.
(B) usefulness leads, without new spectacle; the world as it stands frames every chapter.
(C) effort is capped; L0 shrinks to the decision path.

| | (A) Current: finish the world, session W2 gate, then chapters | (B) Decision path first, the world added per chapter after | (C) Cut L0 to the decision path |
|---|---|---|---|
| Order | W2C1 re-review → W2C2 → W2D → session W2 (all ≥ 4) → 10 → 12 → 8 → 13a → 13b → 14 (session 3) → 15 → 16 → 17 | Close W2 → 12a, 13a → open role space → session W2 (first look) → 13b → 10 → 12b → 14 → 15 → end-to-end session → 8 → moments → 16 → 17 | As B, but Roles (Task 8), the moments task, celebrations and the overlooked-strength interface move to the next milestone. 13b is kept (spec M0 limits). |
| Open role space | No slot. Inserted after session W2 at best, so the product owner judges an ESCO-only slate they've just said is too narrow. | Early: right after closing W2, before session W2 and Skills | Early, minimal version (own titles plus model titles corroborated by live postings); deep research later |
| Milestone 1 | ~13–20 h: the You chapter with its first moments | ~10 h: solver proven on TRACE-01 and pack instances; planning inputs stored; You fixes | Same as B |
| Milestone 2 | ~25–30 h: Skills, then Options | ~17 h: open roles in discovery. ~23 h: Skills (what a target needs, where you stand). | Same as B |
| First computed routes for a person | ~48 h (after 8, 13a, 13b, 14) | ~40 h (after 12b, 13b, 14) | ~38 h |
| Printable plan (spec "complete M0 session") | ~55 h, later if a session W2 fix round happens | ~47 h | ~44 h |
| Total remaining (agent h, incl. review) | ~60–100 (incl. W2C2, W2D, gate risk 0–6 h, open roles ~5–10) | ~55–98 | ~40–65 |
| Main risks | Spectacle before substance; a score below 4 loops before any chapter; the solver risk found late; the product owner's direction not followed | The product owner finds plain chapters "bland" (mitigated: built to references they judged "OK", ledger line 640); some chapter visuals redone when moments land | Drops requested features: the dendrite is in spec M0 ("simple SVG city/company dendrite") and listed as requested in ADR 0008, "What does not change". Needs a spec change. |
| ADR 0008 (order, reviews) | Unchanged | Amend: new order; session 3 merged | Amend, plus a scope change (spec and ADR 0001) |
| ADR 0014 (the world) | Unchanged | Amend decision 9 only: the gate moves to release, moments to a later task. Decisions 1–8 unchanged. | As B, and moments become optional for L0 |
| R10 sessions | W2 (gate), 3 | W2 slimmed (about 30 min, not a threshold), one end-to-end session replaces 3 | As B |
| Global Constraint 11 ("a bland screen fails review") | Applies to every task | Applies at the moments task and the release review. Path tasks are judged on correctness, words, access and fidelity to the references. | Applies at release only |

**Recommendation: shape B, offering C's cuts only as later product-owner choices.**
- It follows the product owner's direction and keeps their world. Every chapter is still
  built "as its place in the world" on references they've seen; only the order changes.
- It moves the riskiest technical work (the solver, planning inputs) to the front, where any
  shape needs it.
- It puts the open role space where the product owner said it belongs, before anyone judges
  the slate.
- It keeps scope. C needs specification changes (the dendrite and the plan's revision are
  M0, spec section 15 "Select, commit and revise [M0]"). C is better offered at the
  end-to-end session, if time matters by then.

---

## 3. Proposed task list (shape B), in order

### 3.1 The list

| # | Task | Scope (one or two sentences) | Preconditions | Cards kept / merged / split / cut | Human session |
|---|---|---|---|---|---|
| 0 | A1 approved | Plan changes below applied in one docs commit | Product owner's yes | — | The A1 summary |
| 1 | **W2E: close Sprint W** | Scoped re-review of W2C part 1's fix round 1 (app I1–I3, design I1 regressions only). Practical fixes: phone decision first (D8), "Help me explore instead" focus, still-words test on a non-fixture workspace. The world requirement family in the register. Plain words for the fixture route preview. ADR 0014 decision 7's strip wording. `docs/reviews/sprint-w.md` (session W2 slimmed). | A1 | Takes from W2C part 1 and W2D. Moves out: ignition, revelations lit, rings, target preview (to task 11), frame re-measure (to task 13), phone openings list (to task 10). | — |
| 2 | **12a: planning inputs (backend)** | Store and confirm ADR 0013 decision 11's inputs as validated commands (expected version, Idempotency-Key). Apply D12–D17. Leave stacked funding unresolved. Outcome accept/override persistence. Null month rows for unknown amounts. API and client regenerated. No interface. | A1 | **Split** from Task 12 (`carry-forward-task-12.md` items 1–7) | none |
| 3 | **13a: solver core** | As the card says: canonical DFS, sound pruning, full encountered archive, F1–F3 peeling, independent oracle and checker, measured complete-coverage sizes. Plus one instance from P01's stored inputs (task 2). | 7c (done); 12a for the P01-inputs instance | Kept, moved earlier | none |
| 4 | **6d: the open role space (new)** | Discovery stops at no fixed list: roles outside ESCO can be found, shown and chosen, with the evidence behind each. Design comes from the role-space lens and the product owner's decision. The model proposes; code corroborates; the person confirms (spec lines 261, 263). | A1; the role-space design approved; ADR 0007 amended and CLAUDE.md line 133 changed with the product owner's approval | **New** (Sprint 2, a new deliverable S2.8). Absorbs W2C2's type-ahead "couldn't match that title in ESCO" question and "none of these" path. | Judged at session W2 |
| 5 | **Session W2, slimmed** (~30 min) | The product owner uses the You chapter in the app, open roles included, and answers about 5 questions (section 3.3). Their record, word for word. No threshold. | Tasks 1 and 4 | Replaces the session W2 gate and its ~25-item sheet | **W2** |
| 6 | **13b: durable, bounded search** | As the card says. Runs while session W2 is awaited. | 13a | Kept | none |
| 7 | **10: Skills chapter** | The Skills chapter to its reference: requirements as demonstrated, self-reported, planned or unresolved; gates; evidence one step away; the question flow; live scoring of the ten course pages. Also: the current role chosen by type-ahead (W2B's backend), "usual in your role, not confirmed yet" as a display state, and requirements for an open-role target from the person's exemplars or task 4's evidence (MAP1-01, by the person's span selection, no new model run). | Session W2; 6d | Kept. Takes W2C2's "usual in your role" and the type-ahead role choice. Its moment (the overlooked strength) moves to task 11. | — |
| 8 | **12b: Options chapter** | The Options chapter and the review checkpoint to its reference, collecting the inputs task 2 stores; pin/exclude; why a route may fail; live scoring of the funding pages; `sprint-5.md`. | 12a, 10 | **Split** from Task 12. Its moment moves to task 11. | — |
| 9 | **14: Routes chapter** | As the card says, on real solver output, with plain words for every cost (H-13's finding: "psychobabble"). The credible-route moment moves to task 11. S0-V04 and S0-V06 carried. | 13b, 12b | Kept. Closes on its checks, not on session 3. | — |
| 10 | **15: Plan chapter** | 15A: snapshot, the Plan chapter, print, JSON and ICS (S8.1, S8.2, S8.5, S8.6). 15B: revision and replan (S8.3, S8.4). Both M0, both in L0. | 14 | Kept, sliced. Its moment moves to task 11. | — |
| 11 | **End-to-end session** (~1 h) | P01 from You to a printed plan in the demo. One live run on a synthetic persona with an open-role target. Formative scores. Picks and orders the moments. | 15A at least | Replaces session 3. Holds H-01 for Sprints 4, 5, 7, 8 (formative). | **E2E** |
| 12 | **8: Roles chapter and job corpus** | As the card says, with live Adzuna data (credentials exist). Roles outside ESCO from task 4 and live postings appear on the map. W2D's phone openings item added. | 15A; session 1 (held) | Kept, moved after the path | — |
| 13 | **M: the moments (new)** | The chapters' moments in the product owner's order from task 11, each within a set budget: the first answer's ignition, the connection lit, decisions previewed (rings, target preview), the overlooked strength (proposal, confirm, held back on support turns, destinations on the horizon), a bridge, the credible route, committing, progress landmarks. Frame re-measure, with the product owner warned first. | Task 11 (the session); 8 | **New**: gathers W2C2's spectacle, W2D's frame run and every card's "with its moment" | — |
| 14 | **16: release qualification** | As the card says. Every rubric category at least 4 (plan section 5). Frame budgets. | All above | Kept. Preconditions updated. | Release checks (section 3.3) |
| 15 | **17: operator's manual** | As the card says | 16 | Kept | H-14 (not a precondition) |
| 16 | Final whole-branch review | As planned | 17 | Kept | — |

Notes:
- One implementer at a time still holds. Tasks 2, 3 and 6 never wait for a session.
- If the role-space design isn't approved by the time task 3 finishes, task 6 (13b) runs next,
  and task 7 still waits for task 4. Skills' handling of roles outside ESCO depends on what
  task 4 produces.

### 3.2 What happens to each item of "Remaining Task W2 work" (`l0-sprint-tasks.md:275-322`)

| Item | Disposition | Why |
|---|---|---|
| W2C part 1 scoped re-review | **Keep** in W2E, scoped to lost input, focus, truth words and the capture regressions | Practical defects; cheap (~1 h) |
| Phone world band ~300 px | **Keep** in W2E: decision first on a phone | Usability; plan's own phone rule (`:208`) |
| "Help me explore instead" drops focus | **Keep** in W2E | Accessibility (WCAG) |
| Identical-words test covers only the fixture workspace | **Keep** in W2E | Truth of the still world |
| First answer's ignition | **Move** to task 13 (M) | Spectacle |
| Type-ahead closest titles question | **Move** to task 4 (open role space), with "none of these" leading to the open path | Directly part of the product owner's new requirement |
| Connection lit in the world | **Move** to M. The connection's sentence in the DOM stays wherever it already is. | Spectacle; the fact is already computed (ADR 0007 decision 14) |
| Overlooked strength proposal and confirm; `held_back`; strength destinations on the horizon | **Move** to M (all together) | A model-backed run built in W2B (ADR 0014 d3); counts for nothing towards readiness; its safety handling must ship with its interface |
| "Usual in your role, not confirmed yet" | **Move** to task 7 (Skills) | It is how Skills shows unknown-but-likely skills |
| Rings, "Make this a target" preview | **Move** to M | World version of "consequences before confirming"; the plain confirm already exists |
| World requirement family in the register; Sprint W acceptance | **Keep** in W2E (the frame part goes to M and 16) | Traceability |
| Frame re-measure | **Move** to M, then 16 | Opens a window on the product owner's screen (ledger lines 635-637); the world will still change |
| Plain words for "Economic cost" / "Direct spending" | **Keep** in W2E (fixture preview), again in task 9 | The product owner saw this in the demo and couldn't follow it (session 2 part 1) |
| ADR 0014 decision 7 strip wording | **Keep** in W2E (docs) | Accuracy |
| Phone openings list one per line, stale/unknown captures | **Move** to task 12 (Roles) | Roles reference |
| Session W2 package, sheet, `sprint-w.md` | **Replace** with the slim package (section 3.3); `sprint-w.md` in W2E | D9 |
| Parked: "&" and accents in `concept_key` | **Move** to task 4's design input | It is a role-space gap ("dog groomer", "&" titles unmatched), not just polish |

### 3.3 Human sessions: which, when, and what each decides

| Session | When | Decides (about 5 questions, plain words, each saying what "yes" does) | Precondition for |
|---|---|---|---|
| 1 | Held 2026-10-28 | Done. One open human gate stays: review committed excerpts for names before any push (`session-1.md`, delegated decision). | — |
| 2 | Held 2026-10-29/30 | Done. Its part 1 result (route words "psychobabble", "Confusion can make one indecisive and give up") is a scope input to task 9. The register still says H-13 "not run" (D11). | — |
| W1 | Held 2026-10-30 | Done. Q2, Q3, Q6 unanswered: drop them. | — |
| **W2, slimmed** (~30 min) | After W2E and the open role space | 1. Is the You chapter in the world right enough to build the other chapters on? (yes = chapters follow its references) 2. For two or three named personas, including one whose role isn't on any standard list, are the suggestions sensible and is anything missing? (replaces the slate-rule parameters, thresholds and note-word items) 3. Keep Source Sans 3 for body text? 4. Keep leaf green for "accept", since words and a glyph carry it? 5. Any words you didn't understand? Optional appendix: the rest of the old sheet, AI-checked if the product owner says so. | Chapter interfaces (tasks 7–10). Not backend. |
| **End-to-end** (~1 h) | After task 15A | 1. Re-ask session 2's three route questions on the real Routes chapter (cost, condition, what's uncertain: the dangerous-misunderstanding check). 2. Formative scores for Skills, Options, Routes and Plan. 3. Order the moments (task 13), or skip some. 4. Are the open-role results honest and useful? 5. Anything that blocks a release? | Task 13 (moments); task 14's design gate |
| Release checks (task 14) | During task 14 | H-01: every category at least 4 (plan section 5). H-03 VoiceOver, H-04 Safari and print, H-05 five task sessions (who takes part is unknown: ask early), H-08 privacy before any real person's data, the pre-push name review, and the counterfactual pass rule (open since ledger line 249). | None is a dispatch precondition (as now) |
| H-14 (task 15) | After the manual | A person follows the manual | Not a precondition |
| Session 3 | — | **Merged** into the end-to-end session | — |

Total remaining product-owner time: about 1.5 h of sessions plus release checks. The current
plan has 2 h of sessions plus the same checks and a possible gate loop.

### 3.4 The open role space: where it sits and what it touches

- **Place:** task 4 (6d), right after closing Sprint W and the two backend tasks, before
  session W2 and Skills. A person first meets it in discovery.
- **Order dependencies**
  1. Design (role-space lens), then the product owner's decision.
  2. Then the rule changes. CLAUDE.md line 133 ("the slate is deterministic code over ESCO")
     and ADR 0007 decisions 5 and 13 must be amended first. They're invariants agents
     enforce. CLAUDE.md needs the product owner's explicit approval.
  3. Then the build (task 4).
  4. Then session W2 judges the slate with it. Otherwise the session spends the product
     owner's time on ESCO-only parameters they've just called too narrow.
  5. Then Skills (task 7). A target outside ESCO has no ESCO requirement list, so Skills needs
     task 4's corroborating evidence or the person's exemplars (MAP-1 allows up to three per
     target; `carry-forward-task-10.md:4`).
- **What it touches**

| Remaining work | Effect |
|---|---|
| W2C part 2 | The type-ahead "couldn't match" question moves into task 4; the "none of these" path leads to the open role space |
| Session W2's sheet | The slate rules, too-general thresholds, main-name-only search and specificity items are replaced by one question on suggestion quality, with an open-role persona |
| Task 8 (opportunity map, job corpus) | Live postings (Meta search, Adzuna) are both a source of titles outside ESCO and their corroboration. The map must group and show such roles (grouping is by ESCO concept today). |
| Task 10 (Skills) | Requirements for open-role targets (exemplars or evidence); the sketch's "No ESCO record, so no requirement list yet" changes |
| Task 12b and the option pack | The pack covers only P01–P05 targets. Open-role options come from live research as `proposed` records, so their routes stay qualified or unresolved (R9). That's honest; it must be said in plain words. |
| Tasks 13a and 14 | Concepts must accept provisional and corroborated IDs. No rule changes. |
| Task 16 | The live journey includes an open-role persona; evaluation cases for "unsupported-title rejection" (spec DIV-1) are revised so a corroborated title outside ESCO passes |
| Muse Wonder (A1 question 4) | "Deep research" is likely its first product use; budget and ledger rules (R5) apply. Spec section 1 lists Wonder as M1, so that needs an ADR 0003 decision. |
| Parked `concept_key` ("&", accents) | Becomes task 4 input |

- **Loop risk:** this is discovery and matching work, the same kind as W2B (5 rounds) and
  Task 6 (5 rounds). Before dispatch, state W2B's rule ("a line says what the search did") and
  that the product owner judges suggestion quality at session W2 (ledger line 698 precedent).
  Estimate 5–10 agent hours.

---

## 4. Exact edits the recommendation needs (described, not applied)

### 4.1 `docs/plan/development-plan.md`
1. **Header (line 5):** "Plan version 1.5 (31 October 2026)"; add "with the product owner's
   direction of 31 October 2026 (a practical, useful product first; the open role space)".
2. **"Delivery envelope" (lines 21–25):** add a re-estimate from history: the remaining work
   is about 55–98 agent hours including review; world work runs about 1.8 times the backend's
   rate per sized day. Replace "Elapsed time is set by human review hours" (line 23) with
   "Elapsed time has been set by build and review loops; every session was held within hours".
3. **"How to use this plan":** add a "Version 1.5" paragraph. Quote the product owner's two
   sentences verbatim. List the changes: the decision path first; Task 12 split; the solver
   first; the open role space before Skills; session W2 slimmed, not a threshold; session 3
   merged into an end-to-end session; chapters' moments in a new Sprint M after the path works;
   Roles after the plan; at least 4 in every category stays the release gate.
4. **Section 1 table, "Visual scope" (line 59):** add "From v1.5, staged revelations,
   consequences shown before confirming, and celebrations come in Sprint M, after the decision
   path works. Until then every chapter is built in the world to Sprint W's design references,
   its states and words exact." Also "Product journey" (line 51): "Roles are never limited to a
   fixed list (v1.5): see Sprint 2, S2.8."
5. **Section 4, opening (after line 135):** add one paragraph: "The visuals serve a practical,
   useful product (the product owner, 31 October 2026). Where the world and the decision path
   compete for time, the path comes first; the world never blocks a working chapter."
   **"Design deliverables" (line 225):** "Every later chapter is built as its place in the world
   by its own sprint, to Sprint W's references (its exact layer: states, words, keyboard list);
   its moment is added in Sprint M."
6. **Section 5, rubric (line 233):** "At Sprints 1, W, 3, 7 and 9" becomes "At Sprints 1 and W,
   the end-to-end session and Sprint 9". "require every category to reach at least 4 at session
   W2 before more chapters are built in the world, and again before the final local release"
   becomes "record scores at session W2 and the end-to-end session to guide the work; require
   every category to reach at least 4 before the final local release".
7. **Section 6 table (lines 263–278):**
   - Row W: closes at the world shell, the You chapter and the deterministic sources; human
     hours "session W1 (held); session W2, about ½ h".
   - Row 2: note S2.8.
   - Row 7: fix to 6–8 days (v1.4's extra day); human "end-to-end session, about 1 h, after
     Sprint 8".
   - Add row M (moments): 3–6 days, after the end-to-end session.
   - Total: recompute. "About 7½ scheduled" becomes the sessions actually held plus about 1½ h.
8. **Line 280:** replace "with its moment" by "to Sprint W's references; its moment in Sprint M".
9. **Add "Order from here (v1.5)" after line 310:**
   (1) close Sprint W; (2) planning inputs, Sprint 6a; (3) the open role space; (4) session W2,
   slimmed, with Sprint 6b meanwhile; (5) Sprint 4 Skills, Sprint 5 Options; (6) Sprint 7
   Routes, Sprint 8 Plan; (7) the end-to-end session; (8) Sprint 3 Roles, Sprint M; (9) Sprints
   9, 10, final review. Add "Backend work never waits for a session. Interface work waits only
   for session W2." The v1.4 list stays as history.
10. **"Human review sessions" (line 314):** sessions now 1, 2, W1 (held), W2 (slimmed) and the
    end-to-end session; session 3 merged.
11. **Sprint 2 card:** add S2.8, the open role space. One line of intent: roles are not
    limited to ESCO; model proposals stay hypotheses until code corroborates them (spec lines
    261, 263); the person confirms. Design details come from the role-space design.
12. **Sprint 3, 4, 5, 7, 8 cards:**
    - Entries: "the approved world" becomes "Sprint W closed and session W2 held".
    - Sprint 7 (line 602): drop "closes only after review session 3"; S7.5 "with its moment, the
      credible route" becomes "as its place in the world (its moment in Sprint M)".
    - Sprint 5 (line 478): S5.3 and S5.4's person-supplied inputs stored and confirmed first, as
      a backend slice.
    - Sprint 8: S8.1, S8.2, S8.5, S8.6 first, then S8.3, S8.4.
13. **Sprint W card:**
    - Line 518: the outcome's revelation sentences are delivered by Sprint M.
    - SW.5: the type-ahead role choice moves to Sprint 4; ignition, the revelations' lighting
      and the strength's confirm move to Sprint M.
    - Line 538: session W2 is a short first look, with no category threshold.
    - Frame measurement moves to Sprints M and 9.
14. **New Sprint M card:** the moments of section 4's table, in the product owner's order from
    the end-to-end session, each within a stated budget; Sprint W's revelation acceptance (the
    sentence and evidence in the DOM; still-world parity; held back during distress); the frame
    re-measure with the product owner warned first.
15. **Section 10 sessions table (lines 867–873):** W2 row becomes "about ½ h (v1.5): the You
    chapter and the open role space in the app; the product owner's record of what to change;
    precondition for chapter interfaces, not a threshold". Session 3 row becomes the end-to-end
    row (after Sprint 8; formative H-01 for Sprints 4, 5, 7, 8; the moments' order;
    precondition for Sprint M).
16. **Section 11 VIS row (line 901):** "The world approved at session W2" becomes "The world
    reviewed at session W2 and the end-to-end session; every category at least 4 at release".
    Add a row for S2.8.
17. **Section 12 risks:**
    - Line 945: the response becomes "references before chapters; moments after the path".
    - Line 949: correct the bottleneck statement.
    - Add: "The world displaces the decision path (v1.5)": path first, moments later, release
      gate kept.
    - Add: "Open role discovery loops on wording and matching": W2B's rule up front; the
      product owner judges quality.

### 4.2 `docs/plan/l0-sprint-tasks.md`
1. **Header (line 3):** plan v1.5.
2. **Global Constraint 11 (lines 60–67):** add before its last sentence: "The visuals serve a
   practical, useful product (the product owner, 2026-10-31): until the decision path works
   end to end, chapters are built to the world's design references with exact states and
   words; their moments follow in Task M." Change "A screen that works but is bland fails
   review" to "… fails the moments review and the release review".
3. **R4 (lines 111–116):** the credentials exist; the live qualification passed (ledger rows
   32–33); `make setup` copies them for the acquisition worker.
4. **R10 (lines 153–175):** replace the three-session text with the five sessions and their
   status (section 3.3). Keep "only the product owner's own record establishes an outcome".
   Add: "the product owner may rule that an AI's check of rote items counts as their review,
   as at session 2; an agent never assumes it".
5. **Add R13, "Path before polish":** from A1's approval until Task 15A closes, world or visual
   refinements that no failing check, truth rule, accessibility rule or Global Constraint
   requires go to Task M's list. Reviews of path tasks judge correctness, words, accessibility
   and fidelity to the references.
6. **Extend R11 with W2B's rule:** every line the UI or API shows says what the code, search
   or match did, never what a dataset contains. A second fix round on the same class of
   wording gets a rule, not another rewording.
7. **Dependency rules (lines 199–228):**
   - Rule 7: Tasks 10 and 12b after 7c; 12b after 10 and 12a.
   - Rule 11: Task 14 after 13b and 12b; closes on its checks.
   - Rule 12: Task 15 after 14.
   - Rule 13: Task 16 after every task including 6d, 12a, 12b, 8 and M, and after sessions 1,
     2, W1, W2 and the end-to-end session.
   - Rule 15: interface tasks (10, 12b, 14, 15, 8, M) wait for session W2; backend tasks (12a,
     13a, 13b) never wait.
   - New rules: 6d after A1, the role-space design approval and the ADR 0007 / CLAUDE.md change;
     session W2 after W2E and 6d; Task 10 after 6d; the end-to-end session after 15A; Task 8
     after 15A; Task M after the end-to-end session and Task 8.
8. **Suggested order (lines 230–236):** W2E → 12a → 13a → 6d → session W2 (13b meanwhile) → 10
   → 12b → 14 → 15 → end-to-end session → 8 → M → 16 → 17 → final review. Keep the v1.4 order
   as history.
9. **"Current position and next tasks" (lines 247–322):** replace "Next, in order" with the
   order above. Replace "Remaining Task W2 work" by the disposition table (section 3.2). Session
   W2's sheet becomes the five questions.
10. **Task W2 card (lines 775–800):** ends with W2E. Session W2 is a first look; no threshold;
    W2C part 2 and W2D are replaced by W2E plus moves to Tasks 6d, 10, 8, M and 16.
11. **New cards: Task W2E, Task 6d (S2.8), Task 12a, Task 12b (from Task 12), Task M.** Each
    has a Preconditions line.
12. **Task 8 card (lines 802–838):**
    - Preconditions add 15A and session W2.
    - The moment moves to Task M.
    - Add W2D's phone openings item.
    - Add: roles outside ESCO from 6d and live postings appear on the map.
    - Correct "no live vacancy data" reasoning.
13. **Task 10 card (lines 867–892):**
    - Remove "with its moment, the overlooked strength".
    - Add the type-ahead role choice and "usual in your role, not confirmed yet".
    - Add requirements for open-role targets (MAP1-01 by the person's span selection, no new
      run kind).
    - Preconditions add 6d.
14. **Task 13a card (lines 955–981):** order note; add the P01 stored-inputs instance (after
    12a).
15. **Task 14 card (lines 1001–1029):** preconditions add 12b, drop session 3; moment to M;
    plain cost words as a named scope input from H-13.
16. **Task 15 card (lines 1031–1053):** preconditions "Task 14 complete"; slices 15A and 15B;
    moment to M.
17. **Task 16 card (lines 1055–1075):** preconditions updated; adds the frame re-measure (the
    product owner warned) and an open-role persona in the live journey.
18. **Task A1 card:** mark it approved, with the approval date.

### 4.3 ADRs
- **ADR 0008:** add an amendment "(2026-10-31, plan v1.5)":
  - The new order: path first; Task 12 split; 13a moved early; 8 after 15A; Task M before 16.
  - Session 3 merged into the end-to-end session.
  - Correct the context's Adzuna premise: credentials now exist. Roles stays after the chain
    because it doesn't feed it.
  - "What does not change" still holds: the dendrite, three layers and sliders stay in L0.
- **ADR 0014:**
  - Status: Accepted, with this amendment.
  - Decision 9: Sprint W closes at the world shell, the You chapter and the deterministic
    sources. Session W2 is a first look. Chapters are built in the world to its references.
    Moments come in Sprint M after the path works. The threshold applies at release.
  - Decision 3's "provisional … until the product owner confirms it at session W2": "at session
    W2, or for the strength's interface, in Sprint M".
  - Decision 7's frame evidence: "Task W2's acceptance slice measures again" becomes "Sprint M
    and Task 16 measure again, the product owner warned first". Decision 7's strip wording too.
  - Decisions 1–8's truth rules are unchanged.
- **ADR 0007:**
  - Decisions 5 and 13 are amended for the open role space (the role-space design decides the
    words).
  - The type-ahead's partial question gets its "none of these" path.
- **ADR 0003:** only if the product owner approves Muse Wonder for deep research or their
  sessions (another lens).

### 4.4 `docs/requirements-register.md`
- **Section 6 sessions table (lines 646–657):**
  - Add W1 (held) and W2 (slimmed) rows, and an end-to-end row.
  - Session 3 row: "merged into the end-to-end session (v1.5)".
  - Intro: "Three fixed sessions" becomes the current set.
  - "Task 16 waits for all three sessions" is updated.
- **H-01 (line 632):** "When" becomes "Sprints 1, 2 (session 2), W (session W2, formative), 4,
  5, 7, 8 (end-to-end session, formative), 9 (release: every category at least 4)".
- **H-13 (line 644):** transcribe session 2 part 1's outcome from the record (correct the stale
  "not run"), as a scope input to Task 14.
- **Owners:**
  - The strength's interface, revelation and ignition rows move to Task M.
  - Frame-budget rows move to Tasks M and 16.
  - VIS-2 "credible route" moves to Task M.
  - The world family is added by W2E.
- **New rows** for S2.8 (open role space; IDs from the design) and for R13's scope list.
  Revise DIV1-03, DIV1-04 and DIV1-05, and the "unsupported-title rejection" evaluation
  expectations, once the design is approved.

### 4.5 Also needed (product owner's approval)
- CLAUDE.md, "The experience" (lines 23–48): one priority line matching Global Constraint 11's
  new sentence.
- CLAUDE.md line 133: the slate invariant amended for the open role space. The controller
  offers exact wording; it's applied only on the product owner's yes.

---

## 5. Risks of the recommendation, and the cost if wrong

| Risk | Likelihood | Response | Cost if wrong |
|---|---|---|---|
| The product owner finds plain chapters "bland" and is angry, as at session 2 | Medium-low: the chapters are built in the world shell they chose, to references they judged "OK" (ledger line 640) | Session W2's question 1 asks exactly this before any chapter is built | Restyling 4 chapters: about 4–8 agent hours. Logic, APIs and tests are kept. |
| Moments retrofitted later force some interface rework | Medium | The exact layer (states, words, list) is built first; moments are world-layer additions keyed to computed states, which ADR 0014 already requires | A few hours in Task M |
| The open role space loops (matching and wording) | High without guard rails | W2B's rule up front; a loop bound; quality judged at session W2 | 5–10 h; worst case another W2B (about 7 h) |
| The role-space design arrives late | Medium | 12a, 13a, 13b fill the wait; Skills waits for it | Skills starts a few hours later |
| Removing the at-least-4 gate lets visual debt build up | Low-medium | The threshold stays at release; formative scores at two sessions | A larger fix round before release |
| ADR and plan churn confuses implementers | Low | One docs commit; cards carry their Preconditions lines | Under an hour |
| Shape C was the right call (time matters more than scope) | Low now | Offer C's cuts at the end-to-end session, with the remaining hours | None until then: B's first half is the same as C's |

If shape A had been right instead: B still builds the same backend first (no loss). The only
loss is chapters drawn before their moments, a few hours of visual rework.

---

## 6. What I could not check

- I didn't run the app or any test, by rule. Usefulness is judged from the code
  (`ChapterView.tsx`), the design references and the ledger. Checks passed on f179d0f per the
  shared brief.
- Hours are estimated from commit timestamps. Agents sometimes overlapped with controller
  commits, and review time isn't separated. Treat the per-day rates as ±30%.
- I didn't read the W2C part 1 fix-round report or reviews in full, only the ledger summaries
  (lines 729–741). So the scoped re-review's size is an estimate.
- I didn't verify which W2B origin and strength endpoints the web app already calls. A search
  found no web caller of `/origin` or the strength routes, so I assume none.
- The role-space design is another lens's. Its effort and its effect on Tasks 8, 10 and 12b
  are estimates until that design exists.
- Muse Wonder's budget and its use in sessions are another lens's (A1 question 4). I only
  noted where it touches the plan.
- Whether five participants exist for H-05 isn't recorded anywhere. Ask the product owner early.
