# Task 6c report: Sprint 0–1 visual corrections and the `next` age-exception removal

Branch `l0-local-release`, from `e5365e1`. Implementer: Task 6c agent. Not pushed. No live
Meta call (none needed); no subagent dispatched.

## Commits

| SHA | Subject |
|---|---|
| `4e3f518` | Tick only the approved counterfactual run; the pass rule and fields stay open |
| `ac94bf4` | Remove the next 16.4.1 age exception now that it is 14 days old |
| `ba5be08` | Correct the Sprint 0 compositions for S0-V01 to S0-V08 and recapture them |
| `574965a` | Plan says plan selection isn't built and what its one action is for (V-06) |
| `0ddbbac` | One headline on the refused account; a short data mode with its explanation |
| `f67d531` | Route cards keep their condition, the phone sheet leads with the figures |
| `2c63b5b` | Recapture the views Task 6c touches and record the dispositions |
| `62f1016` | Transcribe H-12 item 7: the written explanation, asked after session 1 (coordinator addition, docs only) |

## What was implemented

### 1. The `next` 16.4.1 age exception (ADR 0005 decision 1, removal step)

- `apps/web/pnpm-workspace.yaml`: `minimumReleaseAgeExclude` deleted; `minimumReleaseAge:
  20160` kept, comment now says "with no exception".
- Evidence (run 2026-10-28 ~21:55Z, after the 17:43Z removal time):
  - `cd apps/web && pnpm install --frozen-lockfile` → "Lockfile is up to date … Already up
    to date", exit 0; `shasum -a 256 -c` of `pnpm-lock.yaml` before/after → OK (unchanged).
  - Because a frozen install skips resolution, I also proved the age rule is active and that
    16.4.1 passes it without the exception: in a scratch copy of `package.json`,
    `pnpm-lock.yaml` and the edited `pnpm-workspace.yaml`, `pnpm add next@16.4.1
    --save-exact --lockfile-only` → exit 0, lockfile and package.json byte-identical to the
    repo's; `pnpm add next@16.4.3 --save-exact --lockfile-only` (published 2026-10-23, 5 days
    old) → refused (exit 1, the pnpm "minimumReleaseAgeExclude" hint). 16.4.1 was published
    2026-10-14T17:43:55Z (`pnpm view next time`). Scratch copy deleted.
- ADR 0005 (status line and decision 1), `docs/dependencies.md` (the `next` row and the
  exceptions list), register ARC1-03: the exception is recorded as removed.
