# Task W2C part 1, fix round 1: re-review

Reviewer: Claude (Opus 5.5), read-only. Fix range 6af1097..f179d0f (d3a9164, c798ea4, ec5ec8e,
f179d0f). Code read as committed with `git show f179d0f:<path>`.

How I checked:
- I read the contract (new calibration), the fix list, both original reviews and the report's
  "Fix round 1" section. Then I read the 4,600-line diff in passes: e2e, components, lib, then
  backend, ADRs and design.
- Outside the diff, I checked one named risk each:
  - how the world notices a change of view (`World.tsx`);
  - when it writes `data-shown` (`World.tsx`);
  - how the world test and the visual test reach a view (`world.spec.ts`, `visual.spec.ts`);
  - the phone strip's stopped state (`WorkspaceStrip.tsx`);
  - "version" left in the chapter's words (`vocabulary.ts`, `ReviewTray.tsx`);
  - the generated contract (`openapi.json`).
- I looked at the app's captures from acceptance run 2. They were written at 08:07, and
  f179d0f was committed at 08:12 with that run's tree. I also looked at the recaptured
  references.
- I ran no suite. `cmp` shows the token mirror is byte-identical.

## Verdicts

| Finding | Verdict | Evidence |
|---|---|---|
| D-I1, the `.facts` collision | ADDRESSED | Renamed `.known-facts` (`docs/design/compositions/world.css:831`, `world.js:653`); Routes and Plan use the old `.facts` (`world.css:980`) again. `you--known` ×3 and `plan--default--1440x900.png` are whole again. A clipped-text check reads every text in a panel: clipped itself, or past the edge of a box that clips it (`docs/design/tools/screenshots.mjs:153-174`). It feeds `labels`, which fails the capture. |
| D-I2, the world on a tablet and a phone (ruling: the light visible in every view, app and references, with a test) | PARTLY ADDRESSED | **References: done.** Band rule `world.css:1071`; check `screenshots.mjs:188-197`; 7 names placed in every You view at 768 and 390 (`checks.md`). **App:** the band itself is there (`globals.css:1683-1691`), the phone title is hidden (`:1698`), and the test measures the band from the page (`e2e/world.spec.ts:379-403`). But once the person changes view, the world isn't placed again, so the light ends up under the console in What we know at 768 and 390 (`you--what-we-know--768x1024.png`, `--390x844.png`). The test's "You is named" check can't see this: see N1. |
| D-I3, the suggestions view (ruling: notes in one disclosure, actions up the card, real-slate reference) | ADDRESSED | `SearchNotes` holds every fewer, note, salary-floor, AI-filter, unmatched-title and familiarity line, each with its words (`Directions.tsx:381`, `:602`). The actions come straight after the title and kind of work (`:307`). The reference is redrawn from the "data analyst" slate, with examples labelled (`world.js:701`; `you--suggestions--1440x900.png`, choice at y≈716). The app wasn't captured at the top of the page. From the captures' offsets I estimate its choice at y≈820 of 900 with no notice above the cards. Test: `Directions.test.tsx:405`. |
| D-I4, one decision at a time | ADDRESSED | The question waits while `primary === "review"` (`Conversation.tsx:380`). It follows the save notice (`YouChapter.test.tsx:557`; `e2e/conversation.spec.ts:88`, `:101`). The reference agrees (`world.js` review state). The app capture `you--reply-to-review--1440x900.png` shows no question. |
| D-I5, helper text (ruling: list each line cut or kept) | ADDRESSED | Every line is listed with why (report, D-I5 table). The cuts are in the code: the entry glosses (`vocabulary.ts:207`), the hint said once (`Conversation.tsx:387`), "needs your confirmation" (`ReviewTray.tsx:45`), "Skipped changes…" and "Saving creates profile version…" removed, and the shortened suggestions line (`Directions.tsx:729`). Session W2 judges the result. |
| A-I1, nothing typed is lost (ruling: views stay mounted, tested mid-task) | ADDRESSED | All three panels stay mounted and `hidden` (`YouChapter.tsx:250`), and every tab controls its panel (`:98`). The test covers a typed reply, a tray choice, form edits and "Not for me" across views, and checks that nothing was sent (`YouChapter.test.tsx:488`). Side effect on the world: N1. |
| A-M2, a refused note request sent again on remount (ruling: "asked" kept outside the component) | ADDRESSED | Requests are kept per discovery in the query client, never collected (`queries.ts:246`, `:424-468`). `askOnce` reads the cache at the moment of asking. A network failure still shows "service isn't reachable" with a Try again (`Directions.tsx:415-434`), so nothing is masked. Tests: `Directions.test.tsx:471`, `:504`. |
| A-I2, focus after "Add the details yourself" | ADDRESSED | Focus goes to "Edit your answers" (`YouChapter.tsx:225`, `:337`; `ProfileEditor.tsx:156`). Tests: `YouChapter.test.tsx:539`, `e2e/conversation.spec.ts:308`. |
| A-I3, three API descriptions | ADDRESSED | `catalogue_schemas.py:311`, `discovery_schemas.py:577`, `origin_schemas.py:62`; regenerated (`openapi.json:12510`, `:13522`, `:16757`). |
| The sketch's `not_found` words | ADDRESSED | "Careerwright couldn't match it in ESCO" (`vocabulary.ts:444`). The test forbids "Not found in ESCO" (`SketchCard.test.tsx:79-85`). |
| D-M1, a chosen Accept is not a second bright fill | ADDRESSED | Chosen is a faint leaf tint with an edge (`globals.css:655`). The pairing is measured at 8.61:1 (`contrast-pairs.json`, `contrast-report.md`). Both checks count bright fills by computed colour (`screenshots.mjs:206`; `e2e/helpers.ts` `brightFills`, asserted at `conversation.spec.ts:94`, `:142`). |
| D-M2, no teal edge on a chosen proposal | ADDRESSED | `data-chosen` is gone from the app (`ReviewTray.tsx:191`) and from the reference. |
| D-M4, the tone setting | ADDRESSED | Shows "Keep this practical (the default)", says "Saved.", under "Preferences for this workspace" (`ConversationTone.tsx:15`, `:28`, `:49`, `:54`). Calm mode sits above that heading because it belongs to this browser, not the workspace (disclosed). |
| D-M5, no "version" on screen | PARTLY ADDRESSED (Minor, waits for the final review) | Every line the review named is fixed, and the form's notices too (`ProfileEditor.tsx:159`, `:168`, `:205`; `Directions.tsx:735`; `Conversation.tsx:347`). One shared error line is left: "Review the latest version, then save again." (`vocabulary.ts:527`). It shows in the chapter when a tray save is refused as stale (`ReviewTray.tsx:260-264`). |
| D-M6, the early sketch | ADDRESSED | Behind "The early sketch for your target" in What we know (`YouChapter.tsx:342`). |
| A-M1, the phone strip on one row | ADDRESSED | The state's words end in an ellipsis (`globals.css:1710-1723`). V-08 now runs at 390 (`conversation.spec.ts:187`). The capture `you--unavailable--390x844.png` shows one row, "Updates: Recon…". For the stopped state, see N2. |
| A-M3, the open suggestion's header | ADDRESSED | `aria-disabled` while open, and clicking it does nothing (`Directions.tsx:297`; `Directions.test.tsx:410`, `:418`). |
| A-M4, coverage behind claims | ADDRESSED | The tray's limit meaning is asserted (`YouChapter.test.tsx:427`). There is a keyboard journey to a target (`keyboard.spec.ts:126`). The moving/still claim is narrowed in the report's requirement candidates. |
| A-M5, a hyphenated name's exactness | ADDRESSED | `taxonomy_store.py:247`; ADR 0007 decision 13 rule 1 (`:596-603`). |
| A-M7, Resume while paused | ADDRESSED | Resume is the view's primary and Send the secondary; focus goes to "Paused", then back to the question (`YouChapter.tsx:214`; `Conversation.tsx:356`, `:365`; `YouChapter.test.tsx:590`). |

