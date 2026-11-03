# Task W2F, slice E: no em dashes, and a review card with half the words (report)

Branch `wt-w2fe` (worktree `/Users/darianraad/Code/careerwright-wt/w2fe`), rebased onto
`claude/confident-ramanujan-ux3saw` at `1bda36b`. Head `c9a0d06`. (The SHAs below the
"Follow-up" heading are current; those in the first part predate two rebases.)

Commits:
- `28b89fe` Task W2F slice E: no em dash in what a model writes, and an answer state is never a value
- `0953205` Task W2F slice E: the review card with half the words; a state's code is never shown
- `0fd052c` Task W2F slice E: an answered question leaves while its answer is replied to
- `88d9ea2` Task W2F slice E: one place to type at the start, plain-words list changes, Research again, the Save bar's room, and a conversation that follows its newest part
- `c9a0d06` Task W2F slice E: the ADR amendments and the register rows it closes (PROF-02, PROF-08, STATE-06, STATE-11, REC1-11, DIV1-15)

Status: DONE_WITH_CONCERNS (one process slip with Storybook, and two small layout notes, below).

## What the person sees now

1. **Muse never writes an em dash.**
   - Every prompt whose words the person reads now says, in one line: "Never write an em dash
     or a spaced en dash; use a comma, colon or full stop."
   - The checks refuse an em dash, or an en dash with a space either side, so the existing
     repair asks Muse again. Code never rewrites Muse's words.
   - Where: the interview's reply, its next question, each change's reason (shown under
     Source) and each proposed value; the "Why this could suit you" sentences; discovery's
     search phrases and title ideas (both shown in Muse's own words).
   - A dash the person wrote is theirs. If the same words sit either side of the dash in
     their own messages or answers, it is not refused. Quotations were already kept in their
     source's own characters, so a dash Muse typed in place of the person's hyphen is never
     shown.
   - The overlooked strength: its model writes no sentences, only a quotation, which is kept
     in the person's own characters. A test shows Muse's dash never reaches the person. Its
     prompt is unchanged.
   - New prompt versions: `interview-turn-7`, `slate-explanation-2`, `discovery-queries-4`.
2. **A role can no longer be saved as "no_job_yet"** (the coordinator's added item).
   - The check refuses any proposed text or list item that is an answer state's code
     (no_job_yet, unknown, skipped, prefer_not_to_say, unasked, provided), ignoring case,
     spaces, hyphens and underscores. The repair asks again.
   - The interview instructions now say "no_job_yet" is "a state, never text".
   - In the web app, a code saved before this fix reads as the state's words ("I haven't had
     a job yet") on the card and in What we know, and gets no "Research this role".
   - No data migration: the product owner's two workspaces are corrected by hand.
3. **The review card has about half the words.**
   - Each change reads in two lines on a wide screen: "Tasks you enjoy: adds fixing machines,
     removes helping at Brownies" (plain words since the follow-up below), then "Your words"
     (or "Careerwright's reading") and its actions.
     A new answer shows just its value. The dashed edge for Careerwright's reading stays.
   - The task answers' hints and the two limits' plain words are one step away: a small info
     button beside the answer's name ("What total spending limit means") opens them in place.
   - The tray heading is "To review: 4 changes".
   - Save's reason is "Accept or edit one first." and sits beside Save and Keep none when
     there is room.
   - Send's reasons are a few words ("Choose how to start, then send.", "Save or choose Keep
     none, then send.") and show only once something is typed.
   - Kept: a limit's Confirm is still named "Confirm total spending limit as a limit"; every
     action keeps its accessible name; Save and Keep none stay on the bar at the foot of the
     screen; nothing typed is lost; the origin is always shown; leaf green for Accept and
     Confirm, teal for actions.
   - Measured in Storybook: each card is 90 px tall at 1280 px wide (the reference screenshot's
     first card was about 205 px). At 390 px a card is three rows (name, tag with Accept and
     Edit, then Skip and Source), 126 to 150 px.
4. **An answered question leaves** (the coordinator's second added item; the product owner:
   "the question about pay was still showing after I had answered it").
   - Cause: the question on screen was always the newest checked reply's next question. While
     the person's answer was on its way, and while Muse's reply to it streamed, the newest
     checked reply was still the one that asked, so the answered question stayed.
   - Fix (`Conversation.tsx`): no question shows while a message is on its way or the newest
     turn has no checked reply yet. Once the reply is checked, its card shows first; the next
     question appears after the card is decided, as before.
   - A failed reply already hid the question; it still does.

## Files changed

- Backend: `backend/src/careerwright/profile/dashes.py` (new: the one prompt line and the one
  check), `profile/interview.py` (checks, state codes, `interview-turn-7`, words trimmed),
  `profile/slate_explanation.py` (`slate-explanation-2`), `profile/discovery.py`
  (`discovery-queries-4`).
- Backend tests: `tests/domain/test_interview_contract.py`, `test_slate_explanation.py`,
  `test_discovery_contract.py`, `test_strength.py`; `tests/integration/test_interview_choices.py`
  (the sealed prompt version is now 7).
- Web: `src/components/ReviewTray.tsx`, `Conversation.tsx` (Send's reason only once typed; no
  question while the answer to it is replied to),
  `Directions.tsx` (no research for a state code), `Glyph.tsx` (an `info` glyph),
  `src/lib/vocabulary.ts` (`REVIEW_CARD`, shorter `SEND_WAITS`; `LIST_CHANGE` replaced),
  `src/lib/profile.ts` (`isStateCode`, state codes shown in words), `src/app/globals.css`.
- Web tests and stories: `YouChapter.test.tsx`, `profile.test.ts`, `RoleResearch.test.tsx`,
  `src/stories/Conversation.stories.tsx` (new `ReplyWithALimitExplained`; notes updated).
- Docs: ADR 0006 and ADR 0007 amendments (2026-11-03); register rows PROF-02, STATE-06,
  STATE-11, REC1-11.

Journey steps changed: none. Every e2e step that reads the card finds it by
`/To review: N changes/` and its buttons by their accessible names, which still match. The
e2e `send` helper types before it checks Send, so Send's reason behaves as before there. The
journeys read the question (`questionShown`, `.question` counts) only after a card is saved or
a reply has landed, when the new rule shows the same question as before. The visual shots
that include the card will look different (no baselines are kept).

## Rulings (simplest reading, recorded)

1. **The strength's prompt is unchanged.** Its model writes refs and a quotation only, and the
   quotation is stored in the person's characters. A "never write an em dash" line would
   contradict "copy their words exactly" when the person used one. A guard test covers it.
2. **Discovery is included** as "other person-facing model text": its queries and title ideas
   are shown in Muse's words. A query that is the person's own title keeps their dash.
3. **"The person's dash" means the same words either side.** A dash in the model's text is
   allowed only if the word before it, the dash and the word after it appear together in the
   person's own words. Their dash elsewhere is no licence for Muse's own.
4. **Reasons and values are checked too.** The reason shows under Source and the value on the
   card, so both are words the person reads.
5. **One step away is an info button beside the name**, not the Source drawer: the person
   would not look under "Source" for what a limit means. It is a new control with its own
   accessible name; it shows for the four task answers and the two limits, as the hint line
   did before.
6. **Send's reason shows only once something is typed, for every reason** (paused, still
   replying, no key, the start, a waiting card). With an empty field Send sends nothing, as
   before. Try again and Send it again keep their reasons as they were.
7. **Origin tags** are "Your words" and "Careerwright's reading".
8. **The prompt's context still shows each field's state as its code.** Rendering states
   differently would change what the demo interviewer reads; the instruction and the check
   cover it, and the instructions fit the byte guard (4,238 bytes, under 4,250, words cut,
   no rule removed).

## Checks run

- TDD, RED first:
  - `pytest tests/domain/test_interview_contract.py -k answer_state`: 2 failed (the check
    accepted "no_job_yet": `assert [] == ['current_role: "no_job_yet" is an answer state…']`;
    version 6, not 7), then passed.
  - Same file, `-k "dash or answer_state"`: 4 failed for the dash rule, then all 61 passed.
  - `test_slate_explanation.py -k dash`: the claim test failed; the quotation test passed at
    once (existing behaviour, kept as a guard); then 94 passed with `test_spend.py`.
  - `test_discovery_contract.py -k em_dash`: failed (`assert [] == [...]`), then passed.
  - `test_strength.py`: the guard passed at once (existing behaviour, by design).
  - Vitest (`YouChapter.test.tsx`, `profile.test.ts`): 7 failed for the intended reasons (old
    words, hints shown, no info button, the code shown raw), then 496 of 496 passed.
  - The answered question: `YouChapter.test.tsx` "takes an answered question away while its
    answer is replied to" (a decided turn that asked about weekly hours, then the answer's
    turn streaming) failed first (`expected <h2 id="question-title"> to be null`), then 497
    of 497 passed.
