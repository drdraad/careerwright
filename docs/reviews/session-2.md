# Session 2 package: agenda, materials and record sheet (about 2½ hours)

- **Status:** agent preparation (Task 11, rulings R2 and R10). **Every part is not run -
  requires human.** Nothing in this package is an answer, and only the product owner's own
  record of the session establishes its outcome; an agent may transcribe it, never supply it.
- **Held by:** the product owner, with a design reviewer and a domain reviewer if available
  (the roles may overlap, plan section 6).
- **Closes:** H-13 (the formative comprehension session), H-01 for Sprint 2, and H-07 for
  Sprints 4 and 5: the England option pack 0.1.0 and the TRACE-01 checker on P01's real
  option set (TEST1-14), plus the capability reference and its proposed outcome levels.
- **Precondition for:** Task 7c (the reviewed pack, from the H-07 record), and through it
  Sprint 6a and the Skills, Options and Roles chapters' scoring; Task 10 applies the Sprint 2
  design findings first; Task 14 reads the H-13 record (plan section 10).
- **Before the session (about 5 minutes, outside the 150):** run `make demo` from the
  repository root and open `http://127.0.0.1:53000`, so part 2's live-app checks are ready.
  If the app is not running, those checks are optional: record them as not run.

## The agenda

| Part | What | Minutes | Material | Gate |
|---|---|---|---|---|
| 1 | The formative comprehension session | 30 | section 1 below | H-13 |
| 2 | The You chapter and the slate, desktop and phone | 25 | section 2 below | H-01, Sprint 2 |
| 3 | The option pack, parts 1 and 2 (Q1-Q219) | 55 | `session-2-option-pack-questions.md` | H-07 |
| 4 | The checker on P01's real option set (T1-T36) | 10 | `session-2-checker-questions.md` | H-07, TEST1-14 |
| 5 | The capability reference and proposed outcome levels (R1-R58) | 20 | `session-2-capability-questions.md` | H-07 |
| 6 | The decision sheet (D1-D17) | 10 | section 6 below | R6 decisions |
| | In all | 150 | | |

Take the parts in this order: the comprehension session first, while the person is fresh to
the screens, and the design review before the long yes/no sets. Any part may stop early; what
is left unanswered stays as it is (`proposed`, or provisional).

**Not in the 150 minutes:** the pack package's part 3, the job postings and requirements of
P03-P05 (Q220-Q344, about 32 minutes). It is optional: Task 8 may take these. Nothing else was
cut.

## 1 H-13: the formative comprehension session (30 minutes)

One person, synthetic data, the fixture route comparison and the TRACE-01 ledger. Formative,
not statistical (plan section 5); the five Sprint 9 sessions (H-05) are unchanged. Any
dangerous misunderstanding becomes a Sprint 7 scope input (Task 14).

**Surfaces** (existing captures; open them full size, one at a time):

1. The route comparison with route B's month-by-month ledger: `docs/design/screenshots/`
   `route-comparison--default--1440x900.png`, then `route-comparison--default--390x844.png`.
2. The app's fixture route comparison: `docs/reviews/sprint-2/screenshots/`
   `routes--compared--1440x900.png` and `routes--route-b--1440x900.png`, then
   `routes--route-b-expanded--390x844.png` on the phone.
3. Instead of the captures, the live components: `cd apps/web && pnpm storybook`, then
   **Shell / Route Preview From Fixture**.

**Script:**

| Minutes | Step |
|---|---|
| 3 | Say that everything is invented for a test, that there are no wrong answers, and that the screens are being tested, not the person. |
| 5 | Let them look at surface 1 and think aloud. Do not explain anything. |
| 15 | Ask the three questions below, in order, word for word, about route B. Write the answers down as said. |
| 7 | Fill in the record sheet together with the reviewer (not with the participant). |

**The three questions:**

1. "What would route B cost you, and what is that cost made of?"
2. "What does 'conditional readiness' mean here?"
3. "What is uncertain in what you see?"

What the screens are meant to convey, for the record sheet only, never read out: route B
costs £600 in direct spending and £600 in economic cost over a six-month comparison, paid as
£150 a month for four months, with no pay lost; the lowest point of the cash ledger is £4,850,
above the £500 reserve. "Conditional readiness" means ready for applications only if the
assessed report is passed: a modelled milestone, not a job or a guarantee. Uncertain: the
assessment's result, the provider and intake (to verify), the payment dates, and that every
figure is synthetic.

**A dangerous misunderstanding** is one that could lead someone to act against their own
interest: reading economic cost as cash in hand, reading conditional readiness as a job or a
guarantee, missing that a payment cap or the cash reserve could fail, or taking synthetic
figures as real ones.

### H-13 record sheet (not run - requires human)