Counts: 18 ADDRESSED, 2 PARTLY ADDRESSED, 0 NOT ADDRESSED.

The implementer's own rulings are accepted:
- the note is asked for once Suggestions is open;
- Resume outranks a waiting tray's Save;
- D-M5 covers the form;
- the card's details stay visible after the actions;
- the band is `max(300px, 34vh)` (N3 covers a short window);
- the menu's `max-height` (disclosed, outside the findings).

## New breakage

### Critical

None.

### Important

**N1. On a tablet or phone, changing view leaves the world where it was: the person's light
goes under the console, and the key lands over the console or the tabs.**

- **Cause:** a change of view now only toggles the panels' `hidden` attribute
  (`YouChapter.tsx:250`). The world places itself again only on child or text changes, a
  scroll or a font load. It doesn't watch attributes (`World.tsx:682-683`). Before this round,
  a change of view mounted new views, which counted as a child change, so the world followed.
- **What a person sees:**
  - On a tablet or phone, the console's top depends on the view. A short view sits low; a long
    one starts at the band.
  - Open the chapter (Conversation, short), then choose What we know (long). The world keeps
    Conversation's layout until the person scrolls.
  - At 768, the light glows through the console about 55 px under its top edge. "You" can't
    be seen, and the "What the lights mean" button overlaps the console's right edge
    (`you--what-we-know--768x1024.png`).
  - At 390, the light is half under the console's edge, and the same button covers the
    Suggestions tab (`you--what-we-know--390x844.png`). In both captures the light and the
    key sit at the same height as in the Conversation captures (`you--768x1024.png`,
    `you--390x844.png`).
  - So the app fails D-I2's ruling: "the person's light is visible in every view".
