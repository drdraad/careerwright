# Task 6 review, half B (web, tests, visual package, docs): 8a817f6..dec43e6

Reviewer: independent task reviewer (agent). Read-only. I read the 8.6k-line diff in five passes
(shell, e2e and CSS; components; lib and stories; ADRs and register; reviews and runbook). Where
a finding needed it, I made one focused check outside the diff. I opened 10 Sprint 2 captures:
phone default, reply failed, source sheet, support and slate; desktop default, reply to review and
key consent; answer states at phone and desktop. I parsed all three `checks-*.json` files (78
PNGs; no axe, overflow, overprint, console or font failure). I did not re-run any suite. I made
no live calls, started no Docker and wrote nothing except this file.

### Spec Compliance

- ❌ Issues found:
  - **S2.3 review tray (edit).** The edit path can save part of a decision and silently lose
    the edit. See I1: `apps/web/src/components/ReviewTray.tsx:88-115`, `:184-197`.
  - **S2.3 undo.** Undo re-records restored answers as "Direct entry", so their provenance is
    lost. See I3: `apps/web/src/components/WhatWeKnow.tsx:48`,
    `backend/src/nessa/profile/commands.py:141-158`.
  - **Announcements for new turns** (spec line 893, UI-06). Only the first checked reply is
    ever announced. See I4: `apps/web/src/components/Conversation.tsx:185-188`.
  - **Docs honesty.** Several "verified" register claims are not covered, and one is
    contradicted by the code. See I5: `docs/requirements-register.md:409,532,536,588`,
    `docs/reviews/sprint-2.md:189`.
- ⚠️ Cannot verify from diff. These are half A (backend), reviewed separately:
  - interview preferences (table, RLS, migration r0010, event);
  - profile schema 3 (`work_style`, `minimum_salary` validation; never annualised; schema 1/2
    upgrade);
  - the support screen before any model call, and the inference guard and its word lists;
  - discovery (run kind, sealed input, query grounding, ESCO every-word and any-word search);
  - the slate (pool cap 120, near-duplicate folding, floor, greedy reranker, view-only
    parameters, `limits_not_applied`);
  - `POST .../targets` with the `occupation_choice` source;
  - the sketch (including `visible_workspace` before the profile read);
  - export format 3;
  - `live_eval.py` caps and leak scan;
  - the 39 evaluation cases and their offline results;
  - the backend tests the register cites.

  I could not check whether the live-run outputs are authentic. The ledger rows 15-20,
  `live-eval.md` and the report agree with each other: 7 requests, $0.001574, running total
  $0.021774. The implementer's check counts (Vitest 176, Playwright 21, pytest 373/178) were
  not re-run.

**Named risks (one focused check each)**

1. **Addenda in the UI, each with a regression catcher.**
   - V-02:
     - Try again is wired: `ChapterView.tsx:156` calls `profile.refetch()`, and
       `visual.spec.ts` asserts the button.
     - The strip wording is unit-tested (`WorkspaceStrip.test.tsx`).
     - Nothing exercises recovery in place (M6).
   - V-07: the entry choice leads; `YouChapter.test.tsx` covers it, and the `you` capture waits
     for it.
   - V-08: a Playwright height-equality test (`conversation.spec.ts`, Live vs Reconnecting at
     1440).
   - Capture gaps: all four new captures exist. Prefer not to say for pay is outside every
     `you--answer-states` viewport (M5).
   - Salary floor: amount, period and "before tax" (`profile.test.ts`); Unknown is never £0; a
     hard constraint needs Confirm; the slate says "recorded but not applied" (backend
     `limits_not_applied`).
   - S0-V01 and S0-V02: `elementFromPoint` checks at 390×844 for "What we know", the reply
     field, Send and Try again, with the sheet open and closed. This holds.
   - S0-V05: `Directions.test.tsx`.
   - S0-V08: tested in two states, not "every state" (I5).