| Item | Record |
|---|---|
| Date, participant code (no name) | |
| Surfaces used (1, 2, 3) | |
| Question 1, as said | |
| Question 1: right, partly right or wrong | |
| Question 2, as said | |
| Question 2: right, partly right or wrong | |
| Question 3, as said | |
| Question 3: right, partly right or wrong | |
| Misunderstandings seen | |
| Any dangerous misunderstanding? yes / no, and what | |
| Sprint 7 scope inputs | |

## 2 H-01 for Sprint 2: the You chapter and the slate (25 minutes)

A design review of what Sprint 2 built, at 1440 px and 390 px, testing scanning,
understanding and choosing. The earlier package's checklist is in `docs/reviews/sprint-2.md`
("Human design-review checklist").

**Captures** (`docs/reviews/sprint-2/screenshots/`, recaptured by `pnpm run review-screenshots`
in Task 11; `checks-*.json` beside them hold the automated checks, which are not a review):

- the start: `you--1440x900.png`, `you--390x844.png`;
- a reply with its proposed changes: `you--reply-to-review--1440x900.png`,
  `you--reply-to-review--390x844.png`;
- the slate: `you--slate--1440x900.png`, `you--slate--390x844.png`;
- for the checklist below: `you--reply-failed--*`, `you--support-note--*`,
  `you--key-consent--*` and `you--source-drawer--390x844.png`.

**Tasks:**

| Minutes | Task | Look for |
|---|---|---|
| 3 | Open the captures side by side, desktop then phone. | |
| 5 | **Scanning:** look at each first screen for ten seconds, then say what the page is for and what to do first. | Is the decision in view without scrolling? |
| 5 | **Understanding:** on the slate, pick one suggestion and say why it was suggested and what it rests on. | Is "Why this could suit you" read as resting on your answers? |
| 5 | **Choosing:** choose one suggestion and find how to make it a target. | Where does the phone's first screen hide the decision controls? |
| 7 | Score the rubric and answer the checklist. | |

### H-01 record sheet (not run - requires human)

Score each category 1 to 5 with a concrete defect for any score below 4 (plan section 5).

| Category | 1440 px | 390 px | Defects |
|---|---|---|---|
| Hierarchy | | | |
| Typography | | | |
| Spacing | | | |
| Visual identity | | | |
| Uncertainty communication | | | |
| Responsive composition | | | |
| Interaction continuity | | | |

| Item | Record |
|---|---|
| Scanning: what the page is for and the first step, as said | |
| Understanding: the suggestion explained, as said | |
| Choosing: the suggestion chosen; found the control? | |
| Where the first screen hides the decision controls (each size) | |

The Sprint 2 checklist (`docs/reviews/sprint-2.md`, "Human design-review checklist"): yes or
no for each of its seven items, with notes. The captures cover most of it; the parts they do
not show need the live app (`make demo`, then `http://127.0.0.1:53000`).

| # | Item | Captures | Needs the live app for | Yes / no, notes |
|---|---|---|---|---|
| 1 | Start | `you--1440x900.png`, `you--390x844.png` | | |
| 2 | Conversation | `you--reply-failed--*`, `you--reply-to-review--*` | an unchecked reply while it streams (or Storybook **You / Reply Streaming**) | |
| 3 | Review tray | `you--reply-to-review--*` | Confirm, Accept and Undo used in turn | |
| 4 | Slate | `you--slate--*` | | |
| 5 | Support panel | `you--support-note--*` | the panel beside a refused send (no capture exists) | |
| 6 | Key consent | `you--key-consent--*` | | |
| 7 | Phone | `you--390x844.png`, `you--source-drawer--390x844.png`, `you--reply-failed--390x844.png` | the reply field and Try again with the sheet open | |

## 3 H-07: the option pack, parts 1 and 2 (55 minutes)

`docs/reviews/session-2-option-pack-questions.md`, generated by Task 7b and unchanged:
part 1, P01's every row (Q1-Q67, about 17 minutes), then part 2, P03-P05's courses and the
funding (Q68-Q219, about 38 minutes). Answer in that file's last column, or on a copy with the
question numbers. Task 7c applies the answers by number; a record becomes `reviewed` only
when every one of its rows is answered yes.

## 4 H-07: the checker on P01's real option set (10 minutes)

`docs/reviews/session-2-checker-questions.md`, T1-T36, about 9 minutes. The checker that
reproduces TRACE-01 exactly, run on the courses pack 0.1.0 gives P01's target: what it read
about P01 (synthetic, part A), what it read from each page beside its span (part B), and what
it concluded (part C). Readiness is a partial sketch: no pack outcome has a level yet.

## 5 The capability reference and proposed outcome levels (20 minutes)

`docs/reviews/session-2-capability-questions.md`, R1-R58, about 19 minutes: the reference
Task 9 wrote (its targets' ESCO occupations, its rubrics with their required levels and
anchors, their ESCO skills, and the two gate types), then a proposed level for each of the
pack's 18 planned outcomes. The levels are an agent's proposals in this package only; pack
0.1.0 is not changed, and Task 7c publishes the levels you accept.

