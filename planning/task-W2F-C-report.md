# Task W2F, slice C: What we know, targets and suggestions — implementer's report

Status: DONE_WITH_CONCERNS (the concerns are runs I could not make here, listed below).
Branch `claude/confident-ramanujan-ux3saw`, main tree. Commits (pathspec only):
- `223ce63` removing a target, or putting one back, leaves the suggestions current (backend rule and tests)
- `cb3dca5` What we know, targets and suggestions, fixed from session W2 (web, stories, Vitest, journeys)
- `941a03e` the ruling and the rule recorded (ADR 0007 amendment line; STATE-10's row); test tags

## What the person sees now

1. **No label printed over its value, at any width** (finding 1). `.fact`'s label column keeps a
   floor (`minmax(min(8rem, 40%), 1fr)`) and a label word may wrap (`overflow-wrap: anywhere`).
   Cause as found: the label column could shrink to nothing beside a long value.
   New long-values state: story `What we know / Long values` (three long targets, an expected
   qualification, long task answers), measured at 1440, 768 and 390 in `e2e/storybook.spec.ts`,
   and a new app shot `you--what-we-know-long` (same answers, through the API) in
   `e2e/visual.spec.ts`, whose overprint check now sees long values. The overprint helper moved
   to `e2e/helpers.ts` so both use one definition.
2. **Remove beside each target** (finding 2).
   - What we know: a short "Your targets" list right under "Edit answers directly" (and the form
     when open), each target with Remove. The targets are no longer repeated in "Your answers" or
     "Not asked yet"; with no targets the list says the answer's state ("Unknown", "Not asked
     yet"…).
   - A saved suggestion: Remove beside "Saved as one of your targets".
   - Both go through the profile's own save (`PUT /profile`, expected version, idempotency key);
     no new command. What it did is said where it was done ("Removed “Zoo keeper” from your
     targets"), focus goes there, and Undo (orchid, the profile's revert) brings it back
     ("Undone: “Zoo keeper” is one of your targets again"). A refused save shows the error
     code's words and refreshes the answers.
   - After a removal, "Make this a target" is the bright action again and "Suggest again" stays
     hidden: the slate stays current.
   - The full-targets line now reads: "You have 3 targets, the most you can have. To add this
     one, remove one in What we know."
3. **The answer form's Save stays in reach** (finding 9's form part). Save changes and Discard sit
   in a bar kept at the foot of the window while the form is open (`position: sticky` on an
   opaque card surface; above the phone's open evidence sheet too). Measured in Storybook at
   1440, 768 and 390: without it, Save was 1,100–4,700 px below the window for every field but
   the last; with it, in reach at every field.
4. **Title, what the work is and kind of work told apart** (finding 8). An open suggestion has
   nothing under its title; ESCO's description sits under its own "What the work is" heading at
   reading size (16 px, no longer the 14 px note size), with "Kind of work: …" in small muted
   text after it. Closed cards (titles to scan) keep their kind-of-work line.
   **Order kept: actions first.** The hard-to-read part was the unlabelled description and the
   kind-of-work line sitting under the title like a subtitle, not the order; with those fixed,
   the bright choice stays right after the title, as recorded (D-I3), so a phone keeps it in the
   first screen.

Words are in `vocabulary.ts`'s suggestions section (`SUGGESTION_WORDS`: `whatTheWorkIs`,
`kindOfWork`, `full`) and a new targets section right after it (`YOUR_TARGETS`). Nothing in
the field-label or conversation sections changed.

## The backend rule (TDD)

`profile/exploration.py`: `changed_only_by_choices` becomes `stays_current` (the old name no
longer described it). A discovery stays made from the current answers while every later
version changed only the targets and gained none but this slate's choices or a title the
pinned version or such a choice held. So a removal (the last one included), an Undo, or the
same title typed again keeps it current; a new target typed in, or any other answer, still
makes it "based on your earlier answers". It also fixes a side case: undoing a choice no longer
made the slate stale.

- RED: `pytest tests/domain/test_discovery_contract.py -k removing_a_target` → 1 failed
  (`assert changed_only_by_choices([pinned, one_left], choices)` was False).
- GREEN: `tests/domain/test_discovery_contract.py` 16 passed.
- Focused integration run, under the lock, as the dispatch gives it:
  `pytest -m integration tests/integration/test_discovery.py -k "leaves_it_current or leaves_the_slate_current"`
  → **2 passed** in 23.65 s (W2E's test and the new one: choose two from the slate, remove one,
  remove the last (Unknown), Undo, all current; then type "Astronaut", not current). Lock
  taken and released by the same command; log in the scratchpad `w2fc-int.log`.

## Rulings

- **Removing the last target leaves the target roles answered Unknown.** The person was asked
  and has none for now: not "Not asked yet" (false, and the demo interviewer would ask again),
  not "Skipped" (they didn't skip). Undo restores what was there. Recorded in ADR 0007's new
  amendment line.
- **A slate kept current after a removal still holds what its searches found from the removed
  title**, and its written note may still quote it: both describe the answers it was made from.
  This is the consequence of the dispatch's "removing a target alone leaves the suggestions
  current"; recorded in the same amendment line.
- **Remove on a card removes every target title whose stored record names that occupation**
  (normally one), so the card's "saved" state really clears.
- **While a removal or an undo is saving, every Remove waits and says why** ("Removing…",
  "Undoing…"), so a second click can't race the first against the same version.
- Test tags: removal is the profile's own save, so PROF-07 ("same application commands");
  Save in reach is UI-06/UI-09 (reachable controls, layout); the overprint check UI-11.

## Checks run (final code)

- `make check` after each change and last at `941a03e`'s content: exit 0. Ruff and mypy clean;
  backend 2118 passed, 123 skipped; fixture validator passed; web: generated client matches,
  Biome clean (161 files), `tsc` clean, Vitest **481 passed** (46 files), no warnings.
- Vitest RED before GREEN: 8 new tests failed first for the right reasons (no "Your targets"
  region, no Remove, old full-targets words "You have 3 targets: remove one first.", no "What
  the work is"), then all passed.
  New: `WhatWeKnow.test.tsx` (5: listed once with Remove; remove then Undo with the exact PUT and
  revert bodies and focus; last removed leaves Unknown; a 409 keeps the target and says why;
  unasked said in one place). `Directions.test.tsx` (+3: Remove on a saved suggestion with Undo,
  Make this a target bright again, no Suggest again; the full-targets words; the open card's
  order and sizes).
- Storybook: `pnpm run build-storybook` then `e2e/storybook.spec.ts` run locally through a
  scratch Playwright config with no global setup (the spec needs no stack): **3 passed** —
  every story renders and passes axe (the three new stories included), long answers clear of
  their labels at 1440/768/390, Save in reach at 1440/768/390.
- Defect reproduced before the fix, on the same story, by injecting the old rule
  (`w2fc-overprint.mjs`, OLD=1): overprinted "Qualifications" at 1440 and 768; "Current role",
  "Qualifications", "Tasks you enjoy" at 390. With the fix: none, no horizontal overflow.
  Same for Save (`w2fc-save.mjs`, OLD=1 removes the sticky rule): out of reach at 4 of 5 fields
  at each width; with it, in reach at all.
- Screenshots looked at (agent pre-review only, R2): What we know long values at 1440 and 390,
  the removal notice with Undo at 390, the chosen-target card at 1280, the suggestions view at
  390, the open form at 1440 and 390. All in the scratchpad as `w2fc-*.png`.

## Journeys and stories changed

- New `e2e/what-we-know.spec.ts` (not run here): (1) a chosen target removed on its suggestion
  (focus on "Removed…", Make this a target bright, no Suggest again), undone (focus on
  "Undone…", saved box back), then removed in What we know (Unknown shown, Undo in orchid), and
  the suggestions still current; (2, 3) the open form's Save in reach at 1440 and 390 in the
  fixture workspace.
- `e2e/visual.spec.ts`: new shot `you--what-we-know-long` at all three viewports, with its
  `longAnswersWorkspace` set-up; header list updated; overprint helper imported from helpers.
- `e2e/storybook.spec.ts`: two new tests (above).
- Existing steps read and unchanged in what they assert: conversation.spec's "talk, review,
  undo, explore and sketch" (the open card still has one heading before choosing, the saved
  heading's name is unchanged), its phone first-screen test (What we know's Edit answers
  directly is still first; the open card's choice is still right after its title, now nearer
  it), keyboard.spec's "a suggestion opens and becomes a target from the keyboard" (no new
  focus stop between the title and Make this a target).
- New stories `What we know / Long values`, `Target removed` (plays Remove), `Answer form
  open`. Existing slate stories now show "What the work is", and `SlateTargetChosen` shows
  Remove.

## Not run

- `make acceptance`: not run, the controller runs acceptance. That includes the new
  `e2e/what-we-know.spec.ts` and the new visual shot, which I could not run (they need the
  stack). Risk to watch there: at 390 in the app, whether anything else fixed near the window's
  foot covers Save (the Storybook check found nothing, but it has no world layer or strip);
  and Save above the open bottom sheet on a phone is untested.
- No live calls, no web requests. Cost: $0.
- Human-only: the visual and words judgement of these screens — not run, requires human (the
  product owner's short re-test of Maya and Sam).

## Concerns and notes

- **For slice A:** `stays_current` compares every answer except the targets, so the new
  "Tasks you don't enjoy" answer will mark a slate "based on earlier answers" when it changes,
  unless slice A excludes it there (it never searches, so excluding it seems right; their
  call). Remove builds its save from `inputOf(document)`, so `inputFrom` must carry the new
  field.
- **Found, not fixed (outside this slice):** in the answer form, a qualification's status select
  cuts off "Expected: taking it, or waiting for results" at 390 and at 1440 (screenshot
  `w2fc-form-1440.png`). No visual shot opens the form with a qualification, so the
  clipped-select check hasn't caught it. For the final-review list (R13) or slice B's form work.
- The Storybook "What we know" stories have their own top-level group: a "You/What we know"
  group would clash with the existing "You" component in Storybook's tree, and keeping them out
  of `Conversation.stories.tsx` avoids a conflict with slice B.

Generated or vendored paths to skip: none changed (no client regeneration; no lockfile).

## Review

Independent reviewer, 2 November 2026. Read the brief (card "Task W2F"), the slice C dispatch,
session W2's findings (1, 2, 8 and the answers form's part of 9), this report, and the whole
package `review-25fd938..941a03e.diff` (ledger commit 97d5b3c skipped), in three passes
(backend and docs, components, tests and e2e). Code outside the diff was read only for named
risks (listed under each finding). One focused check was run (below). No Docker, no web
requests, no live calls, `.env` not read; nothing in the tree changed except this section.

### The product owner's session comments, done or not done
- Finding 1, What we know's text overlaps ("The UI is broken"): **done.** The label column
  has a floor; the long-values story and a new app shot measure it at three widths.
- Finding 2, no way to remove a target, and the buried way made the paid Suggest again the
  bright action: **done.** Remove in a "Your targets" list and on a saved suggestion, each
  with Undo in place; the slate stays current.
- Finding 8, a suggestion's title and description hard to tell apart: **done.** Nothing sits
  under an open card's title; the description has its own "What the work is" heading at
  reading size; "Kind of work" is small and muted after it.
- Finding 9, the answer form's Save about 3,400 px down: **done, with a side effect** (see
  Important 1).
