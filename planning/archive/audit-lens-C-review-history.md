# Audit lens C: review history — where the fix rounds went, and what they bought

Read-only lens of Task A1. HEAD 8e78060, branch `l0-local-release`.
Sources: the ledger `progress.md` (all 746 lines), 69 review and re-review files (about
13,600 lines; finding headings read for every file, bodies read where a classification
or a loop needed it), 37 fix-round briefs (sampled), the reports where a loop needed
context, `git log main..HEAD` (294 commits) with per-commit numstat, and the product
owner's records in `docs/reviews/`.

Paths below are relative to the repository root. "Ledger N" means `progress.md` line N.
"PO" means the product owner.

---

## 0. The answer in eight lines

1. 46 fix rounds over 21 reviewed units, 83 reviewer passes. 151 of the 294 branch commits
   are fix-round commits. Fix-round churn is about 58k lines against 120k for the first
   builds (0.48). Three units hit the 5-round breaker (Task 6, Task 7 slice A, W2B). They
   took 15 rounds (33%).
2. The rounds that bought the most for the person were about data and state truth:
   readiness, money, unknown versus none, and the AI score. Tasks 9, 11 and 7B each found a
   decision-changing defect in round 1 and converged in 1–3 rounds.
3. The rounds that bought the least were language-rule tails (about 10 rounds, 22%) and
   ESCO-wording tails (about 2–3 rounds). Each round found a new phrasing, a new escape form
   or a new false case, and each fix caused the next finding. Loops ended only when someone
   changed the rule, not the patch (ledger 174, 420, 698, 714).
4. About 30% of all findings were reviewer-only kinds: docs and register honesty (about
   86), tests that prove nothing (about 60), and contract or code hygiene (about 32). The
   reviewer contract promotes some of these to Important (`reviewer-contract.md:31-33`).
5. The PO's own top complaints get under 1% of findings: plain words, helper text, one
   idea per page. They got their first full fix round only in W2C part 1. That came ten
   fix rounds after session 2. The words they called "psychobabble" are still in the app
   (`apps/web/src/components/RoutePreview.tsx:119,123`).
6. About 35% of fix rounds (16) hardened backends that no screen shows yet: evidence
   acquisition, pay, the pack, readiness and the planning checker. Tasks 8, 10 and 12 are
   unbuilt. Their value to the person is real but latent, and the PO cannot judge it.
7. The "minors become must-fix" habit drove the long loops before R12 (ledger 41–362). R12
   was scoped "from Task 7b to session 2" (`docs/plan/l0-sprint-tasks.md:185`), so it lapsed,
   and Sprint W went back to fixing minors now (ledger 589, 594; W2A fix list 13 minors).
8. Recommendation in one line: keep data, state and lost-input review hard. Make R12
   permanent. Replace wording patches with "say what Careerwright did, never what a source
   contains". Let the PO judge matching. Bound loops by finding class, not by round count.

---

## 1. Per-task table

Kind codes, used in every table:
- LANG: language-rule patterns (support-screen stems, quotation validator word lists,
  redaction patterns, pay and work-mode readers)
- WORD: truth of a shown or published sentence or label (UI copy, notes, API descriptions,
  synthetic labels)
- PLAIN: plain words and helper text
- DATA: data and state correctness (money, dates, readiness, unknown versus none or zero,
  coverage, provenance)
- MATCH: matching and ranking rules
- SEC: security, privacy, rights, concurrency
- SPEND: spend bounds and the cost ledger
- INPUT: lost input, broken interaction, recovery, robustness
- LAYOUT: layout, crowding, small screens
- A11Y: accessibility
- VIS: visual style, colour meaning, look and feel
- TEST: tests that prove nothing, coverage gaps
- DOCS: docs, register, ADR and evidence honesty
- PKG: the PO's session packages, decision sheets and plan gaps
- CODE: contract types, dead code, structure
- OTHER: scope, process, operations

Counts include every Critical, Important and Minor raised in the review and its
re-reviews. Classification is from the finding headings, so counts are ±15%. Tasks 1 and 2
have no review files; their counts come from the ledger's summaries.

Columns:
- Rounds: fix rounds.
- Passes: reviewer passes.
- Fix commits / churn: fix-round commits only, insertions plus deletions, with lockfiles
  and the generated client excluded.
- Ratio: fix churn over first-build churn.