- `make check` after each change and after the second rebase: all green (ruff format and
  lint, mypy, 2157 passed and 123 skipped; fixture validator passed; generated client matches;
  Biome clean; `tsc` clean; Vitest 46 files, 497 tests).
- Focused integration runs, each under the lock in one guarded command:
  - `test_interview_turns.py` and `test_interview_choices.py`: 30 passed.
  - `test_slate_explanations.py` and `test_discovery.py`: 30 passed.
  - `test_origin.py` (the strength and "I haven't had a job yet"): 18 passed.
- Storybook (agent pre-review, not the required human review, R2), with throwaway Playwright
  scripts in the scratchpad (not committed):
  - axe (WCAG 2.0, 2.1, 2.2 A and AA) on all 31 You stories at 1440 × 900, the acceptance
    size: no violations.
  - At 1280 × 800: `reply-changes-lists`, `reply-to-review`, `reply-with-a-limit`,
    `reply-with-a-limit-explained`, `start-send-waits`, `start`: no violations. At 390 × 844:
    the same, except one (concern 3).
  - Tabbing through the cards at 1280 × 800 and 390 × 844: no focused control under the Save
    bar.
  - Save and Keep none in the first screen at both sizes.

## Not run

- `make acceptance`: not run, the controller runs acceptance (it covers the e2e journeys,
  the visual shots and the Storybook-wide axe spec).