- The world's role lights can't be clicked: not this slice (a later task, the product owner's
  yes).

### Spec Compliance
- ✅ Spec compliant for the four deliverables and their tests, except the side effect in
  Important 1 (Global Constraint 11, WCAG 2.2 AA).
- Backend rule checked by hand against the risks asked about:
  - `stays_current` (`backend/src/careerwright/profile/exploration.py:258-280`) fails on any
    change to a field other than the targets, and on any target title that neither the
    pinned version nor one of this slate's choices held. So a removal, the last one
    included, an Undo or a retyped title stays current. A new title typed in, a choice from
    another discovery (its source's `run_id` differs, `:290-297`), or any other answer
    changed in the same version or any version in between still marks it stale. A change
    that is later reverted still leaves it stale, which is the safe side. I found no path
    where a stale slate reads as current.
  - Field equality holds across a whole-document save, because `apply_updates` keeps an
    unchanged field's value and source (`profile/document.py:448-451`).
- Remove never loses another answer. It sends `inputOf(profile.document)` with only the
  targets replaced (`apps/web/src/components/TargetRemoval.tsx:56-59`), the same path
  RoleResearch already uses (`RoleResearch.tsx:249`). Every `ProfileInput` field is required
  (`profile/document.py:219-250`), so slice A's new answer cannot be dropped without failing
  `tsc` and the API's validation. Undo reverts to `version - 1` under the expected version,
  so a newer save makes it a 409, never a silent overwrite.
- Removing the last target leaves Unknown. I judge that honest: unknown is never zero or
  ineligible, and an empty "provided" list would read as "none". Whether "Unknown" is the
  right word under "Your targets" is a words question for the re-test (Minor 4).
- ⚠️ Cannot verify from diff:
  - `e2e/what-we-know.spec.ts` and the `you--what-we-know-long` shot were never run, so the
    app at 390 (Save above the strip and above the open bottom sheet) is unproven. They wait
    for the controller's acceptance run.
  - Whether the world's destination lights answer a removal in the running app.
  - Slice A's `disliked_tasks` reaching `inputFrom`. A change to it will mark a slate stale
    under `stays_current`, the safe default, unless slice A excludes it there.

### Strengths
- The backend rule is small, pure and tested both ways: a domain test with removals, the
  last one, Undo and retyping against new titles and other answers, plus a real-PostgreSQL
  integration test through the profile save and revert (log: 2 passed; backend unchanged
  since).
- Remove reuses the profile's own save and revert: expected version, idempotency key, error
  codes in words. There is no new command and no new run kind.
- The words follow the rules. "Removed “X” from your targets" and "Undone: “X” is one of your
  targets again" say what Careerwright did. The full-targets line says where to go. Undo is
  orchid, Remove is quiet and neutral, and sea-glass stays for selection and action.
- The defect was reproduced before the fix (old rule injected) and measured after at three
  widths. The overprint helper is now shared, so the app's visual check finally sees long
  values.
- Product owner's view: the screenshots (long values at 390, removal with Undo at 390, the
  saved card at 1280, suggestions at 390) are calm, legible and practical. What we know reads
  as label then value. The open card now reads title, choice, what the work is, why it could
  suit you. Removing answers in place, with Undo beside the words. This is a working view
  built to the references; the moment is Task M's (R13).