2. **Streaming.**
   - Partial replies are dashed and labelled "not checked yet". The validated reply replaces
     them (`conversation.ts:22-34`).
   - `PARTIAL_REPLY` is a `Record<PartialCompleteness>` over the generated enum.
   - Partial-update events invalidate only `turnReply` (pre-existing code; test kept).
   - A failure mid-stream shows as an alert for the latest turn only. An older failed turn is
     marked by a red border alone (M1).
   - "superseded" is labelled "Checked reply" (M1).
3. **The model proposes, the person confirms.**
   - Nothing auto-applies, and hard constraints get only a "Confirm … as a limit" button
     (`decisionFor` requires `confirm`).
   - Undo works end to end (e2e).
   - The edit and undo paths have the defects in I1 and I3.
4. **No percentage; grounded slate.**
   - `Directions.test.tsx` and the e2e assert there is no `\d%`. Each card has why, might not,
     try it and an ESCO URI source.
   - Unknown answers are shown in words.
   - The support copy says "provisional until it is reviewed" and makes no diagnosis
     (`you--support` capture).
5. **MODEL-07.**
   - Consent copy covers what is stored, where, the encryption, "not end-to-end" and the test
     model's training use. This meets spec line 965.
   - Consent comes before sending. The key is held in component state only and cleared;
     nothing goes to web storage (grep: only calm mode and visited chapters use storage).
   - Rotate and revoke are present. The `CREDENTIAL_REVOKED` handling is untested and can
     strand the user (I5, M7).
6. **Accessibility.**
   - Controls are native buttons, selects and details, so they are keyboard-reachable.
   - The pause button stays in place.
   - The reply announcement fires once ever, and focus is dropped after entry, tray save and
     undo (I4).
   - The one-primary logic is in `YouChapter.tsx:94-102`.
7. **Docs honesty.**
   - The Sprint 2 review is labelled an agent pre-review by the implementer.
   - H-01 (Sprint 2), H-03, H-04 and H-12 are "Not run — requires human". H-05 is described
     as "a human check" and is not claimed to have passed.
   - The INT-01..05 failures are recorded as they were counted, and REC1-09 is `failed`.
   - The CLAUDE.md edits match the code (module list checked with `ls`).
   - The register over-claims (I5).
8. **`next` exception.** It is still in `apps/web/pnpm-workspace.yaml:7-10`. It is listed as
   an open item in `sprint-2.md`, with the steps in the report. It was time-blocked (17:43Z),
   so I did not judge it as a miss.

### Strengths

- **Chat and direct edit share one path.** The tray, undo and target choice all go through
  the one command path. Hard constraints can only be confirmed by name: there is no Accept
  button for them, and `decisionFor` drops anything not confirmed.
- **The streamed-reply view is pure and tested.** `replyView` and `reviewable` are pure
  functions with focused tests, built on generated enums only.
- **S0-V02 is proven by hit-testing.** The test uses `elementFromPoint`, not screenshots, and
  it caught a real regression (composer over Try again) that was fixed test-first.
- **No storage leaks.** The key consent copy is plain and accurate to spec line 965. The key
  never reaches web storage, and `lastSeen` is now scoped to the session and workspace, with
  a RED-then-GREEN test.
- **Tests mock only the network edge.** `fakeApi` scripts the generated client's fetch.
- **The visual package is thorough.** It has 78 captures at three viewports with clean
  automated checks, plus the requested expanded sheets, stale conflict and answer states.
- **The Sprint 2 review is honest.** It labels itself an agent pre-review, keeps the human
  gates open, records the live failures with their cause and limits, and gives a concrete
  claim-to-source trace.

### Issues

#### Critical

None.

#### Important

**I1. A tray edit can save part of the decision and silently lose the edit, with no error and
no undo.**

Where: `apps/web/src/components/ReviewTray.tsx:88-115`, `:184-197`, `:78-86`;
`apps/web/src/lib/profile.ts:99-101`.

What happens:
- `save()` posts the turn decision first and checks the edits only afterwards. If an edit is
  invalid, `if (!input.ok) return;` at `:108` exits with the decision already committed.
- The comment there says "the inline field shows the problem", but the tray's
  `<AnswerControl>` (`:184-197`) receives no `error` prop, so nothing is shown.
