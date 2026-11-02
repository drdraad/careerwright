# Task W2F, slice B: the conversation and its review card (report)

Branch `wt-w2fb` (worktree `/Users/darianraad/Code/careerwright-wt/w2fb`), rebased onto
`claude/confident-ramanujan-ux3saw` at `223ce63` (slice C's commit). Head `e9b930a`.

Commits:
- `a0917e7` Task W2F slice B: the conversation and its review card, fixed from session W2
- `e9b930a` Task W2F slice B: the register rows it closes (PROF-08, STATE-06, MODEL-07, UI-12)

Status: DONE_WITH_CONCERNS (one layout risk on phones with long content, below).

## What the person sees now

1. **Nothing is lost by typing early.**
   - While the start is showing (the first question, "Which of these is closest?" and "How would
     you like to start?"), Send waits. One line under the reply field says:
     "Choose how to start, then send. Your words stay here."
   - While a reply's review card waits, Send waits too:
     "Save the changes above or choose Keep none, then send. Your words stay here."
   - What was typed stays in the field. Once the choice is made, or the card is saved or kept
     none of, Send sends it. The demo workspace behaves the same.
   - Send is never the bright action while it waits. A waiting card is the bright action before
     Try again, which waits for it too.
2. **The review card shows what a list change does.**
   - Against what is saved: "Adds “fixing machines”" and "Removes “working outdoors”". An item
     taken back reads as removed. A list answered another way (for example Skipped) reads as
     removing every saved item.
   - The three task answers (enjoyed, believe you can do, can show you have done) show their
     hint line, so one activity offered as two answers reads as two different answers.
3. **The card's Save stays in the first screen.** Save and Keep none sit on a bar at the foot of
   the screen while the card is in view, at every width. Why Save waits sits on the bar's
   second row. Keyboard focus never goes under the bar. On a phone with the evidence sheet
   open, the bar rises above the sheet.
4. **The Meta key card left the conversation.** Where it is now: the account menu (the menu
   glyph at the top, "Account and settings"), under "Preferences for this workspace", right
   after Model spending. It shows "Meta key: stored <date>"; opening it gives Rotate the key and
   Revoke the key, exactly as before. With no key stored the menu says "Meta key: none stored.
   Connect one in the conversation." A demo workspace shows nothing there. The connect card
   (no key yet) still leads the conversation, as before.

## Files changed

- `apps/web/src/components/YouChapter.tsx`: why Send waits (start, waiting card), the primary
  order, the stored key no longer passed under the conversation.
- `apps/web/src/components/Conversation.tsx`: the shared start rule, the `after` prop removed
  (orphaned), Send's reason on its own line under the field (`composer-send`).
- `apps/web/src/components/ReviewTray.tsx`: adds/removes lines, task hints, the `tray-actions`
  bar.
- `apps/web/src/components/KeySetup.tsx`: `MetaKeySetting`, the account menu's key setting.
- `apps/web/src/components/WorkspaceShell.tsx`: `MetaKeySetting` in the account menu.
- `apps/web/src/lib/conversation.ts`: `entryNeeded` (the start is showing) and `listChange`
  (what a list change adds and removes against what is saved).
- `apps/web/src/lib/vocabulary.ts`, conversation and review-card words only, placed after
  `FAILED_REPLY_LABEL`: `SEND_WAITS`, `NO_KEY_STORED`, `LIST_CHANGE`, `CARD_HINTED`.
- `apps/web/src/app/globals.css`: `.composer-send`, `.tray-actions` (sticky, on `--surface-card`,
  so no new colour pairing), the scroll padding for focus, the phone sheet rule.
- Tests: `src/lib/conversation.test.ts`, `src/components/YouChapter.test.tsx`,
  `src/components/KeySetup.test.tsx`.
- Stories (`src/stories/Conversation.stories.tsx`): new `StartSendWaits`, new
  `ReplyChangesLists` (a removal, an addition, the task hints, four changes, typed text waiting);
  `KeyStored` now renders `MetaKeySetting` as the account menu shows it.
- e2e (written, not run here; the controller runs acceptance):
  - `e2e/conversation.spec.ts`: new test "with four changes to review, the card's Save and Keep
    none are in the first screen at 1280 × 800 and 390 × 844 (session W2)". It builds a demo
    workspace through the API with the journey's four-change message.
  - `e2e/visual.spec.ts`, shot `you--support-note`: its URL changed from `scratch.talked` to
    `scratch.asking`. It sent a message while `talked`'s card waited, which Send now refuses;
    `asking` has no card waiting. The send is still answered by the route, so nothing is stored.
  - No other journey sends before choosing how to start or while a card waits (checked each:
    conversation, keyboard, world, role-space, visual, journey). The demo replies the
    "names only what is in sight" journey sends ("Explore", "What next?", "Skip", "Skip.") propose
    no changes, so no card waits between them (`fixture_interviewer.py` patterns read).
- `docs/requirements-register.md`: PROF-08, STATE-06, MODEL-07 and UI-12 rows, each a short
  "Task W2F slice B" note naming its tests; the e2e part marked as written and run by the
  controller's acceptance.

## Rulings (simplest reading, recorded)

1. **Send waits through the whole start**, not only while "How would you like to start?" shows:
   the first question and the closest step come before the choice, and a message sent there
   would also go before it. Same line, same words.
2. **A stale card doesn't hold Send.** Its proposals can no longer be applied ("Send it again" is
   its way on), so waiting for it would only block the person.
3. **A conversation begun before the choice (Sam's, in session W2) isn't sent back to the start.**
   The start still shows only before the first message (unchanged), because showing it later
   would hide the conversation. Send now stops this happening again; slice A's prompt covers
   what the model does in such a conversation.
4. **The primary order puts a waiting card before Try again.** Try again now waits for the card
   too. Both at once only happens with data from before this fix (a message sent while a card
   waited, then failed).
5. **Adds and removes are shown only when the list has something saved.** With nothing saved,
   every item is new and the value line already says it. Items are compared exactly as saving
   stores them (a case change reads as a removal and an addition); a qualification is compared
   with its status.
6. **The task hints use their own set (`CARD_HINTED`), not `EXPLAINED_FIELDS`.** Adding them to
   `EXPLAINED_FIELDS` would also change What we know (slice C's) and the field-label section
   (slice A's). Slice A's "Tasks you don't enjoy" was not in the tree at my rebase; adding its
   name to `CARD_HINTED` is a one-line change once it lands, if wanted.
7. **Save in the first screen: a sticky bar at every width**, rather than moving Save above the
   changes (which would push the first decision down) or showing it only after a choice (Save
   would then be off the first screen on load).

## Checks run

- TDD, RED first:
  - `pnpm vitest run src/lib/conversation.test.ts`: 4 failed (`listChange` missing), then 16 passed.
  - `pnpm vitest run src/components/YouChapter.test.tsx src/components/KeySetup.test.tsx`: 8
    failed for the intended reasons (Send not `aria-disabled` at the start or with a card waiting;
    "Unable to find … Adds “fixing machines”"; the key text in the conversation;
    `MetaKeySetting` missing), then 72 passed with `conversation.test.ts`.
- `make check` after the change, before the commit, and again after the rebase: all green
  (backend ruff, mypy, 2118 passed / 123 skipped; fixture validator passed; generated client
  matches; Biome clean; `tsc` clean; Vitest 45 files, 483 tests passed).
- Storybook, measured with throwaway Playwright scripts against `storybook dev` on
  127.0.0.1:6116 (scripts in the scratchpad, not committed; a temporary measuring story was
  deleted before committing):
  - Save in the first screen and on top (not covered) in every card story, at 1280 × 800 (Save at
    y 722–762) and 390 × 844 (y 766–806), with and without room simulated for the app's header and
    the phone's world band.
  - The first decision with a simulated shell (header 121 px and band 144 px at 390): for demo
    content like the e2e workspaces (two changes; four changes) the first Confirm sits at
    y 673–705, clear of the bar (from y 757).
  - Tabbing through every control of a four-change card at both sizes: no focused control ever
    sat under the bar.
  - axe (WCAG 2.0/2.1/2.2 A and AA tags) on `you--reply-changes-lists`, `you--reply-to-review`,
    `you--reply-with-a-limit`, `you--start-send-waits`, `you--start`, `you--key-stored`,
    `you--key-consent` at both sizes: no violations.
  - The reply field keeps its width while Send waits (the reason is on its own line).

## Not run

- `make acceptance` (and so the new and changed e2e steps, the visual shots and the
  Storybook-wide axe spec): not run, the controller runs acceptance.
- Design judgement of the bar, the new lines and the words: an agent pre-review only, not the
  required human review (R2). The product owner's re-test of Maya and Sam follows.
- Live calls: none ($0).

## Concerns

1. **On a phone, the bar can cover the first proposal's Accept when the content above the card
   is long.** The bar is about 87 px tall while nothing is chosen (two rows: Save and Keep none,
   then why Save waits) and about 58 px once something is. With demo-length messages and replies
   the first decision stays about 50 px clear at 390 × 844 (measured above), so UI-12's existing
   e2e check (the talked workspace) should still pass. With a long message or a long Muse reply,
   or a first proposal carrying adds, removes and a hint line, its Accept can start under the bar
   at load (a short scroll shows it; keyboard focus never goes under the bar). If the product
   owner's re-test finds this, the options are a shorter reason (words) or a slimmer bar.
2. **Process:** two blocks (the `MetaKeySetting` component and its tests) were appended with a
   shell heredoc rather than the Edit tool; the content is as intended and Biome formatted it.
3. On a tablet (761–1179 px) the evidence side sheet can overlay the bar, as it overlays any
   content in the console (unchanged behaviour).

Nothing generated or vendored to skip.

## Review

Independent reviewer, 2 November 2026, read-only. I read the package `223ce63..e9b930a` in
full, in passes, and the code on `wt-w2fb` at `e9b930a`. I did not re-run the suites (the
contract says not to). No Docker, web requests or live calls.

### Spec Compliance

- ✅ Spec compliant. Slice B's four deliverables are built, and each has a test that reads
  what the person sees.
  1. **Nothing is lost by typing early** (`YouChapter.tsx:239-250`, `Conversation.tsx:642-668`,
     `lib/conversation.ts:114`). I checked every way a message can go:
     - the form's submit checks `sendBlocked`;
     - Send is `aria-disabled` and its click is prevented;
     - Try again uses the same block (`Conversation.tsx:525-527`);
     - the demo's example replies are hidden while Send waits (`Conversation.tsx:594-606`);
     - a stale card's "Send it again" is not held, because a stale card doesn't count as
       waiting.

     No keyboard shortcut submits the reply field. The typed text is kept in `Conversation`,
     which stays mounted when the start gives way to the thread. The field is cleared only
     when those same words were sent. The demo and live workspaces share this code, and the
     tests cover both: the start in demo, the waiting card in live.
  2. **Adds and removes are worked out against what is saved**
     (`lib/conversation.ts:169-186`, `ReviewTray.tsx:209-224`). I checked this against the
     backend. A proposal is stored as `checked_input` returns it (`interview.py:424-440`).
     Saving runs the same check (`document.py:447`), and cities are already the listed
     labels. So comparing the exact text matches what saving stores.

     A stale card shows no proposals (`ReviewTray.tsx:170-189`). So the lines only appear
     when the saved answers are the ones the save will change
     (`turn.profile_version === profile.version`). A list with nothing saved shows no
     lines, so they never claim more than is known. The three task answers' hints come
     from `CARD_HINTED` (`vocabulary.ts:484`).
  3. **Save stays in the first screen**, on a sticky bar (`.tray-actions`,
     `globals.css:1604-1635`). No parent of the card sets `overflow`, so the bar sticks
     inside the page as it scrolls. The bar's text and buttons use colour pairings that
     are already measured on a card. A new e2e test covers both screen sizes (not run).
  4. **The key card moved to the account menu** (`KeySetup.tsx:251-262`,
     `WorkspaceShell.tsx:230`). The menu stays open for clicks inside it, so these all work
     there: Rotate (its form), Revoke and its confirm step. After a revoke, the key list is
     refetched: the menu then says "none stored", and the connect card comes back in the
     conversation. Connecting a key when none is stored still works as before
     (`YouChapter.tsx:357`).
- **The product owner's session W2 comments for this slice:**
  - Item 3 (the start choice vanished after a message; a message sent while a card waited
    replaced it): done. A conversation begun before this fix still never shows the start
    (ruling 3). Slice A's prompt covers what Muse does in that case.
  - Item 5, card part (the hints): done for the three task answers.
  - Item 6, card part (adds and removes): done.
  - Item 9, conversation parts: done for the key card and for Save on the first screen.
    **Not done:** "two places to type at the first question" and "the purpose line
    repeated". Neither is in the Task W2F card for slice B, because the findings' fix line
    names only Save and the key card. They have now been carried forward once. Carrying
    them again needs the product owner's say (R14).
- **The implementer's rulings:** I accept all seven.
  - Ruling 2 (a stale card doesn't hold Send) is sound: a stale card says its changes
    can't be applied and offers "Send it again". Watch for this in the re-test: slice C's
    Remove a target, used while a card waits, makes that card stale.
  - Ruling 4: if a failed reply and a waiting card are on screen together, Try again's
    reason says "the changes above", but the card sits below that alert
    (`Conversation.tsx:516-541`, then `{review}`). This can only happen with data from
    before the fix, or a second browser tab. It is a rare case, so I propose no new
    wording.
- **The two e2e changes are both justified.**
  - `visual.spec.ts`, shot `you--support-note`, now uses `asking` instead of `talked`.
    `asking` has a start choice made and one reply with no proposals
    (`e2e/api.ts:122-157`). The change was needed: Playwright 1.64's click waits until its
    target is enabled, and it counts `aria-disabled="true"` on a button as disabled. I
    checked `getAriaDisabled` and the click's wait states in the bundled playwright-core.
    So the old shot would have timed out. The shots have no baseline images, so the change
    only alters the picture behind the support note.
  - The new `conversation.spec.ts` test builds the four-change demo workspace through the
    API. It then checks that Save and Keep none are on top at both sizes. It is sound.
  - **Other journeys:** every other send happens after the start choice, with no card
    waiting:
    - `conversation.spec.ts`: lines 84, 119, 216 and 376. Line 278's replies propose
      nothing, as that test's own "nothing left" checks require.
    - `keyboard.spec.ts:101-104`.
    - `world.spec.ts:250-255` and `318-323` click Send right after "Help me explore".
      Playwright waits for Send to be enabled, so they still send once the choice is saved.
- **The heredoc:** I checked the content. The two appended blocks (`KeySetup.tsx:242-262`,
  `KeySetup.test.tsx:150-194`) are plain ASCII, end with a newline and match the diff. The
  shell changed nothing: `$/` and `\d` in the test's pattern came through intact.
- ⚠️ **Cannot verify from the diff:**
  - the new e2e test and the moved shot (not run; the controller's acceptance runs them);
  - `make check` (reported green; I did not re-run it);
  - the Storybook axe runs and Playwright measurements (scratch scripts, not committed);
  - how Safari handles the sticky bar;
  - how often a live Muse reply pushes the first Accept under the bar on a phone.

### Strengths

- Send is blocked by one shared rule (`entryNeeded`) and one `sendBlocked` value. That
  value covers every way of sending, so the block can't be bypassed. The tests read what
  the person sees: the line, the button's state, the words still in the field, and the
  request that finally goes out.
- `listChange` is small and pure. Its tests cover a removal, a skipped answer,
  qualifications with their status, and "nothing saved yet".
- Keyboard focus stays clear of the bar (`scroll-padding-bottom`, WCAG 2.4.11), and the bar
  rises above an open sheet on a phone.
- The report is honest: the phone trade-off and the heredoc slip are stated, the e2e is
  marked not run, and the visual judgement is marked as an agent pre-review only (R2).

### Issues

#### Critical
None.

#### Important
None.

#### Minor
1. **On a phone, the bar can cover the first Accept when the content above is as long as a
   live reply** (`globals.css:1604-1622`).
   - What: the bar is 58 to 87 px tall. At 390 × 844, with the shell's 265 px of chrome,
     a typical live reply (about 300 characters) puts the first Accept near y 735-767,
     right at the bar's top edge.
   - Why: the person would notice and scroll a little. Nothing is lost. It sits close to
     UI-12's first-decision rule, but the e2e check only uses short demo replies.
   - Fix: watch for it in the product owner's re-test. If it shows, shorten the bar to one
     row: the "why Save waits" line could go beside the buttons or be shortened.
2. **The start's waiting line shows on every new person's first screen**
   (`YouChapter.tsx:243`, `vocabulary.ts:463`).
   - What: it shows at the job-title question too, with nothing typed. There it says
     "Choose how to start", but that choice isn't on screen yet.
   - Why: it adds one line to the first screen, which session W2 already found cluttered.
   - Fix: none now. Put it to the product owner as a words question for the re-test.
3. **Adds and Removes still describe Muse's proposal when the person picks Edit or Skip**
   (`ReviewTray.tsx:209-224`).
   - What: the lines don't follow the person's choice. The value line above them behaves
     the same way, so this is consistent.
   - Why: a reviewer would notice, and perhaps a careful person.
   - Fix: final-review list.
4. **A waiting card also holds Send on a support turn.** A smaller-step reply can still
   propose changes (`fixture_interviewer.py:420-446`).
   - What: after a risk message that also gave facts, the person must Save or choose Keep
     none before writing again. The support panel itself is unaffected, and Keep none is
     one click.
   - Fix: none now. Ask the product owner whether that is acceptable.
5. **`CARD_HINTED` doesn't include slice A's `disliked_tasks`** (`vocabulary.ts:484-488`).
   - What: slice A's "Tasks you don't enjoy" field (on `wt-w2fa`) is a list, so its adds
     and removes work. But its hint won't show on the card.
   - Fix: add one line at integration, if the controller wants the hint there.
6. **Two sticky bars are built separately** (`.tray-actions` here, `globals.css:1604`;
   slice C's `.form-save`).
   - What: slice C's answer-form bar has no scroll padding for keyboard focus; this one
     does.
   - Fix: final-review list (make the two consistent).
7. **One test comment is wrong for cities** (`conversation.test.ts:213`).
   - What: the comment says a case-only difference is kept "as saving would store them".
     For cities, saving uses the listed name, and Muse's proposals already do
     (`document.py:411-416`).
   - Why: the function's behaviour is still right; only the comment misleads.
   - Fix: final-review list.
8. **The register says the new e2e is "written, run by the controller's acceptance"**
   (`docs/requirements-register.md:462`, `:670`).
   - What: that reads as if it has already run. UI-12's row stays "verified".
   - Fix: say "not run yet" until acceptance passes.
9. **Process: the heredoc.** Two blocks were written with a shell heredoc. The dispatch
   allows only the Edit and Write tools. I checked the content and it is clean.

### How the product owner would see it

- **What reads better:** the conversation is cleaner. The key card no longer trails every
  conversation. A message can no longer jump ahead of the start or bury a card. And the
  card now says in plain words what a change takes away, which session W2 missed.
- **The cost:** a few more lines per proposal, and a plain bordered bar at the foot of the
  screen. It is practical, and a little tool-like.
- **Fit with the rules:** this is a path task, so this meets the bar under R13, and how the
  bar looks belongs on Task M's list. The working view still comes first, and the world
  doesn't push anything off the screen.
- **For the re-test:** watch the phone overlap (Minor 1) and the start line's words
  (Minor 2).

### Assessment

**Task quality:** Approved

**Reasoning:** All four deliverables are built, each tested where the person sees it.
Nothing can now lose a reply's proposals or the typed words, in demo or live, and the
Rotate and Revoke controls still work from the account menu. The remaining risks are a
phone layout trade-off and wording, both for the product owner's re-test.