## 6 The decision sheet (10 minutes)

The provisional decisions the plan leaves to the product owner (ruling R6), as yes / no
questions. "No" needs a note with what to do instead. The controller may add any it still
holds before the session.

Two of ADR 0011's provisional decisions are not on this sheet: decision 10 (pack-local skill
rows) was taken by the controller as an internal identifier scheme and superseded by ADR 0012's
rubrics, and decision 12 (a restrictive copyright notice keeps a page pending) belongs to the
rights review before any push (OI-07).

| # | From | Decision | Yes / no, and a note if no |
|---|---|---|---|
| D1 | ADR 0011 decision 8 | P02 has no records in the pack, since its fixture gives it no target. | Yes: answered by the product owner on 2026-10-29, before the session |
| D2 | ADR 0011 decision 9 | Two statements on one page that disagree leave the field unknown, keeping both; a bound and a point at the same amount are not a disagreement, and the bound is the label ("Up to £28,000"). | Yes: answered by the product owner on 2026-10-29, before the session |
| D3 | ADR 0012 decision 3 | A requirement's importance is what the postings state (all essential, all preferred, or "disputed" for a mix); a disputed row counts as required until you decide; an ESCO-only row is unknown and never enters readiness. | |
| D4 | ADR 0012 decision 4 | A protected gate is satisfied only when you say you hold it and have verified it at its source (L0 checks no register); a regulated occupation with no typed gate keeps a gate no statement can satisfy. | |
| D5 | ADR 0012 decision 5 | "I did it with help" counts at most as level 1. | |
| D6 | ADR 0012 decision 5 (review M4) | A reviewed demonstration below a concrete self-report sets the level to the demonstration's (a self-report of 3 and an assessment of 1 give 1), flagged as a conflict to clarify. | |
| D7 | ADR 0012 decision 5 | Towards readiness count a reviewed demonstration's level, or else the latest self-report with an example and when it was last done; a level with no example counts for nothing. | |
| D8 | ADR 0012 decision 6 | In L0 an assessed result counts once you confirm the result and its assessor (there is no third-party reviewer). | |
| D9 | ADR 0012 decision 7 (review N6) | The right to work, or another eligibility statement alone, never makes a target "ready": that needs a skill row a rubric models or a modelled legal-practice or recognition gate. | |
| D10 | ADR 0012 decision 8 | The questions' order (essential 3, disputed 2, preferred 1, times uncertainty and targets served), stopping once 80% of the weighted required rows have usable evidence, and the twelve first prompts. | |
| D11 | ADR 0012 decision 10 | A target finds its pack target by the same title, or else by the one pack target whose ESCO crosswalk names its occupation; two candidates are never guessed between. | |
| D12 | ADR 0013 decision 4 | A whole fee with no stated payment date is taken as due in the course's first month, and so is each stated extra cost (such as a £13.99 certificate). | |
| D13 | ADR 0013 decision 4 | An intake given only as a month stands on the monthly grid as that month's first day. | |
| D14 | ADR 0013 decision 6 | The monthly deficit limit, if you set one, counts each month's payments, less support received, plus the pay lost against your baseline. | |
| D15 | ADR 0013 decision 6 | Today the model follows the specification (section 12: payments plus repayments within the monthly payment cap, `P_m + R_m ≤ M_m`), so repayments of debt you already have count against the cap as well as in the monthly cash. One effect: if those repayments alone are above the cap, every route fails the cap, even one that costs nothing. (The You chapter asks for the cap as the most you would spend in one month on the change.) Should they sit outside the monthly payment cap instead? (Yes changes the model; no keeps it.) | |
| D16 | ADR 0013 decision 8 | A readiness milestone reached at the month boundary that ends the comparison horizon counts as within it. | |
| D17 | ADR 0013 decision 9 | The delay scenario moves every conditional offer and award later by one number of months, declared for each comparison with no default, whoever the award is paid to: a fee waiver paid to the provider that arrives late leaves you paying the fees due before it. Course dates stay fixed. | |

## The session record (not run - requires human)

| Item | Record |
|---|---|
| Date and time | |
| Held by, and who took part | |
| Part 1 (H-13): done, partly or not; record sheet filled? | |
| Part 2 (H-01 Sprint 2): done, partly or not; scores recorded? | |
| Part 3 (Q1-Q219): the numbers answered | |
| Part 3, optional (Q220-Q344): the numbers answered, or left for Task 8 | |
| Part 4 (T1-T36): the numbers answered | |
| Part 5 (R1-R58): the numbers answered | |
| Part 6 (D1-D17): the numbers answered | |
| Where the answers are written (these files, or copies) | |
| Anything to change before Task 7c publishes the reviewed pack | |