- A failed edit write (for example a 409) sets `write.error`. However, the decision's success
  invalidates the scope, and the now-decided turn drops out of `reviewable`. The tray (keyed
  by turn) unmounts or is replaced, and the error disappears with it.
- In both cases `onSaved` is never called, so Undo is not offered for the part that did save.
- A third path: a proposal whose state is Unknown, Skipped or Prefer not to say opens Edit
  with that state (`startEdit`, `:78-86`). There is no state selector, so whatever the person
  types is discarded by `unanswered()` (`profile.ts:99-101`), which saves the old state.

Why it matters: a failure looks like success (Global Constraint 6). The card's "the old
profile survives every failed proposal" does not hold, and the person's edit is lost without
a word. No test covers editing in the tray (`YouChapter.test.tsx` has no edit case; the
`decisionFor` test only proves an edit is not accepted).

Fix:
1. Validate every edit before posting the decision, and pass the error to `AnswerControl`.
2. Give the edit control a state selector, or start it as `provided`.
3. Report a failed follow-up write somewhere that survives the tray unmounting (lift the
   state to `YouChapter`), and call `onSaved` for the decision. Better still, send the
   decision and the edits as one command.
4. Add a component test for: invalid edit, edit of an Unknown proposal, and the edit write
   failing.

**I2. "Send it again" on a stale tray swallows errors and support responses, and stays
clickable while the resend is in flight.**

Where: `apps/web/src/components/YouChapter.tsx:47`, `:157-158`;
`apps/web/src/components/ReviewTray.tsx:143-158`; `apps/web/src/lib/conversation.ts:70`.

What happens:
- `resend.mutate(...)` runs on a separate `useSubmitTurn`. Its `error` is never rendered, and
  a `{kind: "support"}` result is dropped.
- A message that was originally sent with `send_after_support: true` and is then resent
  shows nothing at all.
- The button has no pending, no-key or paused `disabledReason`.
- While the new turn runs, `reviewable` skips it (`proposal === null` → `continue`) and keeps
  showing the old stale tray. After the first success `ChangeKeys.settled()`, so a second
  click gets a new idempotency key and creates a second turn and model call.

Why it matters: these are swallowed errors, and they can cause duplicate paid calls.

Fix:
- Route the resend through the `Conversation` send path, which handles errors and support.
- Disable the button while a turn is in flight, when no key is stored and when paused.
- Hide the stale tray once a newer turn exists.
- Test it.

**I3. Undo (and an unchanged tray edit) re-records restored values as "Direct entry", so
their provenance is lost.**

Where: `apps/web/src/components/WhatWeKnow.tsx:44-52` (`inputOf(lastSave.before)` sent as
`PUT /profile`); `backend/src/nessa/profile/commands.py:141-158`.