- **Proposed `CLAUDE.md` edit (not made; for the user's approval).** In "Repository facts →
  Compatibility boundary", replace

  > the exact pins in `apps/web/package.json` and its lockfile (at least 14 days old,
  > enforced by pnpm; one provisional exception, `next` 16.4.1, to remove per ADR 0005
  > decision 1; record each in `docs/dependencies.md`)

  with

  > the exact pins in `apps/web/package.json` and its lockfile (at least 14 days old,
  > enforced by pnpm, with no exception; record each in `docs/dependencies.md`)

### 2. ADR 0007 checklist carry-over (controller ruling, docs only)

- `docs/adr/0007-conversation-discovery-and-support.md`: the "Counterfactual tolerance" item
  is split. Ticked: **Counterfactual comparison run**, approved as session 1 Part B line 6
  puts it ("run the powered comparison at release, estimated at most $0.07 on the test
  model", Task 16). New unticked item: **Counterfactual tolerance**, the pass rule across
  several samples per arm and the fields, not asked at session 1, to be decided before Task
  16, with the Task 6 report's derived figures kept as "not asked"; "Not run — requires
  human". Nothing else in ADR 0007 changed (`git show 4e3f518 -- docs/adr` is that hunk only).
- Register: H-12 then read "six of eight checklist items done" with the open items named (now
  "seven of nine" after 2b below); the session 1 row likewise; REC1-09's "still open" adds "and the fields
  compared (… an unticked item in its checklist)".

### 2b. H-12 item 7, "Written explanation" (coordinator addition mid-task, docs only, `62f1016`)

Source: `.superpowers/sdd/l0-sprint-tasks/session-1-addendum-item7.md` (five questions asked
in the chat on 2026-10-28 after the package; answer "yes yes yes yes yes").

- `docs/reviews/session-1.md`: new section "Addendum (2026-10-28): H-12 item 7 …" with the
  five questions and answers and the "Not asked" line copied exactly (checked by a script:
  all 15 non-empty lines of the source's questions and "Not asked" paragraph occur verbatim),
  the "asked in the chat … after the package" statement, and a labelled transcription note
  that it supersedes the earlier note saying item 7 was not put to the product owner.
- ADR 0007 checklist: "Written explanation" ticked, accepted on 2026-10-28 for exactly what
  answers 1-5 cover (automatic request, one paid call per set and the model by data kind;
  every sentence quoting both the person and the record, "art" not quotable alone; readiness,
  pay and hiring words blocked unless the record uses them, the "employers need" false alarm;
  Try again only if no paid call was made, else Suggest again; placement above "How Nessa
  found it", the "only the quoted words were checked" wording, EXP-01 as written), citing
  the addendum. New unticked item "Not covered by the addendum's answers": the claim and
  quotation bounds, the full function-word list, the "first view" definition, and the three
  support phrasings as built (placed here as instructed, though they belong to decision 7);
  "Not asked: not run — requires human". The "Evaluation cases" item's "EXP-01 is in the open
  item above" now cites answer 5.
- To keep ADR 0007 from contradicting itself I also made minimal edits beyond the checklist
  item, all about item 7: the checklist's intro sentence, the status line's decision 12
  sentence, the "Not done" line, and decision 12's "Provisional (R6, H-12)" bullet (now split
  into accepted / still provisional, not asked). Nothing else in ADR 0007 changed.
- Register: H-12 "seven of nine checklist items done" with the addendum and the remaining
  open items; the session 1 row "seven of nine"; REC1-11's status (accepted parts vs still
  provisional parts); TEST1-10's EXP-01 sentence (accepted as written, answer 5).
- Left as is (outside the instruction): `docs/reviews/sprint-2.md`'s Task 6b "Open (added)"
  row still lists the note's H-12 review as not run; `safety.REVIEW_STATUS` and PROF-09 are
  unchanged (the three phrasings are still not reviewed as built, which stays true).

### 3. App fixes (`apps/web`)

| Finding | Change | Covering test / capture |
|---|---|---|
| V-01, S0-V03 | Each route card shows the conditional badge "Conditional: ready in N months, once its assessed report is passed"; "Ready in …" stands alone only when the data says the route is ready. The adapter's condition words became the clause after "ready" (`trace.ts` READINESS: "once its assessed report is passed"); the drawer says "ready only once …", the shared note "every route here is ready only once …". A header comment in `RoutePreview.tsx` carries the rule to the computed routes (Task 14). | `RoutePreview.test.tsx` (2 new tests), `trace.test.ts` (expectations updated to the new wording); `routes`, `routes--layers` captures |
| V-03 | Fixture notice first and whole (two sentences, shorter); one-line "Economic cost against the fixture's baseline, over the same 6 months for every route (January to June 2027)."; the definitions (cost shown, horizon, where) and the shared condition behind a native `<details>` "What's being compared"; phone gap 16. Route A's whole card is in the 390×844 first view; A–C at 768×1024. | `e2e/layout.spec.ts` (phone V-03, tablet V-03), `RoutePreview.test.tsx` (disclosure); `routes`, `routes--compared` captures |
| V-04 | The route drawer is titled "Route B" (its close is "Close route B": `EvidenceDrawer` now derives the close label from the title, so "Where this came from" is unchanged). The body leads with a group "Route B at a glance": fixture pill, condition badge, and a `dl.figures` row Ready in / Economic cost / Direct spending; dates and layer follow. Phone sheet gap 16 → 12 so it fits the 212 px peek. | `e2e/layout.spec.ts` (peek is 212 px and holds the title and the whole group), `RoutePreview.test.tsx`; `routes--route-b` (peek) and `routes--route-b-expanded` captures |
| (found) S0-V07, Routes part | With a route's sheet open on a phone, focusing a lower route left it under the sheet: only You had `scroll-padding-bottom`. Added `html:has(.app[data-drawer="open"])` scroll padding for every chapter (You's more specific rule still wins). | `e2e/layout.spec.ts` "with the sheet open, a route brought into view by focus is not under it" |
| V-05 | Options are `DATA_MODE` words only ("Demo data", "Live-assisted"); the chosen mode's explanation is `field-hint` text linked by `aria-describedby` and changes with the choice. | `WorkspaceList.test.tsx` (new; `CreateWorkspace` exported for it); `home--empty` captures; 200 % zoom captures (below) |
| V-06 | Plan's empty state: "Plan selection isn't part of this build yet, so no plan has been made. When it is, a plan will start from a route Nessa computes from your answers, never from a fixture preview." Action "Review your answers in You" (per-chapter `next` label; the others keep "Review what we know"). | `ChapterView.test.tsx` (new V-06 test); `plan` captures |
| V-09 | Visited landmark = 2 px ring in `--text-on-space-muted`, no fill (the fill is kept for recorded decisions, spec section 15). Consequence: the current chapter's mark is now a plain selection ring even when visited (it used to show the grey fill inside). Rule added to `docs/design/README.md`. | `e2e/layout.spec.ts` V-09 (computed style: neither filled, rings differ); `ChapterNav.test.tsx` unchanged and passing; every desktop/tablet capture |
| V-10 | New `NotInvited` (PageState.tsx): h1 "This account isn't invited", then an announced error `Alert` with no title holding "Sign in with an invited account.", the reference and Sign out. Used on the home page and on a workspace URL. `Alert`'s `title` is now optional (only this use omits it). | `PageState.test.tsx` (new), `e2e/access.spec.ts` (the cause appears once); `not-invited` captures |
| S0-V04, S0-V06 (app) | No app state exists: Routes shows only the fixture preview, which no profile version produces (nothing to be stale) and whose figures are all known (no direct-spend-only comparison). Ruling: not built speculatively; rule carried to Task 14. What applies is in place: the peek always leads with name, condition and figures, and More is in every sheet state. | — |

Visual package (`e2e/visual.spec.ts`): new shots `routes--compared` and `routes--layers`;
`expandSheet` takes the dialog's title; the per-shot checks were factored into `measure`
and `expectClean` (same checks) plus a new **`clipped`** check: each visible select's chosen
option is measured by a shrink-to-fit copy holding only that option and compared with the
select's width (validated in a scratch page: the old "Demo data: synthetic, nothing leaves
this computer" at 308 px is flagged, short and auto-width selects are not; my first,
canvas-based version wrongly flagged the auto-width "month" select and was replaced). A new
test captures the home page at 200 % zoom: 1440×900 → 720×450 CSS px and 390×844 → 195×422
CSS px, device scale 2, writing `checks-zoom200.json`. The overflow gate applies only at ≥
320 CSS px (WCAG 1.4.10); see "Concerns".