| Unit | Rounds / passes | Findings by kind (≈ count) | What the rounds bought the person | Value | Fix commits / churn (ratio) |
|---|---|---|---|---|---|
| T1 Spikes | 1 / 2 | SPEND 3, DOCS 3, DATA 2, other 4 (≈12) | Paid calls never unledgered; typed provider failures | Low (dev spike); medium for the PO's cost rule | 2 / 1,151 (0.32) |
| T2 Design refs, register | 1 / 2 | DOCS 3, WORD 2, VIS 1, LAYOUT 1, other 5 (≈12) | Route chart no longer draws a dominated route on the boundary; the phone sheet no longer hides the main task | Medium (later UI copies these) | 5 / 559 (0.08) |
| T3 Platform | 3 / 5 | SEC 14, SPEND 9, CODE 6, DOCS 4, DATA 3, TEST 3 (39) | Round 1: master-key rotation would have made run outputs unreadable; revocation, isolation. Rounds 2–3: the developer's `live-smoke` ledger (ledger 73, 79) | R1 high (data loss); R2–3 low for the person | 11 / 3,499 (0.23) |
| T4 Web shell | 2 / 4 | TEST 8, DATA 6, DOCS 6, A11Y 5, INPUT 4, CODE 3, SEC 2, WORD 2, other 3 (39) | A stale save no longer reverts someone else's changes (A-I2); tokens out of localStorage; Unknown/Skipped no longer block chapters; truncated lists not shown as complete | High | 14 / 3,084 (0.33) |
| T5 ESCO, interview runs | 2 / 4 | DATA 9, TEST 6, SPEND 5, DOCS 5, CODE 5, MATCH 2, WORD 2, other 4 (38) | An outage no longer reads "over budget"; the true cost is booked; streaming was added as scope (ledger 119) | Medium | 9 / 2,869 (0.37) |
| T6 Discovery, support, You | 5 + follow-up / 7 (+1 aborted) | LANG 19, DOCS 11, TEST 10, DATA 8, MATCH 5, INPUT 5, WORD 4, A11Y 4, CODE 3, SPEND 2, other 2 (≈73) | R1: tray edits no longer lost; unrelated jobs no longer folded; salary period checked. R2–R5: the support screen, from blocking, to two-tier intent, to a one-list non-blocking screen, to proximity rules; R5 then tokenisation | R1 high. Redesign (R4) high. R2–R3 nothing kept. R5 and follow-up tail low–medium | 16 / 7,543 (0.62) |
| Plan update | 1 / 2 | DOCS 6, PKG 2 (8) | No release on an unreviewed pack (Task 7c added) | High for the build | 1 / 263 |
| T6b Span-cited note | 3 / 4 | LANG 12, INPUT 4, DOCS 3, SPEND 1, WORD 1 (21) | R1: the note can't claim "qualified" or "paid" from the person's words; a failed note can be retried. R2–R3: quote-shape tail (apostrophes, quote marks), each one a paid repair; R2 broke the demo note (ledger 231) | R1 medium–high; R2–R3 low | 9 / 2,052 (0.59) |
| Session 1 transcription | 1 / 2 | DOCS 5, WORD 2, LANG 1 (8) | "Provisional" removed from the distress panel; "isn't going to exist" no longer shows the panel | Medium (small) | 2 / 166 |
| T6c Visual batch | 1 / 2 | DOCS 4, WORD 1 (5) | Records accurate | Low | 1 / 58 |
| T7A Acquisition | 5 + addendum / 15 | LANG 19 (15 redaction, 4 value readers), SEC 18, DATA 17 (14 state honesty), SPEND 7, INPUT 7, CODE 6, DOCS 5, TEST 4, OTHER 3 (≈86) | R1: an unread page no longer says "none found"; a truncated search no longer looks complete; javascript: links and SSRF via redirects closed; retention not raised by a page's own claim. R2: residuals plus model extraction (scope). R3–R5: redaction escape forms (NBSP, JS escapes, inline markup, entities, percent-encoding, @2x), the pay reader, the spend ceiling, lock order | R1 high (latent: no jobs screen). R3–R5 medium–low (third parties' details; most fixes fail safe) | 39 / 12,011 (1.16; includes extraction) |
| T7B Pay, AI evidence | 2 / 5 | DATA 14, WORD 4, TEST 4, DOCS 4, PKG 1 (27) | An open-ended "From £24,000" no longer removes a vacancy; an exposure-only AI score is never published; found that the pinned ASHE table publishes no percentile, so the floor is inert (ledger 450) | High | 5 / 1,066 (0.18) |
| T7d Lock order | 1 / 2 | CODE 1, DOCS 1, TEST 1 (3) | A 409 kept where a race gave 202 | Low (the first build's deadlock fix was the value) | 3 / 275 |
| T7b Option pack | 3 / 4 | DATA 10, DOCS 6, PKG 2, TEST 2, OTHER 3 (23) | A grant keeps "not repayable"; durations and patterns typed; session 2 package made complete | Medium (latent); the package's completeness bought little, because the PO checked Q1–Q15 and delegated Q16–Q344 to an AI | 7 / 5,642 (1.65; pack re-cuts) |
| T9 Capability | 3 / 4 | DATA 17, DOCS 2, TEST 2, CODE 2, MATCH 1, WORD 1 (25) | Nursing no longer reads "ready now" without the NMC gate (C1); "not yet assessed" no longer reads "not ready"; self-entered evidence not shown as corroborated | High (latent: no Skills screen) | 6 / 1,900 (0.31) |
| T11 Planning checker | 1 / 2 | DATA 9, PKG 5, DOCS 3, CODE 2, TEST 2 (21) | An unknown cap no longer passes; a payment before the start no longer dropped; a qualified readiness no longer gives an unqualified verdict | High (latent: no Options screen) | 3 / 935 (0.16) |
| W1 World spike | 2 / 3 | VIS 8, A11Y 4, LAYOUT 3, DOCS 3, PKG 3, other 4 (≈25) | A fair three-way choice for session W1: same face, Chrome opens, words don't vanish, one idea at a time | Medium (spike code thrown away, ledger 601) | 4 / 3,458 (0.54) |
| T7c Reviewed pack | 1 / 2 | DATA 6, DOCS 2, TEST 2 (10) | No value served that the reviewer marked "?"; the funding earnings rule kept | Medium–high (latent) | 1 / 337 |
| W2A World layer | 2 / 4 | LAYOUT 14, DOCS 8, WORD 6, A11Y 5, VIS 5, TEST 5, INPUT 3, PLAIN 2, other 4 (52) | The world is visible on tablet and phone; motion resumes after typing; a WebGL failure no longer leaves a blank world; trails pass 3:1 as drawn; the PO's cost words cut from the references | Medium–high | 4 / 4,601 (0.42) |
| W2B Deterministic sources | 5 / 6 | WORD 19, MATCH 12, TEST 9, DATA 5, DOCS 2, INPUT 1 (48) | R1: the type-ahead finds titles for 3 of 5 personas (was 0). R1–R3: matching through essential skills only, no alphabetical ties, generic answers don't retrieve, so slates are smaller or empty. R4–R5: note sentences about "what ESCO contains" made true | R1 type-ahead high; R1–R3 matching unproven (PO hasn't judged); R4–R5 low | 5 / 4,500 (1.18) |
| W2C part 1 You chapter | 1 (re-review not run) / 2 | LAYOUT 7, VIS 5, A11Y 3, PLAIN 2, WORD 2, other 4 (23) | Typed input no longer lost when switching views (A-I1); one decision per view; the bright action above the fold; helper text cut; world above the console on small screens | High | 4 / 1,875 (0.64) |