What happens:
- `write_profile` cites every changed field to one new `DIRECT_ENTRY` source.
- Undoing a tray save therefore re-attributes the restored values to the person as typed
  entries:
  - a fixture value loses its "Synthetic fixture" source (P01's £1,500 cap → "Direct entry");
  - an earlier chat-confirmed `inferred` answer loses its basis and turn citation.
- The same happens when an inferred proposal is saved unchanged via Edit.

Why it matters: provenance is PROF-01. Global Constraint 5 says synthetic data stays labelled
and fixtures never appear as the person's evidence. Undo should restore an earlier state, not
change who said what.

Fix: make undo a revert command that restores the previous version's field values with
their original `source_ref_id`s. `commit_profile_version` already takes
`(value, source_ref_id)` per field. Add an e2e or integration assertion on the restored
field's source.

**I4. Only the first checked reply is ever announced, and focus is dropped by entry, tray save
and undo.**

Where: `apps/web/src/components/Conversation.tsx:169`, `:185-188`, `:283`;
`ReviewTray.tsx` (save); `WhatWeKnow.tsx:38-39`; `Conversation.tsx` `EntryChoice`.

What happens:
- `setAnnounced("Nessa replied.")` sets the same string every time. After the first reply
  the live region's text never changes, so later replies are silent.
- On load with an existing reply it announces spuriously.
- New proposals in the tray are not announced.
- Several actions remove the element that has focus, with no focus target and no
  announcement:
  - choosing an entry (`EntryChoice` unmounts);
  - saving the tray (the turn is decided, so the tray unmounts);
  - Undo (the block unmounts).
- The "Saved as version N" note sits in an `aria-live` container that mounts together with
  its text, so it may never be read.
- The register's UI-06 row (`:588`) claims "a checked reply and the support response are
  announced once". No test asserts any announcement.

Why it matters: spec line 893 requires screen-reader announcements and keyboard-only
completion, and this was a named risk. Sprint 1 set the bar (a stale-save notice takes focus;
the drawer returns focus).

Fix:
- Announce per reply, for example "Nessa replied: N changes to review", keyed by turn ID or
  cleared before it is set.
- Keep the live regions mounted.
- After entry, move focus to the question heading.
- After a tray save or undo, move focus to the "What we know" heading or the saved note.
- Add tests for each.

**I5. Register and review claims marked verified are not covered, or are contradicted by the
code.**

- **MODEL-03, T6 part** (`docs/requirements-register.md:532`). It says the You chapter shows
  "a failed turn's partial as not saved with its failure". `Reply` returns `null` for a failed
  turn (`Conversation.tsx:59`), so the partial is never shown. `conversation.test.ts:93`
  ("keeps a failed turn's partial text visible") tests the pure function only.
- **STATE-06** (`:409`). It cites `YouChapter.test.tsx` for "edit (saved as a direct edit)",
  "skip" and "keep none". That file tests none of them, and no test anywhere covers the edit
  being written (see I1).
- **MODEL-07** (`:536`). It claims "`CREDENTIAL_REVOKED` answered in words". There is no test
  of it. `KeySetup.test.tsx:78` asserts "Rotate the key" is still visible after a revoke, which
  is the stale pre-refetch state, not the revoke outcome.
- **S0-V08.** `docs/reviews/sprint-2.md:189` says "Fixed for You in every state (tested: one
  `btn-primary`)". Only the failed-reply state counts primaries
  (`YouChapter.test.tsx:334`); the tray test checks two buttons' classes.

Why it matters: these are named docs-honesty risks. A "verified" row must be backed by
evidence that applies to the final code.

Fix:
- Either render the failed partial or correct MODEL-03.
- Add the tray edit, skip and keep-none tests, a `CREDENTIAL_REVOKED` test and a
  primary-count assertion in each state (or narrow the wording).
- Re-word the rows until then.

#### Minor

**M1. Completeness vocabulary and failed-turn display.**
- `apps/web/src/lib/vocabulary.ts:225` maps `superseded` to the label "Checked reply" for
  text that was never checked. It is harmless only because the backend returns `text: null`
  for superseded; during the race it shows "Nessa is reading your message".
- `PARTIAL_REPLY[*].tone` is never used.
- An older failed turn is marked only by `border-color: var(--status-error)`
  (`Conversation.tsx:275`), which is colour-only (WCAG 1.4.1). It also still fetches its
  reply on every event (`:48`) for a view that renders `null`.
- For hard constraints, `kindOf` (`ReviewTray.tsx:36-39`) drops the stated/inferred wording,
  so an inferred limit is distinguished only by its dashed border.

Fix: label superseded as "Replaced by the checked reply" (or reuse "none"). Add text for a
failed older turn. Stop fetching replies for ended turns. Keep the basis wording for limits.

**M2. Pause is not enforced, and ADR 0007 overstates it.**
- `Conversation.tsx:295-296` (Try again) and the stale tray's "Send it again" are not blocked
  while paused.
- ADR 0007 decision 1 (`docs/adr/0007-conversation-discovery-and-support.md:30-32`) says "the
  composer gives way to Resume" and "the person can only send one by resuming". The composer
  stays (Send is disabled), and Try again sends.

Fix: block both while paused, or correct the ADR.

**M3. Entry and tone presentation.**
- The tone select shows "Keep this practical" when `conversation_mode` is null
  (`Conversation.tsx:240`), but spec line 289 says the person explicitly chooses.