### 4. Sprint 0 compositions (`docs/design`, `ba5be08`)

- **S0-V01** `conversation`: the `.known-summary` base rule moved before the media queries
  (it overrode them); it is a link "What we know, … — Review" to `#known-title`, at the top
  of the thread, shown ≤ 1280 px; "What we know" stacks after the thread on phones (no longer
  `display: none`).
- **S0-V02** `conversation`: phone `.you` padding keeps the sheet clearance (the shorthand
  reset it to 0); the composer sticks at `peek + 16`; `html` `scroll-padding-bottom: peek +
  96px`; the failure notice moved before the not-processed message ("kept below"), so Try
  again and "Add the details yourself" are in the first view; tighter phone spacing.
- **S0-V08** `conversation`: Send is secondary in every state (the drawer's Accept / Add an
  amount, or Try again, is the one primary); `opportunity-map` failure: the listing's action
  is a secondary "Check this listing again".
- **S0-V03** `route-comparison`: each TRACE-01 card has a status line "Conditional: ready in N
  months, if the assessed report passes" (glyph inserted with `NESSA.glyph`), its figures
  line keeps the cost; the group note "Every route here is conditional" removed.
- **S0-V04**: the journey head is shared by all states and, in failure, carries "Previous
  comparison, version 14, 2 days old" (stale glyph) above the condition.