- Live calls: none ($0). The capped live checks of `interview-turn-7`, `slate-explanation-2`
  and `discovery-queries-4` on the test model are the controller's (R5).
- Design judgement, VoiceOver and Safari: not run, requires human.

## Concerns

1. **Process slip: one outbound request.** I first started Storybook without
   `--no-version-updates`. Storybook's own update check contacted its version service (it
   reported "A new version (10.6.5) is available"). Telemetry was off by the project's config.
   I stopped it at once and restarted with the update check off. No key or data was involved.
   The project's `pnpm storybook` script has the same update check.
2. **A refused reply can flash a dash.** The reply streams before it is checked (ADR 0006
   decision 13). If Muse writes a dash, the person may see it for a moment before the
   repair's reply replaces it. Each refusal costs one paid repair, and a second dash ends the
   turn as an invalid output. The prompt line should make both rare; the live check will
   show how rare.
3. **On a phone, the Save bar can partly cover a control at load.** axe at 390 × 844 flags the
   third card's Source button in `you--reply-to-review` as partly under the sticky bar
   (target size). Which control sits at the bar's edge depends on content length; the person
   scrolls a little. The acceptance axe run (1440 × 900) is clean. Slice B noted the same
   kind of overlap.
4. **The minus sign looked like a dash.** A removed item was marked with the minus sign
   (U+2212), which in this font looks like an en dash. Resolved in the follow-up below: list
   changes are now in plain words.