- "You can change this later" (`:128`) is not true: there is no control to change the entry
  mode after the first choice. "Help me explore instead" is unsaved local state
  (`YouChapter.tsx:50,177`), and an unsure person cannot switch to sure.

Fix: add an unselected "Choose a tone" option and a saved way to switch entry mode, or
reword.

**M4. Salary floor polish.**
- The period select's accessible name is only "Per" (`apps/web/src/components/fields.tsx:125-126`).
- The field hint says "A firm limit once you confirm it" (`vocabulary.ts:173`), while nothing
  applies it yet. Only the slate says "recorded but not applied", so a person who never
  requests directions is never told.

Fix: name it "Lowest pay you'd accept, per", and add "recorded, not applied until pay is
researched" to the hint or the What we know row.

**M5. Visual package gaps.**
- The 1440 `you` capture was taken while "Loading the early sketch" was still showing,
  because `ready` (`apps/web/e2e/visual.spec.ts:186-195`) does not wait for the sketch.
- `you--answer-states` (`:220-232`) scrolls to current role, so Prefer not to say for
  "Lowest pay you'd accept" is outside the viewport at every size.
- No capture shows the salary input in the provided state (amount plus period).

Fix: wait for the sketch, scroll to or capture the pay row, and add a provided-salary state.

**M6. Addendum regression tests are partial.**
- V-02 "recovers in place": no test clicks Try again and sees the profile load, because the
  capture aborts the route.
- S0-V02 asked for the manual-entry action ("Add the details yourself") to be hit-tested and
  for keyboard use to be checked; neither is in `conversation.spec.ts`.

**M7. KeySetup edge cases.**
- After a `CREDENTIAL_REVOKED` 409 (`KeySetup.tsx:190-191`), the copy says "Store a new key
  to continue", but only rotate and revoke for the revoked key are offered until a
  `credential.revoked` event refreshes the list. Mutation errors do not invalidate.
- `.catch(() => undefined)` (`:145`, `:170`) resolves, so `KeyForm` clears the field even on
  failure (`:36`).
- Revoke has no confirmation.
- `type="password"` with `autoComplete="off"` (`:72`) may still trigger the browser's
  save-password prompt, which is at odds with "never kept in your browser".

Fix:
- Invalidate credentials on a 409 and show the store form.
- Clear the field only on success.
- Add a confirmation to revoke.
- Use `autoComplete="new-password"` plus password-manager ignore hints, or say so in the copy.

**M8. Hand-written run-status sets are duplicated and already diverge.**
- `TERMINAL` appears in `Conversation.tsx:32` and `Directions.tsx:35`, `ENDED` in
  `apps/web/src/lib/conversation.ts:20`, and an inline list in `YouChapter.tsx:93`.
- All are untyped `Set<string>`, so a renamed status compiles silently (spirit of Global
  Constraint 10).
- They disagree: `Conversation` treats "complete without a proposal" as failed, while
  `YouChapter` does not.

Fix: one typed helper over the generated `RunStatus`.

**M9. Support flow details (for H-12).**
- The career question heading stays above the support notice.
- "Send my message to Nessa anyway" sends the current composer text, possibly edited and
  untrimmed (`Conversation.tsx:342`), not the message that was screened.
- `checked_on` is shown as raw ISO.

**M10. Stale trays resurface.** `reviewable` (`conversation.ts:70`) brings back older
undecided turns as stale trays after the newest is decided. Consider only the newest turn
that has proposals.

**M11. The Sprint 2 review omits the commit hash.** `docs/reviews/sprint-2.md:4` describes
the reviewed revision as "the last Task 6 commit that changes code or tests" without naming
it (96259d7).

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The You chapter, streaming view, consent UI and S0-V01/V02 fixes are solid and
well evidenced, and no human gate is falsely claimed. But the tray's edit and resend paths
mask failures (Global Constraint 6), undo rewrites provenance, new replies are not announced
after the first, and several "verified" register rows over-state their tests. Fix these
before Sprint 2 closes.