- **S0-V06**: unknown journey: title "Route B" (set by JS), More, a summary row Ready in 9
  months / Direct spending £2,400 (bound `directai.routes.1.*`, so the fixture check covers
  them) / Economic cost "Not available", then "Schedule not available".
- **S0-V05** `opportunity-map` unknown card heading "Preference fit not assessed".
- **S0-V07**: notices lead with label + one line, the explanation in a `<details
  class="more-detail">`; phone hides the sentence under the Routes title (the basis summary
  now starts with the region) and the panel's duplicate version label; phone alert padding
  16, gaps 8; the `.routes`/`.roles` phone padding shorthands no longer reset the sheet
  clearance to 0 (found by the new focus check: the last cards could not clear the sheet).
  First card top on the phone: failed Roles 547, unknown Routes 537, failed Routes 587 (was
  649, 673, 818; sheet at 632).
- `shell.css`: phone `scroll-padding-bottom`, `.more-detail` style, phone alert padding.
- `tools/screenshots.mjs` gained three checks, written to `checks.md`: filled primaries in
  view ≤ 1; with a phone sheet open, the first list card at least 40 px above the sheet
  (`FIRST_CARD_CLEAR_PX`); every work-area control, focused, on top at its centre. RED
  evidence: the same logic as a scratch probe on the pre-fix compositions reported 2
  primaries in failed Roles, first cards at 649/673/818 and covered route cards after focus
  (and nothing in the fixed conversation).
- `README.md`: the rail rule (filled = decisions recorded; visited = brighter ring), the
  sheet-peek, notice and card rules, and the checks list.

### 5. Recaptures and dispositions (`2c63b5b`)

- `docs/reviews/sprint-2/screenshots/` (the current package, as Task 6 used for its
  dispositions): `pnpm`'s review run rewrote all 99 shots and the four checks files; I kept
  every PNG whose change my fixes explain and restored seven that differed only in per-run
  text, after a pixel diff against HEAD (bounding boxes, scratch script): `not-found` ×3 (the
  reference), `you--reply-to-review--390x844`, `you--support-note--390x844`,
  `you--slate-note-unavailable` at 1440 and 768 (a few small glyphs each). Kept: Routes (all),
  Plan, not-invited, home--empty, the new `routes--compared`, `routes--layers`,
  `home--empty--*-zoom200`; the phone `you--source-drawer`(`-expanded`) (sheet gap); every
  desktop/tablet capture whose diff is the rail; and `you--unavailable--390x844`, whose
  committed copy dated from `dec43e6` and predated later Task 6 You changes (a refresh, not a
  6c change). The checks JSON files are from this run on the final code: 33 shots per size,
  axe/overflow/overprint/clipped/console/fonts all clean; zoom: 1440 clean, 390 overflow 51
  (recorded).