### Issues
#### Critical
None.

#### Important
1. **The sticky Save bar hides the keyboard focus as the person tabs down the form** (WCAG
   2.2 SC 2.4.11, Focus Not Obscured; Global Constraint 11). Files:
   `apps/web/src/app/globals.css:1619-1628` (`.form-save`) and
   `apps/web/src/components/ProfileEditor.tsx:335-337`.
   - Each newly focused field is scrolled to the window's foot, under the 66 px bar. Nothing
     reserves that room; the only `scroll-padding-bottom` is for the open sheet (`:1091-1093`).
   - Focused check (reviewer's script on the existing static Storybook,
     `what-we-know--answer-form-open`, Tab from the first field to Save): entirely hidden
     controls at 1440×900: 8 (e.g. "Work area 3", "Qualification 3: achieved or expected");
     768×1024: 4; 390×844: 7. Script:
     `/private/tmp/claude-501/-Users-darianraad-Code-careerwright/51b74d1a-6cb8-4bb3-b832-9054484ac3c7/scratchpad/rev-w2fc-focus.mjs`.
   - Why it matters: a keyboard or magnifier user filling in their answers loses sight of
     where they are typing. Before this slice, the form had no such barrier. The Save-in-reach
     tests check Save only, not the controls it covers.
   - Fix (CSS only): while the form is open, reserve the bar's height, e.g.
     `html:has(.form-save) { scroll-padding-bottom: calc(<bar height> + var(--space-16)); }`,
     adding `--sheet-peek` when the sheet is also open. Then add a Tab-through check to the
     Storybook spec beside "Save stays in reach".
   - Under R16 this is neither safety, truth nor lost input. The controller decides whether
     it is fixed in this piece or listed. It is graded Important because it breaks a Global
     Constraint.