- **Why the tests pass:**
  - The new world test (`e2e/world.spec.ts:379-403`) counts "You" as named when its label
    has `data-shown='true'`. Only a placement writes that attribute (`World.tsx:359`), so the
    value left from Conversation passes. Its `scrollTo(0, 0)` doesn't move a page that is
    already at the top, so it fires no scroll event either.
  - The reference check can't see this: each reference state is drawn fresh, with no change
    of view.
- **Audit overlap:** the audit lists the button over the Suggestions tab (appendix E, F8) for
  a follow-on task. This is its cause. Moving the button alone would leave the light hidden.
- **Fix:**
  1. Let the world's observer also watch `hidden` (`attributes: true, attributeFilter:
     ["hidden"]`), or ask for a new placement when the view changes.
  2. In the world test, change view without scrolling. Then compare the "You" label's box with
     the console's top, and the key's box with the tabs, rather than reading `data-shown`.

### Minor (wait for the final review)

**N2. On a phone, the strip's ellipsis also cuts the stopped state's reason.**
- Where: `globals.css:1710-1723` applies to every state that isn't live (`WorkspaceStrip.tsx`
  `LiveUpdates`).
- What it does: "Updates: Stopped: access to this workspace ended" or "…: sign in again"
  shows as "Updates: Sto…". With the Reconnect button beside it, almost no words are left.
- Fix: only connecting and reconnecting need to stay on one row. Let a stopped state take its
  own row, as a failed refresh already does (`.strip-refresh-failed`).

**N3. The band has a 300 px floor whatever the window's height.**
- Where: `globals.css:1683-1691`.
- What it does: in a window under 968 px wide and about 420 px tall, such as a phone turned
  sideways (844 × 390), the console starts below the first screen, so the start view shows
  only the world.
- This is the same band as the audit's F7. Fold it into that follow-on: cap the band by height,
  or fall back to the backdrop when the height can't hold both.

## Out-of-scope observations

- The type-ahead's `partial` description still says what ESCO lists ("ESCO lists no title with
  every word typed", `catalogue_schemas.py:201`). It's developer docs only, under the same rule
  as A-I3.
- "Help me explore instead" still drops focus when its view changes underneath it. This is
  older than W2C and appears as report concern 3.
- Each of the two save notices has its own Undo request. While one Undo is in flight, the other
  view's Undo stays enabled. The expected version refuses a second undo, so nothing is lost.

## Assessment

**Needs fixes:** N1 only. It is one observer option plus a test that measures boxes. If the
controller prefers, it can travel with the audit's F8 follow-on, as long as that task fixes the
cause and not just the button.

Everything else in the fix list is addressed, or partly addressed at Minor level (D-M5's
leftover line), and no human-only gate is claimed as passed.