- Dispositions: `docs/reviews/sprint-1.md` V-01, V-03, V-04, V-05, V-06, V-09, V-10 (each
  naming its test and captures), the D/E coverage gap, the open-items table (V-findings,
  coverage, the new 195 px zoom item, UI-06 partly run, the `next` row closed) and the
  approval note; `docs/reviews/sprint-0.md` (S0 row, a Task 6c paragraph, approval note);
  `docs/design/pre-review-sprint-0.md` (a disposition under each S0 finding);
  `docs/reviews/sprint-2.md` (one sentence on the package's 6c additions). Register UI-06,
  UI-09, UI-11 (T6c parts) and H-02.

## Rulings I made

1. **S0-V04 and S0-V06 in the app**: no such state exists (see table); not built, carried to
   Task 14; the composition is corrected.
2. **Where the recaptures live**: `docs/reviews/sprint-2/screenshots/`, the package
   `pnpm run review-screenshots` writes and Task 6 cited for V-02/V-07/V-08; the historical
   `sprint-1/screenshots/` stay as the Sprint 1 record.
3. **"200 % zoom"** read as the standard 200 % browser zoom of the 1440×900 desktop (720×450
   CSS px), gated with every check; I also captured a 390 px phone at 200 % (195 CSS px) and
   gate everything there except overflow, because WCAG 1.4.10 asks for reflow only down to
   320 CSS px.
4. **V-09** fixed by distinguishing (ring vs fill), not by a visible legend; the question of
   what the marks communicate stays with the human reviewer, as the finding asks.
5. **V-04 title**: the route sheet is titled with the route (as the Sprint 0 reference);
   other evidence sheets keep "Where this came from".
6. **Composition copy** keeps the references' own wording ("if the assessed report passes");
   the app keeps its adapter's ("once its assessed report is passed").

## Checks run (final code)

| Command | Result |
|---|---|
| `cd apps/web && pnpm install --frozen-lockfile` | exit 0, lockfile unchanged (sha256 check OK) |
| scratch `pnpm add next@16.4.1 … --lockfile-only` / `next@16.4.3` | 16.4.1 resolves, lockfile identical; 16.4.3 refused by the age rule |
| Vitest, focused while iterating (TDD) | RED first: RoutePreview 4 new tests failed (dialog "Route B" not found etc.), ChapterView V-06 failed, PageState V-10 and WorkspaceList V-05 failed (component not exported/absent); then GREEN |
| `make check` | exit 0: ruff format (184 files) and lint clean, mypy clean (184), 621 fast backend tests passed (197 deselected), fixture validator passed; web: client matches OpenAPI, Biome clean (110 files), `tsc` clean, Vitest 211 tests in 25 files passed |
| `playwright test e2e/visual.spec.ts e2e/layout.spec.ts e2e/access.spec.ts e2e/keyboard.spec.ts e2e/journey.spec.ts` with `NESSA_REVIEW_DIR=../../docs/reviews/sprint-2/screenshots` (fresh `nessa-l0-webtest` stack) | 19 passed (1.7 min) — wrote the committed captures |
| `cd docs/design && pnpm run screenshots` | fixture check 64 assertions passed; 18/18 captures pass (incl. the three new checks) |
| `cd docs/design && pnpm run contrast` | 68/68 pairs pass; `contrast-report.md` unchanged. No new colour pairing (the visited ring is `--text-on-space-muted` on `--surface-space`, already measured; the other new uses are existing token pairs) |
| `make acceptance` (on `2c63b5b`, the final code; `62f1016` after it is docs only) | exit 0: 197 integration and stack tests passed (621 deselected) in 320 s on PostgreSQL 16 and DBOS; the Storybook build succeeded; Playwright 28 passed in 2.2 min on a fresh `nessa-l0-webtest` stack (access 5, conversation 5, journey 1, keyboard 4, layout 5, session 3, Storybook 1, visual 4). One line of noise, as before: Node's notice that `NO_COLOR` is ignored because Playwright sets `FORCE_COLOR` |

Earlier runs while iterating (not evidence for the final code): a first visual run failed on
my own over-strict `clipped` check ("month") and on the 195 px overflow, and the V-09 test
failed on Playwright's accessible name ("Roles , visited"); all three were fixed as above.

## Live calls (R5)

None. No Meta key read; `.env` not touched.

## Not run / blocked

- Human design check of every correction (H-01 Sprint 1 findings, H-02 compositions): **not
  run — requires human** (R2). Nothing here is a score or an approval.
- VoiceOver (H-03), real Safari (H-04): not run — requires human.
- 200 % zoom on any page other than the home page; long names and three targets in the app
  captures.

## Agent pre-review of the recaptures (agent pre-review — not the required human review)

- Route cards are taller: the condition wraps to two lines on a phone and in the two-column
  desktop grid ("… assessed report / is passed").
- The visited and not-started rings differ in brightness and stroke only (2 px mist-300 vs
  1.5 px ink-500); readable on the captures, but subtle; a person should judge it.
- The "What's being compared" disclosure uses the browser's marker on ink; the summary is
  14 px semibold, close to the body line above it.
- Compositions: in unknown You on a phone the answer choices start under the sticky reply
  field in the first view (focus or scrolling clears them; the check passes); in failed
  Routes only the top of route A's card (about 45 px, its letter and name) clears the sheet.

## Concerns

1. The home page at 195 CSS px (a 390 px phone at 200 %) overflows 51 px: "Sign out
   <email>" and "Create workspace" are `nowrap` buttons. Recorded in `checks-zoom200.json`
   and as an open UI-06 item, not fixed (outside V-05; the select and its text are whole).
2. Seven per-run-noise PNGs were restored to their committed versions (listed above), so the
   package mixes capture runs as before; their checks in `checks-*.json` are from this run.
3. Process transparency: all repository file changes were made with Edit/Write, plus the
   project formatter (`biome check --write` on six of my files, inspected) and `git checkout`
   to restore the seven PNGs. Outside the repository I redirected `make acceptance` output to
   a scratch log, and one no-op heredoc to `/dev/null` was run by mistake; no repository file
   was written that way.

## Paths a reviewer can skip

`docs/reviews/sprint-2/screenshots/*.png` and `checks-*.json`,
`docs/design/screenshots/*.png` and `checks.md` (generated); no lockfile or generated client
changed.

---

## Fix round 1 (FIX_BASE `865ab59`, the controller's `CLAUDE.md` commit, left untouched)

Commit: `8276485` Fix round 1: answer 3 as the rule, the stale Sprint 2 rows, the
computed-route rule. Docs and one code comment only; no behaviour change.

1. **Answer 3 is a rule with examples, not the full lists.**
   - ADR 0007 decision 12's bullet now reads: accepted "blocking readiness, pay and hiring
     claims unless the job's own record uses the word, as answer 3 put it: the rule, with its
     examples ("qualified", "well-paid", "in demand", "employers need") and the "employers
     need" false alarm"; "the full readiness, pay and hiring word lists and phrasings" moved
     to its "Still provisional (R6, H-12), not asked" part.
   - REC1-11 status: accepted "the readiness, pay and hiring block as answer 3 put it, the
     rule with its examples"; "the full word lists" listed with the still-provisional items.
   - To keep the record consistent with this, the full word lists were also added to what
     was not asked in ADR 0007's unticked "Not covered by the addendum's answers" item, its
     status line and its "Not done" line, and the register's H-12 "Open" list. The checklist
     tick itself was already worded as the rule and is unchanged.
2. **Stale Sprint 2 rows** (`docs/reviews/sprint-2.md`).
   - The `next` row: "Closed: removed in Task 6c (`ac94bf4`); `pnpm install
     --frozen-lockfile` passes with the lockfile unchanged (ADR 0005 decision 1)".
   - Both H-12 rows (the accepted-limitations table and the Task 6b "Open (added)" table) now
     give the recorded outcome: seven of the checklist's nine items closed by the product
     owner on 2026-10-28, at session 1 and in its item 7 addendum, citing
     `docs/reviews/session-1.md` and the ADR 0007 checklist. The open items stay "not run —
     requires human", with the same list the register's H-12 row gives (the second row lists
     only the written-explanation items it is about).
3. **The forward rule for computed routes**, stated in `RoutePreview.tsx`'s header comment,
   `docs/design/README.md` ("A card keeps its own qualification") and the V-01 disposition in
   `docs/reviews/sprint-1.md`: computed routes (Task 14) take the qualification from their own
   computed readiness state, never from the fixture adapter's words, and never show an
   unqualified "Ready in …" when that state carries a condition.

Checks: `make check` exit 0: ruff format (184 files) and lint clean, mypy clean (184 source
files), 621 fast backend tests passed (197 deselected), fixture validator passed; web: the
client matches the OpenAPI document, Biome clean (110 files), `tsc` clean, Vitest 211 tests in
25 files passed. No acceptance run (not needed for docs and a comment); no live calls; no
subagents. All edits were made with Edit. An untracked Office lock file
(`~$ssa_Local_Development_Plan.docx`, not mine) is in the working tree; I left it alone and
did not commit it.