**Totals by kind (≈600 findings)**

| Kind | ≈ Count | Share | Where it concentrates | Typical value to the person |
|---|---|---|---|---|
| DATA | 106 | 18% | T9, T7A, T7B, T7b, T11, T5 | High: decisions (ready, feasible, eligible, pay) rest on it |
| DOCS | 86 | 14% | every task (register "verified" claims, ADR wording) | Low; it matters at release (R2 honesty), not per round |
| TEST | 60 | 10% | T6, W2B, T4, T5, W2A | Medium, indirect: vacuous tests hid real defects (W2A parity test; W2C1 checks passing a CSS regression; T6's 692-row table generated from its own lists, ledger 179) |
| LANG | 51 | 9% | T6, T7A, T6b | Head findings high (blocking distress screen; a model claiming "qualified"); tails low |
| WORD | 46 | 8% | W2B (19), W2A, T7B | Medium where it misleads a decision; low for edge cases about ESCO's contents |
| SEC | 38 | 6% | T3, T7A | Medium–high (local, loopback, single user, but it fetches the open web) |
| CODE | 32 | 5% | T3, T7A, T5 | Low |
| SPEND | 28 | 5% | T3, T7A, T5 | Medium for the person's own key; low for developer tools |
| INPUT | 26 | 4% | T7A (robustness), T6, T6b, T4 | High (lost work) |
| LAYOUT | 26 | 4% | W2A, W2C1 | Medium–high when the main decision is hidden; low for polish |
| MATCH | 21 | 4% | W2B, T6 | High in intent, but only the PO can judge it |
| A11Y | 21 | 4% | T4, T6, W1, W2A | Medium |
| VIS | 20 | 3% | W1, W2A, W2C1 | Medium (the PO cares about the look, but second to use) |
| PKG | 15 | 3% | T11, W1, T7b | Medium for the PO's sessions |
| OTHER | 18 | 3% | T1, T2, T7A | — |
| PLAIN | 5 | <1% | W2A, W2C1, T11 | High: it is the PO's own top complaint |

**Fix rounds by their main kind (46)**

| Main kind of the round | ≈ Rounds | Which |
|---|---|---|
| DATA and state truth | 12 (26%) | T7B r1–2, T7b r1–3, T9 r1–3, T11, T7c, parts of T4 r1, T5 r1, T7A r1–2 |
| LANG tails | 10 (22%) | T6 r2–r5 and follow-up, T6b r1–r3, T7A ≈2 of r3–r5, part of S1T |
| MATCH and WORD (the slate) | 5.5 (12%) | W2B r1–r5, part of T6 r1 |
| DOCS and PKG | 5 (11%) | T2, plan update, S1T, T6c, parts of T1 and T7d |
| LAYOUT and VIS | 4.5 (10%) | W1 r1–2, W2A r1–2, part of W2C1 |
| SPEND (developer ledger, reservations) | 3 (7%) | T3 r2–3, parts of T1, T5 r2, T7A r4–5 |
| SEC | 2.5 (5%) | T3 r1, parts of T7A r1–2, T7d |
| INPUT and A11Y | 2.5 (5%) | T4 r2, parts of T4 r1, T6 r1, W2C1 |

---

## 2. Patterns

### 2.1 Kinds that recur

| Pattern | Evidence | Judgment |
|---|---|---|
| Data and state truth defects turn up in every backend task's first review, and close fast | T9 C1 and I1 (`task-9-review.md`); T11 I1–I3 (`task-11-review.md`); 7B A-I1 and B-I1; 7A B-C1 and B-I3; T5 B-I2. Each closed in 1–3 rounds | The review loop's best value per round. Keep it (confidence high) |
| Register and ADR overclaims recur in nearly every review | DOCS findings in 20 of 21 units. Examples: T4 B-I2 ("STATE-07 marked verified"); T6 B-I5; T6 rr4 M-1, M-2 ("692 rows reads as coverage"); 7A rr1-A C-1 ("ACQ-06 overclaims the redaction") | A by-product of closing register rows per task. Cheap one at a time, but present in every round. Batch it (§4 R-7) |
| Vacuous tests recur, and some hid person-visible defects | T4 A-I5 (assertion-free resume test); T6 A-M1 (vacuous 404); ledger 179 (the 692-row table "generated from the patterns' own word lists, so it can't find gaps"); W2A app I3 (the parity test "can't fail for what it claims"); W2C1 design I1 ("the checks pass it"); W2B rr2 N-M3, rr3 M3 (pass by construction) | Keep checking tests that guard a person-facing invariant. Park the rest |
| Fix rounds in the language-rule loops cause regressions | T6 rr3 C-1 (round 3 drops shapes, ledger 173); rr4 I-2 (refused turns lose the panel, ledger 179); rr5 N-I1 (the dash regression, ledger 184); T6b rr2 R3-I1 (the demo note breaks, ledger 231). None reported in T9, T11 or 7B | Pattern-extension fixes are fragile. The tail rounds partly fixed their own regressions |
| Phone and tablet layout is a large share of Sprint W findings | About half of the 26 LAYOUT findings (≈13) are at 768 or 390 px (W2A design I5, app I4, rr1 M1–M3 and M6; W2C1 D-I2, A-M1, A-M6). The PO skipped phone review: "skip this - it's a waste of time until we've fixed this mess of a page" (`docs/reviews/session-2-answers.md:42`) | Valid where the world or the main decision is hidden (W2A app I4). Polish findings (leader lines, wrapped markers) ran ahead of the PO's priority (judgment, medium) |

### 2.2 Loops that did not converge, and what ended them

| Loop | Rounds | Why it kept going | What ended it | What it bought |
|---|---|---|---|---|
| T6 support screen | r1 + r2–r5 + follow-up | The first fix tried to judge intent (two tiers, ledger 159). Each re-review found a new phrasing that reached the wrong tier or no tier (ledger 168, 173, 179, 184). The round-4 test table was generated from the patterns, so it could not find gaps (ledger 179) | The controller stopped the classifier: "two failed fixes in one direction → wrong hypothesis" (ledger 174). Then a token-and-proximity screen (ledger 180), the breaker (ledger 184), and parking residuals as H-12 known limits (ledger 185–186). The PO later accepted exactly that design and its limits (`docs/reviews/session-1.md:41-45`) | The non-blocking panel: high. Rounds 2–3 (intent tiers): nothing kept. Rounds 5 and the follow-up: grammar, dash and apostrophe variants, "nothing load-bearing for synthetic local use" (ledger 184) |
| T7A redaction tail | r3–r5 (inside a 5-round task) | "The rights clause is absolute" was applied to every new escape form, and every rights Minor was upgraded (ledger 301, 309, 322, 340, 345, 358, 362, 376, 390). Each round found one more encoding: JSON escapes, NBSP, JS escapes, inline markup, entities, percent-encoding, sentence boundaries, @2x | The breaker at round 5 (ledger 405). Then R11, triggered by the PO-supplied review: "Put a firm boundary around language-rule refinement" (`docs/reviews/intermediate-code-review-2026-10-29.md:42`), adopted at ledger 420 | Third parties' emails and phones kept out of kept bodies and Meta input: medium. Most late fixes fail safe (body not kept), with their own false positives (R5-1, R6-1) |
| T6b quote validator | 3 | Each shape of quotation found a new bypass or a new false refusal ("s" fragments, apostrophes, quote marks), and each refusal costs a paid repair | The same re-reviewer, resumed, approved round 3 (ledger 236). Known false positives were accepted for H-12 (ledger 232). The PO said "yes" to all five item-7 questions (`docs/reviews/session-1.md`, addendum) | R1 high. R2–R3 low (test-model repairs cost a fraction of a cent) |
| W2B matching | r1–r3 | Each reviewer found the slate "still arbitrary" by a new route: description words, skill-label words, alphabetical ties, generic answers (`task-W2B-rereview-1.md:33-80`; ledger 687, 694). Reviewers proposed rules that the next reviewer critiqued (ledger 688) | A loop bound: "round 3 is the last matching-quality round … the PO is the judge of suggestion quality" (ledger 698) | The type-ahead fix was high. The rest is unproven. The PO's own case ("data analyst") was already fixed by the first build and did not change in any fix round (`task-W2B-report.md:94,347,617`). P01, P04, P05 and common answers now give empty slates (`task-W2B-report.md:862-868`) |
| W2B note wording | r3–r5 (+ carried into W2C) | The truth rule "no note claims something untrue" (`task-W2B-rereview-3-dispatch.md:23-25`) let every fresh reviewer search for a counterexample. One false sentence was "the ruled wording: re-review 2 suggested it, and the controller adopted it" (`task-W2B-rereview-3.md:156-158`). Five different re-reviewers were used (ledger 686, 693, 704, 712, 719) | A rule, not a fifth wording: "every note describes what the search did … never what ESCO contains" (ledger 714). Then the breaker (ledger 721), with the false lines outside the slice carried to W2C (ledger 722) | Low. Each false case is rare (for example, 2,582 skills essential to no occupation). The rule made the words more technical: "cost if wrong: slightly more technical wording" (ledger 714); "'Main name' is new to the person. Is it plain enough?" (`task-W2B-rereview-5.md:213`) |
| T9 readiness | 3 | Each re-review found a narrower edge (C1(b), N1, R2-1, R2-2, R3-1) | Converged with a resumed reviewer (ledger 526–539); the last edge was parked | High (every edge changes a "ready" answer) |

### 2.3 Rules and processes that produce loops

| Mechanism | Evidence | Effect |
|---|---|---|
| Open-ended truth checks with no person-impact test | The reviewer contract makes "cannot be trusted until fixed" Important, and lists "tests asserting nothing, verbatim logic duplication" as Important (`reviewer-contract.md:31-33`). Re-review dispatches ask that "no note claims something untrue" (`task-W2B-rereview-3-dispatch.md:23-25`) | Any untrue sentence in any edge case becomes Important and a new round. That drove W2B r3–r5 and T6 rr4–rr5's "claims say exactly what is covered" (ledger 180, 184) |
| Minors upgraded to must-fix | Upgrade rulings at ledger 41, 53, 66, 68, 96, 120, 152, 219, 267, 301, 309, 322, 340, 349, 362. After R12 (ledger 421): parking at 439, 453, 457, 470, 490, 523, 540, 557, 564. R12 is scoped "From Task 7b to session 2" (`docs/plan/l0-sprint-tasks.md:185`), so it lapsed. Sprint W fixed minors again: ledger 589, 594; `task-W2A-fix-round-1.md:70-71` (13 minors fixed now); `task-W2A-rereview-1.md:40,65` ("Minor (fix now)"); `task-W2C1-fix-round-1.md:50-57` (10 of 15) | Long fix lists, more surface for regressions, and more re-review findings. Units under R12 (7B, 7d, 7b, 9, 11) averaged 2.0 rounds; the units before it (3, 4, 5, 6, 6b, 7A) averaged 3.3. The work also differed in kind, so this is suggestive, not proof (confidence medium) |
| Absolute clauses applied to patterns | "The rights clause is absolute" (ledger 323, 345, 358); "claims say exactly what is covered" (ledger 180) | Every new form is a must-fix. Closed only by R11 (`docs/plan/l0-sprint-tasks.md:176-184`). R11 lists stems, word lists, redaction and value readers, but not slate notes or matching rules, so W2B's loops fell outside it |
| A fresh re-reviewer each round | W2B: five different re-reviewer agents. T6b (ledger 224, 230, 235) and T9 (ledger 526, 533, 538) resumed one reviewer and converged. T7A resumed its reviewers and still looped on redaction | A fresh reviewer searches widely and opens new classes. Resuming helps only where no absolute clause is in play (confidence medium–low) |
| Policy questions settled by reviewers, not the PO | The support-screen design (recall versus intent) was settled by controller rulings over 5 rounds. The PO was asked only at session 1, after the loop, and accepted the simple design (`docs/reviews/session-1.md:41-45`). The trade between empty and arbitrary slates was ruled by the controller (ledger 688, 695); the PO hasn't seen it (`task-W2B-report.md:729-730`) | Rounds spent on questions with no code answer |
| Large slices | Implementer contexts: 646k for Task 6 (ledger 270), about 700k for W2A (ledger 652), about 830k for W2B (ledger 682), about 762k for W2C1 (ledger 738). W2A's first review raised 13 Important across its two halves (ledger 641, 646) | Long fix lists and fresh implementers per round (re-reading cost). The split precedents worked: Task 7 into A and B (ledger 270); W2 into four slices (ledger 625); W2C into two parts (ledger 726) |

### 2.4 Latent value: backend correctness with no screen yet

- 16 fix rounds (7A 5, 7B 2, 7d 1, 7b 3, 9 3, 11 1, 7c 1) hardened contracts that no screen
  shows: "no web code renders APPLY_URL yet" (ledger 280); "no UI renders model_extraction
  (Task 8)" (ledger 330). The Skills, map, Options and Routes chapters are unbuilt
  (`handover-2026-10-31.md`, section 4).
- The findings were real: "ready now" for nursing without the NMC gate, an unknown cap
  passing, "none found" for an unread page. But neither the person nor the PO can see or
  judge them yet. Next reviews of Tasks 8, 10 and 12 should check that these contracts show
  correctly on screen. That is where the value lands.

### 2.5 Things that broke for the PO, which no review caught

- `make demo` was refused because a live-eval file was created 0644. The PO hit it
  themselves (ledger 569).
- The DBOS worker-shutdown hang, noted in Task 1 (ledger 44, 47), recurred in W2B's
  acceptance run (ledger 674). Every recurrence costs a re-run.
- A stress scene opened in a headed window looked to the PO like the product:
  "Wow, the scene looked too busy. was overwhelming" (ledger 635).

---

## 3. What the PO asked for, against where the review effort went

| What the PO asked | Source | Review effort | State at HEAD |
|---|---|---|---|
| Plain words on the money and route screen ("psychobabble"; "don't understand … the difference between economic cost and direct cost"; "the language is inaccessible") | `docs/reviews/session-2-answers.md:8-10` | W2A design I7 and M2; T11 M6 ("the T set is hard going"). About 0.3 rounds | Still in the app: `RoutePreview.tsx:119,123` ("Economic cost", "Direct spending"). Carried W2A → W2D (ledger 656) |
| Chat first; tone moved to preferences; one idea per page; less helper text; "too much on one page" | `session-2-answers.md:37-38,46` | W2C1 dispatch (`task-W2C1-dispatch.md:38-40`); design review I3–I5, M4–M6. 1 round | Fixed in W2C1 fix round 1; its re-review has not run |
| Suggestions that aren't "arbitrary matching on keywords" (from "data analyst") | `session-2-answers.md:22` | W2B: the first build plus rounds 1–3; 12 MATCH findings | "data analyst" was fixed by the first build (`task-W2B-report.md:94`) and unchanged after. Other personas and common answers are now empty. Not yet judged by the PO |
| A bright primary button | `session-2-answers.md:23` | W2C1 design I3 | Fixed in fix round 1 (re-review pending) |
| Accept and undo colour-coded | `session-2-answers.md:48` | W2C1 commit 5c14792; D-M3 parked | Built; colour-blind check goes to session W2 (ledger 736) |
| "What do these mean??" (the spending and payment limits) | `session-2-answers.md:39` | W2C1 A-M4 (tray limit meaning untested) | Partly addressed |
| Phone review deferred: "waste of time until we've fixed this mess of a page" | `session-2-answers.md:42` | About 13 phone and tablet LAYOUT findings in Sprint W, plus phone A11Y items | Effort ran ahead of the PO's priority. Hidden-decision cases are still valid |
| A "revolutionary" look; Horizon made livelier; solid trails; sound "subtle and evocative" | `session-2-answers.md:550`; `docs/reviews/session-w1-answers.md` | W1 2 rounds, W2A 2 rounds | Built. On the real references the PO said "no, they look OK" (ledger 640) |
| A firm boundary on language-rule refinement (in the review the PO supplied) | `intermediate-code-review-2026-10-29.md:42` | R11 adopted (ledger 420) | Worked for 7B–11. W2B's wording and matching loops fell outside R11's list |
| Real evidence before polish (same review) | same file, point 2 | 7b, 9, 11 and 7c: 8 rounds | Done. Value latent until the chapters exist |
| Support screen: accept one word-list screen with its known limits | `session-1.md:41-45` | T6 r2–r5 and the follow-up (4.5 rounds), all before the PO was asked | The PO accepted the design the loop ended on. The intent-tier rounds bought nothing that was kept |
| Rights: policy yes; names in running text "yes"; "Do as you think best" | `session-1.md` (Part A and addenda) | 7A r3–r5 redaction tail under "the rights clause is absolute" | The PO's stance was more relaxed than the review standard |
| "Visuals subservient to a practical, useful product" | `audit-lens-common.md:14-15` | Sprint W: 10 fix rounds (W1 2, W2A 2, W2B 5, W2C1 1), while Skills, map, Routes and Plan are unbuilt | — |
| Skill frequency across many similar-level jobs (D3 comment) | `session-2-answers.md:527` | None yet | Carried to Task 10 (`carry-forward-task-10.md:11`) |

Order matters too. Session 2 ended on 2026-10-30 with the first-screen complaints. Ten
fix rounds on other work came before the first round aimed at them, W2C part 1 on
2026-10-31: W1 2, 7c 1, W2A 2, W2B 5 (ledger 571–741).

---

## 4. Recommendations for the remaining work

| # | Recommendation | Evidence | Confidence |
|---|---|---|---|
| R-1 | **Keep reviewing hard, and fix in the task:** state and data truth that changes a decision (ready or not, feasible or unresolved, unknown versus none, money values, eligibility); lost input; links, tokens and fetch safety; the support panel always showing and never blocking; the first ten seconds | T9 C1, I1; T11 I1–I3; 7B A-I1, B-I1; 7A B-C1, B-I3, A-I5; T4 A-I2; W2C1 A-I1; W2B I5. All converged in 1–3 rounds | High |
| R-2 | **Make R12 permanent** for every remaining task, Sprint W included. Minors park by default; fix now only for R-1 kinds, a PO session finding, or a failing check | R12's window (`l0-sprint-tasks.md:185`); minors re-upgraded once it lapsed (ledger 589, 594; `task-W2A-fix-round-1.md:70-71`; `task-W2C1-fix-round-1.md:50-57`) | High |
| R-3 | **Replace wording patches with two standing rules**, offered for CLAUDE.md: (a) "A sentence says what Careerwright did or checked, never what a source contains or what a screen catches." It applies to Task 8 ("none found"), Task 10 (readiness) and Task 12 (verdicts). (b) "When exact and plain conflict, say less": a shorter true sentence, not a longer exact one | Ledger 714 (it ended W2B's loop); T6 rr4 M-1/M-2 and rr5 N-M3/N-M4; 7A rr1-A C-1; W2C1 A-I3. The plain-words cost: `task-W2B-rereview-5.md:213`, ledger 714, `session-2-answers.md:9` | Medium–high |
| R-4 | **Widen R11 to slate notes and matching rules. Let the PO judge matching quality** on a fixed before-and-after case set (P01–P05, "data analyst", the common answers), with pass criteria agreed before the round. At most one matching fix round per slice; anything else goes to the session sheet | Ledger 698; `task-W2B-rereview-1.md:33-80`; `task-W2B-report.md:862-868` | High |
| R-5 | **Bound loops by finding class.** When one class (a false note, a missed stem, an escape form) recurs in two re-reviews in a row, stop patching: choose a rule, a fail-safe, or a one-line PO question. Lower the breaker to 3 rounds for wording, matching and visual work; keep 5 for security, money and data | T6 ended this way at round 4 (ledger 174); W2B at rounds 3 and 5 (ledger 698, 714); T7A only at the breaker (ledger 405) | Medium–high |
| R-6 | **Scope re-reviews to the fix list and its regressions.** New findings outside it are raised only at R-1 severity. Resume the same re-reviewer across rounds | W2B: five fresh re-reviewers, each opening new classes (ledger 686–719). T6b and T9 converged with one resumed reviewer (ledger 224–236, 526–539) | Medium |
| R-7 | **Grade severity by its effect on the person.** In `reviewer-contract.md`, add one line: high = they would act on it, lose work or be harmed; medium = they would notice; low = only a reviewer would. Docs, register, code-hygiene and vacuous-test findings become one batched docs-and-tests pass per sprint and at the final review, unless a vacuous test hides an R-1 defect | `reviewer-contract.md:31-33`; DOCS + TEST + CODE ≈ 178 of ≈ 600 findings | Medium |
| R-8 | **Smaller slices:** one chapter view or one backend contract per slice; aim for a diff of about 3–4k lines and an implementer context well under 500k. Keep the two-half review (design and experience; app, truth and tests) | Contexts of 646k–830k (ledger 270, 652, 682, 738); W2A's 13 Important; the split precedents (ledger 270, 625, 726) | Medium |
| R-9 | **Ask the PO before round 2 of any policy loop** (recall versus precision; empty versus arbitrary; strict versus relaxed redaction), as one yes-or-no line that says what "yes" does | The support-screen design accepted by the PO only after the loop (`session-1.md:41-45`); empty slates still unjudged (`task-W2B-report.md:729-730`); the PO's relaxed rights answers (`session-1.md`, addenda) | High |
| R-10 | **Start the design review from the PO's own session words.** Every task that touches a screen the PO commented on lists each comment as done or not done, and a not-done comment cannot be carried twice without asking the PO | The W2C1 dispatch did this (`task-W2C1-dispatch.md:38-40`) and its review found I3–I5. The route words were carried twice and are still on screen (ledger 656; `RoutePreview.tsx:119,123`) | High |
| R-11 | **Review what the person sees from the hardened backends.** Tasks 8, 10 and 12 should be reviewed end to end: does each guaranteed state (unread, unresolved, insufficient coverage, qualified) appear in plain words on screen? Do not re-review the backend rules again | Section 2.4; ledger 280, 330 | Medium (the plan lens owns the order) |
| R-12 | **Add the PO's own commands to acceptance** (`make demo`, `make setup`, opening each session package), and fix the recurring DBOS shutdown hang | Ledger 569 (the PO hit a refused `make demo`); ledger 44, 47, 674 (the hang) | Medium |

---

## 5. What I could not check

- Tasks 1 and 2 have no review files. Their findings by kind come from the ledger's
  one-line summaries (ledger 40–41, 52–53).
- Findings were classified from their headings, with bodies read only where a loop needed
  it. Per-kind counts are ±15%, and some findings fit two kinds.
- Person-visible value is my judgment from the review texts and the PO's records. I did not
  run the app (no Docker, no browser, by the audit rules).
- W2C part 1's fix round 1 has no re-review yet, so its value is unverified.
- The cost per round is in commits and churn only. Tokens and wall time are recorded only
  for some rounds (implementer contexts at ledger 270, 652, 662, 682, 738; times in Task 7A,
  ledger 303–392).
- Churn counts docs, pack data and scope work: 7A round 2 built model extraction, and 7b's
  rounds re-cut the pack. The fix-to-build ratios for those units overstate rework.
- I cannot separate R11 and R12's effect from the simpler nature of Tasks 7B–11. The
  "2.0 against 3.3 rounds" figure is suggestive only.
- I did not read the agent visual critiques (`docs/reviews/sprint-0.md`, `sprint-1.md`,
  `sprint-2.md`: V-01 to V-10, S0-V01 to S0-V08) in full. They are agent pre-reviews, not
  the PO's words, and I counted them only through the ledger's routing (ledger 136, 144).
- Whether resuming the same re-reviewer causes convergence is inferred from three cases (T6b,
  T9 converged; T7A did not), so the confidence is low.