5. Left as they were (not in this slice's list): the stale card's sentence ("Your answers
   changed after you sent …"), the demo's "I noted 4 things for you to review." line, and
   source search candidate titles (page titles, a source's words, in slice D's files).

Nothing generated or vendored to skip.

## Follow-up: five more items from the re-test (commit `88d9ea2`)

What the person sees now:
1. **One place to type at the start.** The first question has only its job title field; "How
   would you like to start?" has only its two choices. The reply field appears with the
   conversation's first question. (Send's "Choose how to start" reason is gone with it.)
2. **Research again after "not yet found".** Offered after not yet found, a stopped search, no
   pages or a stopped reading, never after found. Each shows the cost first, as a first
   research does.
3. **A list change in plain words.** "Tasks you enjoy: adds fixing machines, removes helping at
   Brownies". No plus or minus signs. Several items read "adds a, b and c".
4. **Focus never goes under the Save bar, at any width.** The window now keeps the bar's
   measured height clear, as the answers form does. At 320 px the bar is three rows (135 px);
   the fixed 96 px let Edit, Skip and Source go under it.
5. **The conversation follows its newest part.**
   - Once the person sends, the reply field stays in view as the message, the streamed reply
     and its card arrive.
   - It never scrolls the person's own newest message above the top, so the reply reads from
     its start and the card's first decision stays near it.
   - Scrolling up stops it. Coming back to the end resumes it. Opening the chapter never
     scrolls.
   - Under reduced motion or calm mode it jumps; otherwise it glides. Focus never moves.

Journey steps changed (written; the controller's acceptance runs them):
- `e2e/conversation.spec.ts`, "the demo takes a target in the person's words…": at the start,
  no reply field or Send (was: Send not bright); after "I know my direction", the reply field.
- `e2e/visual.spec.ts`, shot "you": no reply field at the first question (was: visible).
- `e2e/world.spec.ts`, "says the same in the moving and the still world": the text check reads
  "Conversation with Careerwright" (was: the reply field's label, absent at the start).
- New: `e2e/storybook.spec.ts`, "tabbing through a waiting review card… at 320 px too".

The journey for load (contract item 6), walked in Storybook at 390 px:
- First question: one place to type (the job title), two actions (I haven't had a job yet,
  Skip for now). Was two places to type.
- Which of these is closest: no place to type, its choices only.
- How would you like to start: no place to type, two equal choices. Was a reply field too.
- The conversation's first question: one place to type, Send, Pause.
- Sending: the answered question goes, the page follows the reply.
- The card: each change two lines on a wide screen, three on a phone; Save is the one bright
  action; Send's reason shows only once something is typed.
- No em dash, en dash or minus sign in any of these views (checked on the page's text).

Rulings:
1. **Following starts when the person sends**, not on opening the chapter, so a page opened
   mid-conversation keeps its first screen (UI-12).
2. **The follow stops at the person's newest message.** On a phone a reply and a four-change
   card are taller than the screen; scrolling to the very bottom would push the first decision
   off it.
3. **Item 4's axe flag at load is a different thing from focus.** At 390 px, in
   `you--reply-to-review`, the third card's Source still sits partly under the sticky bar when
   the story opens. That is where the list happens to cross the bar's edge, not where focus
   goes: no scroll padding can change it. What scroll padding fixes, focus going under the
   bar, was real at 320 px and is fixed. The acceptance axe run (every story, 1440 × 900)
   passes. Removing the load overlap would mean a bar that isn't sticky, which session W2
   rejected (Save fell off the first screen). That is the product owner's trade-off.
4. One combined commit for the five items: they share files (the conversation, its tests,
   the vocabulary), and splitting hunks needs an interactive add.

Checks run:
- RED first:
  - Vitest: the start test (a reply field at the first question), the list wording, and the
    three Research again cases failed; the follow test failed (`scrollBy` never called).
  - The new Storybook journey test failed at 320 px (Edit, Skip and Source under the bar),
    run with Playwright against the static Storybook build. A throwaway config without the
    stack's global setup was used, then removed.
- Then: Vitest 502 of 502; the whole `e2e/storybook.spec.ts` (every story's axe at 1440 × 900,
  the three earlier layout tests and the new one) 5 of 5 passed against a fresh static build.
- `make check` after the rebase onto `1bda36b`: all green (backend 2157 passed, 123 skipped;
  Biome, `tsc`, generated client; Vitest 502).
- Storybook was started with telemetry and update checks off this time (no outbound request).

Not run:
- The changed e2e journeys in conversation, visual and world specs: they need the stack;
  the controller's acceptance runs them.
- The follow in a real browser with a streaming reply: covered by the jsdom test with the
  layout stubbed at its edge; no story streams a reply.
- Safari's handling of an instant scroll; VoiceOver: requires human.

Concerns:
1. The load-time overlap at 390 px (ruling 3).
2. The follow is new behaviour in every live conversation; the product owner's re-test is its
   real check.

## Review

Independent review under `planning/reviewer-contract.md` (Parts 1 to 3), of
`planning/review-1bda36b..c9a0d06.diff`, read in passes (backend; web lib; the card; the
conversation and the follow; tests, e2e and stories; docs), against the worktree at `c9a0d06`.
No suite re-run, no Storybook, no Docker, no web request, no live call. Two throwaway probes ran
with the worktree's Python from the scratchpad, writing nothing in the tree:
`/private/tmp/claude-501/-Users-darianraad-Code-careerwright/51b74d1a-6cb8-4bb3-b832-9054484ac3c7/scratchpad/w2fe-review/repro_saved_dash.py`
and
`/private/tmp/claude-501/-Users-darianraad-Code-careerwright/51b74d1a-6cb8-4bb3-b832-9054484ac3c7/scratchpad/w2fe-review/dash_edges.py`.

Code read outside the diff, one named risk each:
- Does the interview's dash licence cover the person's saved answers? `TurnInput` holds the
  last six messages only (`interview.py:78`, `conversation.py:160`) and the saved profile
  (`context_profile`, `interview.py:513`). Probe run: it does not (Important 1).
- Could the answered question flash back after sending? `useCommand` awaits the turns' refetch
  before `pending` clears (`queries.ts:283-290`), so no.
- Does any e2e step still type before the start's choice? No: every other use of the reply
  field follows a choice or a preset entry mode.
- Does a saved state code still show anywhere? Yes, one place (Minor 1).
- Does the bar's measuring ref clean up? React 19.3 (`apps/web/package.json:34`) runs ref
  cleanups, so yes.
- Dashes the person reads: none in non-comment lines of `apps/web/src/components` and
  `src/lib`; none in backend source strings except the pinned option pack's quoted source
  excerpts (a source's words, never ours).

### Spec Compliance
- Issues found: the dash rule's "a dash in their own words is theirs" is incomplete in the
  interview: a dash in the person's saved answers is refused (Important 1,
  `backend/src/careerwright/profile/interview.py:444-461`).
- Delivered as asked, checked in the code:
  - The one prompt line in `interview-turn-7`, `slate-explanation-2` and `discovery-queries-4`;
    each check refuses an em dash or a spaced en dash, the bounded repair asks again, and no
    code path rewrites Muse's words (`profile/dashes.py`). Leaving the strength's prompt
    unchanged is sound: its model writes only a quotation, stored in the source's characters,
    and a guard test shows Muse's dash never reaches the person.
  - The state code check, with the exact live case as a test (`holding_no_job_yet`: the text
    "no_job_yet" refused, the state itself accepted, "Unknown Soldier tour guide" kept).
  - The card in about two lines: the answer's name and only what changes, the origin as a
    short tag, the dashed edge kept, hints and the limits' plain words one step away behind a
    wired disclosure (`aria-expanded`, `aria-controls`, `hidden`), "Confirm total spending
    limit as a limit" and every other accessible name intact, leaf green for Accept and
    Confirm, Save and Keep none on the sticky bar.
  - Nothing typed is lost: the text stays in `message` while Send waits, and Send's reason
    shows once something is typed.
  - One place to type at the start: the reply field renders only once the start is done
    (`Conversation.tsx:653`), and the start's steps never show together
    (`Conversation.tsx:226-235`).
  - "Research again" after not yet found, a stopped search, no pages or a stopped reading,
    never after found, with the estimate before the button (`RoleResearch.tsx:149`).
  - The answered question leaves while its answer is sent and replied to.
  - The Save bar's room is its measured height, with a Storybook test at four widths.
  - The follow never moves focus, jumps under reduced motion and calm mode, and never scrolls
    the person's newest message off the top.
- Cannot verify from diff: the e2e journeys, the visual shots and the Storybook-wide axe run
  (acceptance not run: the controller's); the capped live checks of the three new prompt
  versions (R5, the controller's); the follow in a real browser with a streaming reply, and
  Safari's handling of `behavior: "instant"`; the card heights (90 px at 1280 px); VoiceOver,
  Safari and design judgement: not run, requires human (R2).

### Strengths
- One small module holds the prompt line and the check for all three prompts; refusal plus
  repair, never a rewrite, as the dispatch asked.
- The exact live failure (a role saved as "no_job_yet") is reproduced in a test at the
  contract's boundary, and the web reads a legacy code in words and offers it no research.
- The question fix is a few lines and cannot flash the old question back.
- The bar's room is measured, not guessed, and a test tabs through the card at 320 px.
- RED-first evidence for each item, and an honest report of the process slip and of what was
  not run.

### Issues

#### Critical
None.

#### Important
1. `backend/src/careerwright/profile/interview.py:444-461`: the interview's dash check counts
   only the turn's last six messages as the person's words, never their saved answers.
   - What: the instructions tell Muse to send a list's complete items, keeping what the
     profile holds. A saved item holding the person's own dash is refused when Muse keeps it
     word for word. That covers an item typed in What we know, one from more than six messages
     ago, or one accepted before this fix. The probe (`repro_saved_dash.py`): a saved enjoyed
     task "helping at Brownies <em dash> mostly crafts" kept in the list is refused; a reply
     naming a saved target "Teaching assistant <spaced en dash> SEN" is refused too.
   - Why it matters (high: lost or changed input): the repair pushes Muse to drop or reword
     the item. The card then shows the person's own words removed, or swapped for Muse's, and
     Accept saves that. Or Muse keeps it, and the second refusal ends the turn as invalid
     output after a paid repair. Phones turn a typed double hyphen into an em dash, and titles
     pasted from adverts often hold a spaced en dash, which "Use my own words" keeps exactly.
     The report's "in their own messages or answers" holds for discovery and the written
     note, not for the interview.
   - Fix: count the saved profile's text values and list items (`context.profile`) as the
     person's words beside the messages, as `_basis` already treats saved items. Add a test
     for a kept saved item and one for a reply naming a saved title.
2. `apps/web/src/components/Conversation.tsx:653` with `YouChapter.tsx:246` (Part 3, the
   journey's load): the reply field and Send stay beside a waiting review card, whose Save or
   Keep none must come first.
   - What: on the card's step the person meets two next actions, the card's Save and the
     reply's Send, and Send can only refuse ("Save or choose Keep none, then send."). This is
     the contract's own example: a reply box beside a choice that must come first.
   - Why it needs a word first: it reverses slice B's "Send waits" design and reads against
     the dispatch's "nothing is lost by typing early".
   - Fix: while a card waits, hide the reply field and Send; what was typed stays in `message`
     and comes back with the field. Or ask the product owner: "While a review card waits,
     should the reply box hide until you save or choose Keep none? Yes hides it, and anything
     you already typed comes back after."

#### Minor
1. `apps/web/src/components/TitleDetails.tsx:231`: a role saved as a state code before the fix
   still reads "Your role: No_job_yet" in What we know's title details. The report's "and in
   What we know" covers the answers list only. Legacy data, which the product owner is
   correcting by hand.
2. `backend/src/careerwright/profile/interview.py:465`: the repair says "give it as the
   state". In the live case the profile already holds no_job_yet, so Muse will likely
   propose the same state again, and the card shows an unchanged "Your current role: I
   haven't had a job yet" with four actions. Better: leave the field out when the profile
   already holds that state.
3. `apps/web/src/lib/vocabulary.ts:525`: Save's reason "Accept or edit one first." also shows
   on a card holding only limits, whose buttons say Confirm.
4. The implementer's open concern, the phone Save bar over a Source button at load: as I read
   it, not a WCAG failure.
   - Focus never goes under the bar (2.4.11): the new Storybook test tabs through the card at
     320, 390, 768 and 1440 px (the implementer's run).
   - The axe flag at 390 px is target size (2.5.8), for a full-size Source button whose lower
     part sits under the sticky bar at the story's opening scroll position. A small scroll
     shows all of it. Which control sits at the edge depends only on content length, as with
     any sticky footer.
   - No check fails: acceptance runs axe at 1440 px only. If a phone-width axe run is added,
     scroll the story first.
   - The one pointer risk: a tap on the covered part lands on the bar. Save saves only what
     the person chose, and Undo follows.
5. `apps/web/src/lib/followLatest.ts:76` and `:87` (from reading, not run in a browser):
   - Following starts on any scroll that reaches the end, not only on Send (ruling 1).
   - It stays on while the person is in another view. When the Conversation view shows again
     its size changes, so `keep` runs and the window can scroll while focus stays on the tab.
     On a phone the focused tab can leave the screen. It never scrolls past the person's
     newest message.
6. `backend/src/careerwright/profile/dashes.py:20`: when punctuation stands right before a dash
   (a closing quote mark, say), the licence needs only the dash and the word after it. A
   person who once wrote "bikes<em dash>and" licenses Muse's `"bikes"<em dash>and`
   (`dash_edges.py`). Rare.
7. Known limit, disclosed: a refused reply's dash can show while it streams. The capped live
   check should count dash refusals, so the product owner can judge how often it happens.
8. Rebase: the integration branch has moved to `30b8737` (slice D round 2). Both slices append
   to the register's DIV1-15 row, so the rebase will conflict there: keep both sentences.
   The `vocabulary.ts` edits are in different places. Re-run `make check` after.
9. Process: the disclosed outbound request came from Storybook's update check.
   `apps/web/package.json:21` (`pnpm storybook`, a command in `CLAUDE.md`) turns telemetry off
   but not the update check, so the next agent who runs it makes the same request. Add
   `--no-version-updates`.

### The journey and its load (Part 3)
Walked from the code, as the person meets each step (places to type / actions / lines read):
1. The first question: 1 (the job title) / 2 (I haven't had a job yet, Skip for now) / 3 (the
   question, what Careerwright is for, England only). No reply field. Pass.
2. Which of these is closest, when offered: 0 / its choices and "None of these is my job".
   Pass.
3. How would you like to start: 0 / 2 equal choices / the question and England only. Was a
   reply field too. Pass.
4. The conversation's first question: 1 / Send and Pause / the question and one helper line.
   Pass.
5. Sending and the streamed reply: the answered question goes; the field stays; Send says
   nothing unless something is typed; the window follows without moving focus. Pass.
6. The card, four task changes: per change 2 lines wide (3 rows on a phone), 4 actions and an
   info button; then Save (the one bright action), Keep none and "Accept or edit one first."
   Below it, the reply field and Send: a second next action on this step (Important 2). The
   Confirm-only wording slip is Minor 3.
7. After Save: "Saved to What we know" with Undo, then the next question. Unchanged.
8. Research this role, not yet found: 0 / 2 (the read pages, one step away; Research again) /
   the title, why, the result and its reason, then the cost just before the button. Pass.
9. No em dash or spaced en dash in any of these views' own words.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** Important 1 can remove or reword a person's saved answer, a lost-input problem
to fix inside this piece. Important 2 is a load finding that needs the product owner's yes
before it changes slice B's design. Everything else is Minor and can wait for the final
review.

## Fix round (Important 1 and 2)

Branch `wt-w2fe`, rebased onto `claude/confident-ramanujan-ux3saw` at `ec059b3`. Head `b5daf8a`.
The Minors are left for the final review, as asked.

Commits (after the rebase):
- `49085ae` Task W2F slice E fix: a dash in the person's saved answers is theirs (review, important 1)
- `97bf222` Task W2F slice E fix: no reply field while a review card waits (review, important 2)
- `b5daf8a` Task W2F slice E fix round: the register rows it closes (PROF-02, STATE-06, UI-06)

### What changed

1. **A dash in the person's saved answers is theirs** (`backend/src/careerwright/profile/interview.py`).
   - The interview's dash check now counts the saved answers as the person's words, beside
     the turn's messages: each text, list item and qualification name in the profile the turn
     carries (`_saved_words`).
   - So a list kept word for word ("helping at Brownies", their em dash, "mostly crafts") and a
     saved title a reply names ("Teaching assistant", spaced en dash, "SEN") are no longer
     refused or repaired away.
   - Muse's own prose still never carries a dash: the licence still needs the same words
     either side of the dash, so a dash between other words is refused as before.
   - No new prompt version: the prompt is unchanged, only the check.
   - ADR 0006's slice E amendment says so (one sentence).
2. **No reply field while a review card waits** (`Conversation.tsx`, `YouChapter.tsx`,
   `followLatest.ts`).
   - While a card waits, the reply field and Send step aside. Its Save or Keep none is the one
     next action. Demo and live alike.
   - Whatever was typed stays and comes back with the field.
   - Focus: if it was in the reply field or on Send when the card arrived, it goes to the
     card's first choice (the first change's Accept or Confirm). After Save or Keep none it
     lands in the reply field. After Undo it still goes to the "Save undone" notice.
   - A button that used to hand focus to the reply field (dismissing a support panel,
     Resume) now hands it to the card's first choice while there is no field, so focus is never
     lost.
   - While there is no reply field, the conversation follows its own end instead, still never
     scrolling the person's newest message off the top.
   - Stories: `you--reply-changes-lists` no longer types into the reply field (there is none);
     its unused helper went with it. Vocabulary: only comments changed; "Save or choose Keep
     none, then send." is still said by Try again.
   - ADR 0007's slice E amendment and the register rows (PROF-02, STATE-06, UI-06) say so.

### Rulings

1. **The card's first choice is found in the page**, as the first toggle button in a change
   (Accept or Confirm; the info button is not a toggle). The dispatch said focus moving to the
   card was already handled; it was not (nothing moved focus, and with the field gone focus
   would have fallen to the page), so I added it.
2. **Focus moves to the card only when it was in the reply field or on Send as they went.**
   Opening the chapter with a card waiting, or reading elsewhere, never moves focus.
3. **A stale card keeps the reply field.** It has no Save or Keep none, only "Send it again".
4. **Paused with a card waiting: no reply field either.** Resume is still the bright action.
5. **Dismissing the calm panel after a save still returns focus to the "Saved" notice**, as
   before: that is not a decision on the card.
6. **Saved words are every saved value**, not only ones first stated: the turn's context
   holds no sources, and the person accepted or typed each one.

### Tests, RED then GREEN

- Important 1, `uv run --locked pytest tests/domain/test_interview_contract.py -k "saved_answer or saved_title"`:
  - RED: 2 failed. The kept list: `assert ['enjoyed_tasks: no em dash or spaced en dash; use a comma, colon or full stop'] == []`.
    The reply naming a saved title: `assert ['reply: no e...or full stop'] == []` (the reply
    and the next question both refused).
  - GREEN: 2 passed; the whole file 63 passed.
  - The kept-list test also keeps a saved qualification ("BTEC", en dash, "engineering"). A
    throwaway probe (scratchpad, not committed) showed it is refused when only plain strings
    count, so that part of the change is needed.
- Important 2, `pnpm exec vitest run src/components/YouChapter.test.tsx`:
  - RED: 3 failed, 49 passed.
    - "has no reply field while a card waits, and brings it back with what was typed after
      Keep none" (new; typed while the reply streams, then the card arrives):
      `expected <textarea> to be null`.
    - "follows once the person sends…" (extended: the card arrives, the conversation's own end
      is followed): `expected <textarea> to be null`.
    - "reverts to the version before the save…" (focus after Save): `expect(element).toHaveFocus()`.
  - GREEN: those 3 passed. Two older tests assumed a reply field beside a card and were
    updated: "keeps a typed reply, the tray's choices…" became "keeps a typed reply" (with no
    card) and "keeps the tray's choices, the answer form's edits and the slate's picks";
    "applies a limit only once confirmed by name…" now checks there is no Send and one bright
    action, where it checked Send was not bright. Then 46 files, 503 tests passed.

### Commands and output

- `make check` after each change: all green (after fix 1: backend 2159 passed, 123 skipped,
  Vitest 502; after fix 2: backend 2159 passed, Vitest 503).
- Rebase onto `ec059b3`: two conflicts, both resolved keeping both sides.
  - `RoleResearch.test.tsx`: slice D's "No longer there" test and this slice's Research again
    tests sit side by side (16 passed).
  - The register's DIV1-15 row: slice D's round 2 sentence, then this slice's Research again
    sentence.
- `make check` after the rebase and on the head: all green (ruff format and lint, mypy;
  backend 2166 passed, 123 skipped; fixture validator passed; generated client matches; Biome
  clean; `tsc` clean, e2e included; Vitest 46 files, 504 tests).
- Integration, under the lock in one guarded command each: `test_interview_turns.py` and
  `test_interview_choices.py`, 30 passed before the rebase (82.9 s) and 30 passed after it
  (84.8 s). Once the lock was held by another run; I waited and retried.
- Storybook, static build (`pnpm run build-storybook`, telemetry off; a build makes no update
  check), then Playwright against it with a throwaway config without the stack's set-up
  (removed after):
  - `e2e/storybook.spec.ts`: 5 of 5 passed (every story renders and passes axe at
    1440 × 900; the two answer-form layout tests; tabbing through a waiting card at 320, 390,
    768 and 1440 px).
  - A throwaway walk (removed after) of `you--reply-to-review`, `you--reply-changes-lists`,
    `you--reply-with-a-limit`, `you--paused` at 1280 × 800 and 390 × 844: no place to type, no
    Send, one bright action (Save, or Resume while paused), the Save bar in the first screen,
    and no em dash or spaced en dash in the page's words. `you--demo-question-with-examples`
    (a decided card): the reply field and Send are back.
- No web request, no live call ($0), no Docker started.

### Journey steps changed (written; the controller's acceptance runs them)

- `e2e/conversation.spec.ts`, "talk, review, undo, explore and sketch":
  - New at the card: no reply field and no Send; focus on "Accept current role" (Send had it).
  - After Save: focus in the reply field (was: the "Saved to What we know" heading focused; the
    heading is now checked as visible).
- `e2e/conversation.spec.ts`, the `keepAll` helper (used by "the demo takes a target…" and
  "exploring by example replies…"): after Save, focus in the reply field (was: the heading).
- `e2e/keyboard.spec.ts`, "the You chapter completes from the keyboard…":
  - At the card: focus is on "Accept current role" (was: focus put back on the page, then Tab).
  - After Save: focus in the reply field (was: the heading). Undo is then reached by Tab from
    the page's start (was: five Tabs from the heading).
- `e2e/visual.spec.ts`:
  - "you--saved": no reply field while the card waits; after Save the reply field is focused
    (was: the heading). The shot will show the focus ring on the reply field.
  - "you--reply-to-review": now checks there is no reply field. The shot will look different
    (no reply field under the card).
  - "you--support-note": comment only.

### The journey and its load (contract item 6)

Walked in Storybook at 1280 and 390 px, and in the tests:
1. A reply streaming: one place to type (the reply field), Send and Pause.
2. The card arrives: no place to type. The card's choices, then Save (the one bright action)
   and Keep none. Focus on the first choice. Lines: the reply, "To review: N changes", two
   per change, Save's short reason.
3. After Save or Keep none: "Saved to What we know" with Undo, then the next question, then
   the reply field with anything typed earlier, focused. One place to type, one next action.
4. Paused with a card waiting: Resume the one bright action; no reply field.
5. No em dash or spaced en dash in any of these views.

### Not run

- `make acceptance`: not run, the controller runs acceptance (the changed journeys above, the
  visual shots and the Storybook axe spec in its own run).
- The capped live check of `interview-turn-7`: the controller's (R5). The fix changes no
  prompt.
- Safari and VoiceOver: not run, requires human. In Safari a clicked button takes no focus,
  so after clicking Send focus is on the page and the card's arrival leaves it there (nothing
  lost, but nothing moved either).

### Concerns

1. The hand-off to the card relies on React letting go of the form's ref before the form
   leaves the page. The jsdom test shows it does (React 19.3); the e2e journeys check it in
   Chromium when acceptance runs.
2. Pre-existing, not changed: after a refused save with a support panel, dismissing the
   panel tries to focus the card's heading, which can't take focus, so focus falls to the
   page (`YouChapter.tsx`, the support panel's dismiss).

Generated or vendored paths to skip: none.

## Acceptance run 15: the failed journey step (main tree)

**What failed:** `e2e/conversation.spec.ts:100` waited for focus on "Accept current role" once the
card arrived, and it never came.

**Why: the step named the wrong button. Focus was not lost.**
- The code moves focus to the card's first choice: the first change's Accept or Confirm.
- In this journey the demo proposes the work areas first. Its card, read from run 15's trace:
  work areas, weekly study hours, current role, then tasks you enjoy. So the first choice is
  "Confirm work areas as a limit", not "Accept current role". I assumed the role came first.
- Three more checks agree:
  - In the same run, the keyboard journey passed with the same check. Its card has current
    role first, so "Accept current role" is right there.
  - I replayed the order with a mouse in real Chromium (a throwaway Storybook story and
    script, not committed): click Send, then the card arrives. The browser logged focus
    leaving Send and arriving on the card's first choice.
  - In Next's React, a form's ref is let go before the form leaves the page, so the check
    still sees focus in the reply field or on Send. Read in
    `next/dist/compiled/react-dom/cjs/react-dom-client.production.js`, where it deletes a
    page element.

**Change:** one journey step. It now finds the card's first choice, checks it is named
"Confirm work areas as a limit", and checks that it has focus. No app code changed.

**Not done, and why:** the dispatch asked for a "sent from the reply box" flag and a Vitest
test that fails first. No defect is there for that test to catch, so I added neither. A
flag would add code for a failure that does not happen. If you want the flag anyway as a
safety net (focus moves to the card only when it was on the page), say so and I will add it.

**Checks:**
- `pnpm exec playwright test e2e/conversation.spec.ts`, under the lock in one guarded
  command: 12 of 12 passed (1.1 min), including the corrected step. The run built and
  started its own test stack, as the spec's set-up does. The lock was released.
- `make check` in the main tree: all green (backend 2166 passed, 123 skipped; generated client
  matches; Biome clean; `tsc` clean, e2e included; Vitest 46 files, 504 tests).
- No live call ($0). No web request.