#### Minor
1. `Directions.tsx:466` against `TargetRemoval.tsx:135`: on a card, Remove's spoken name uses
   the card's sentence-case title ("Remove Bicycle mechanic…") while the notice quotes the
   stored words ("Removed “bicycle mechanic”…"). Use one form.
2. `TargetRemoval.tsx:166-171`: while one removal saves, "Removing…" is printed beside every
   Remove in the list (three times with three targets). A single line under the list would
   do.
3. `WhatWeKnow.tsx:162-163`: with the form open, the targets can be changed in two places
   (the form's field and "Your targets" below it). Removing one with unsaved form edits makes
   the form's next Save meet a 409 and rebase. Nothing is lost, but it may surprise. A
   candidate for the final-review list.
4. `docs/adr/0007-conversation-discovery-and-support.md:1108-1110`: the "Unknown after the
   last removal" ruling isn't marked provisional (R6). For the re-test, ask in one sentence:
   after removing your last target, does "Your targets: Unknown" read right? Yes keeps it.
5. The recorded consequence, for the product owner's awareness. A slate kept current after a
   removal still shows reasons found from the removed title, and its written note (asked
   automatically while current, `Directions.tsx:710`) may quote it as "You said". That is
   still true, but may read oddly beside an empty "Your targets".
6. Pre-existing class, now with two more entries: any profile save while a review card waits
   (Make this a target, the form, and now Remove) moves the version, and the card can only
   "Send it again" (`profile/conversation.py:322-332`; slice B's ruling 2). It is not silent.
   Worth one line on the final-review list with slice B.
7. An unmentioned widening of `stays_current`. A choice of ESCO occupation for an existing
   target made outside the slate (same words, new `occupation_choice` source, e.g. the
   sketch's "which one do you mean") used to mark the slate stale and now keeps it current.
   This is harmless, since the slate is recomputed from the current target records on every
   read (`exploration.py:746-748`), but it is untested and absent from the ADR line.
8. `Directions.tsx:505` uses a styled `<p>` for "What the work is", like "Why this could suit
   you", so screen-reader users can't jump to it by heading. Polish, for the final review.
9. A rare edge. `stored_targets` keeps one record per title concept
   (`profile/targets.py:336-340`), so a card's Remove takes only the first of two titles that
   are the same concept ("Data analyst" and "data analysts"). The card would then still show
   "Saved". The report's "every target title" is slightly overstated.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** All four session findings are fixed. The backend rule is correct and has no
path to a falsely current slate, and Remove/Undo cannot lose another answer. But the new
sticky Save bar hides the keyboard focus on 4 to 8 form controls at every width (WCAG 2.2
2.4.11, Global Constraint 11). The fix is a small CSS rule; the controller decides under R16
whether it lands in this piece's fix round or on the list.

## Fix round 1 (Important 1 only; the Minors stay on the final-review list)

Commit `81cbbc1`, on top of the branch (no rebase).

**Changes.**
- `ProfileEditor.tsx`: while the form is open it measures its Save bar (a ResizeObserver, since
  the bar's height changes when it wraps) into `--form-save-height` on the page's root, and
  removes it when the form closes.
- `globals.css`: `html:has(.form-save)` sets the window's scroll padding to that height plus a
  small space, so whatever is focused or scrolled into view stops above the bar. On a phone
  with the evidence sheet open, the padding is the sheet's peek plus the bar (the bar already
  sits above the sheet).
- `src/test/setup.ts`: jsdom has no ResizeObserver, so Vitest gets one that never reports a size.

**Covering test.** New in `e2e/storybook.spec.ts`: "tabbing through the open answer form, the
Save bar never covers the focused control". At 1440, 768 and 390 it tabs forward through the
open form (story `What we know / Answer form open`) until focus reaches the bar. It fails if
any focused control overlaps the bar even partly, or if fewer than 30 stops were tabbed. It
waits for the fonts first, so nothing moves after a stop is measured.

**RED, then GREEN.** Command (Storybook spec only, no stack; scratch config
`w2fc-pw.config.mjs` with no global setup), after `pnpm run build-storybook`:
`pnpm exec playwright test -c <scratchpad>/w2fc-pw.config.mjs`.
- Before the fix: failed. At 1440, 13 focused controls were covered by the bar, from "Work
  area 2" to "Add another task you believe you can do". The reviewer's script
  (`rev-w2fc-focus.mjs`) gave 8, 4 and 7 wholly hidden at 1440, 768 and 390.
- After: the spec's **4 tests passed**, three runs in a row. The reviewer's script: 0 wholly
  hidden and 0 partly covered at every width (59 stops each).
- One run before adding the fonts wait had a single control covered: fonts arrived after
  focus moved and shifted the layout under it. That was a timing problem in the test, not the
  page, so the test now waits for fonts before tabbing.

**`make check`:** exit 0. Backend 2118 passed, 123 skipped. Web: client matches, Biome clean,
`tsc` clean, Vitest 481 passed.

**Not run:** the app at 390 with the evidence sheet open (the padding over the sheet), and
`make acceptance`. Both are the controller's.
