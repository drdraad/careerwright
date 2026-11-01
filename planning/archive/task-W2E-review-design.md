# Task W2E review: design and experience half

Reviewer: independent agent, read-only. Base ec4d060; commits 8410eff, 7c3a72b, c64b636, 4dcc2ca.
Read: the brief (task file, W2E card and rulings), the dispatch, the implementer's report, the
review package (my half's files in full: Conversation, YouChapter, Directions, SketchCard,
ProfileEditor, ChapterNav, ChapterView, WorkspaceStrip, WorkspaceShell, World, WorldControls,
Button, globals.css, vocabulary.ts, conversation.ts, the fixture interviewer, the e2e specs,
the design references' css/js/tool, ADR 0014's strip lines, `sprint-w.md`; the rest skimmed),
the audit's appendix E, both session records, and the images.

Captures: the app's `apps/web/test-results/visual-*/screenshots/` were written 11:17 to 11:18 on
2026-10-31, after c64b636 (11:03) and before 4dcc2ca (11:24, documents only), so they show the
final code. **Not stale.** The design references were written at 10:51, matching c64b636.
No suite re-run. No browser, no Docker, no live call.

## The product owner's own comments (R14), done or not done

Session 2 (`docs/reviews/session-2-answers.md`):

| Comment (their words, shortened) | This task touches it? | Status |
|---|---|---|
| Route screen: "psychobabble"; "don't understand 'conditional', or 'fixture' or … economic cost and direct cost"; "Confusion can make one indecisive and give up" | Yes | **Done** for the person's path: Routes shows its "not built yet" place in every workspace, the fixture's too (`routes--1440x900.png`). The words come back with real Routes (Task 14; the end-to-end session asks again). |
| Start page: "It's for inputing information about yourself and your job preferences, not sure" | Yes (the start screen changed) | **Not done.** The start now has one bright choice and the England line, but still doesn't say what Careerwright is for. Planned for Task 6d's first question and session W2's first question. Controller: check whether this comment has already been carried forward once; if so, R14 says ask the product owner. |
| Suggestions: "many feel like arbitrary matching on keywords" | Partly (each reason now names its skills) | Quality is the product owner's call at session W2 (R14). The named skills make each reason visible, but the card now says it twice (Important 2). |
| "I found the button, but it did not stand out enough. Needs to be a bright colour." | Yes | **Done.** "Make this a target" stays the one filled bright action (`you--slate--*`); once chosen it gives way to "Saved as one of your targets". |
| "Starts with How Nessa talks with you … above the fold … a mess … incoherent" | Yes (the start and the strip) | **Done** for what this task touches: the start's one bright action is the entry choice; the world's switches left the tablet strip. |
| "Chat should be immediate … too much on one page … jobs … on a separate tab … too much helper text that isn't actually helpful" | Yes (new lines added) | **Not done on the suggestion cards.** Each skill-joined card now states the same join twice in a row, and the connection card does too (Important 2). Elsewhere the new lines are needed (England line, example replies). |
| "total spending limit and monthly payment limit - what do these mean??" | No new words | Done earlier; unchanged. On a tablet the strip now cuts the budget mid-number (Important 1). |
| "Don't even know where to start" | Yes | **Done in the demo:** bright entry choice, one-tap example replies, two ways on at the role question, unbuilt chapters marked in the rail. |
| C1 "ditch the tone selection … minimum ideas per page" | Yes | Done earlier; kept in the account menu. |
| C3 "could be easier with colour coded buttons" | No | Done earlier; kept (leaf Confirm, orchid Undo in `you--saved--390x844.png`). |
| Phone scores skipped ("a waste of time until we've fixed this mess of a page") | — | Not scored. This task's phone work (slim band, first decisions) is ready for session W2 to judge, with Important 3 open. |

Session W1 (`docs/reviews/session-w1-answers.md`):

| Comment | Touches it? | Status |
|---|---|---|
| Horizon, livelier, solid trails not dashed | No | Unchanged; trails solid in every capture. |
| Sound "subtle and evocative, not cheesy", off until on | Yes (moved) | **Done:** still off by default; below 1180 px it is in the account menu with its words and switch. |
| "Keep Outfit" | Yes (phone headings 20 px) | **Done:** still Outfit. |

The product owner's direction of 2026-10-31 ("visuals … subservient to … a practical, useful
product"): **done** for the band (144 px below 968 px; none at 560 px tall or less). "Not limited
to a prefilled list of roles": Task 6d's; in the demo, a sure person still can't name their own
role in the conversation without the exact phrase (Minor 2).

### Spec Compliance

- ❌ Issues found:
  - On a tablet the strip "keeps" work area and budget, but cuts all three facts, a money value
    among them, while room is free beside them (`apps/web/src/app/globals.css:1809-1826`;
    `you--768x1024.png`, `you--role-or-explore--768x1024.png`). Important 1.
  - At 390 × 844, What we know's first action is below the first screen in the fixture workspace;
    the test runs only on a sparse workspace (`apps/web/e2e/conversation.spec.ts:474-478`;
    `you--what-we-know--390x844.png`). Important 3.
  - The suggestion card's reason repeats itself and one reused line breaks the sentence rule
    (`apps/web/src/components/Directions.tsx:261-299, 476-478`). Important 2.
- Met, checked against captures and code: the demo's example replies and the target phrase;
  "Show me suggestions" and "Name a role", committing nothing; the rail's "not built yet" marks
  (rail and phone menu); "Saved as one of your targets" with what the work usually asks for, no
  "Based on your earlier answers" (`you--target-chosen--*`); the entry choice as the start's bright
  action and Send bright only with text (`you--1440x900.png`, `you--390x844.png`); "Hold the
  world still" apart from "Pause the interview"; "Careerwright covers England for now." until the
  first answer; the budget words name no missing control; Routes not built yet in every workspace;
  the world placed again after a view change (at 768 and 390, "You" stands above the console and
  the key clears the tabs in What we know: `you--what-we-know--768x1024.png`, `--390x844.png`);
  the reply-to-review's first Confirm in the first phone screen (`you--reply-to-review--390x844.png`);
  ADR 0014 decision 7's strip wording matches what the app does.
- ⚠️ Cannot verify from the diff and captures:
  - You with three long targets in the 144 px band at 390: no capture, and no test asserts a target
    is named in You on a phone. On a phone the world is the only place outside What we know that
    names the target, so a band too small to place long names would hide it. One capture would settle it.
  - The account menu holding the world's switches below 1180 px, the sideways window (844 × 390)
    and "Name a role" landing in the form: tested, never captured.
  - A demo question with its example replies, and the connection card: Storybook stories only
    (axe-checked); no image anywhere.
  - The live bridge: no live run (Task 3b).

### Strengths

- The demo no longer loops on the paths the card names, and a person can always tap their way
  on. The two ways on at the role question read as one decision (`you--role-or-explore--*`).
- The chosen target is confirmed in place, focused, with ESCO's list under it. The confusing
  "out of date" reaction is gone (`you--target-chosen--1440x900.png`).
- The phone is much better: the band shrank from about 300 px to 144 px, and the key no longer
  covers a tab. N1 is fixed at its cause (the observer now watches `hidden` and `open`), and the
  new browser test reads live boxes after each change with `scrollY === 0`, so it can't pass on a
  stale value.
- The strip's stopped state keeps its reason whole on a phone (N2), and a short window drops the
  band (N3).
- The Sprint W review is honest where it matters: it calls itself an agent pre-review, says the
  ten-second bar is not met, and claims no human gate.

### Issues

#### Critical

None.

#### Important

1. **On a tablet the strip cuts the person's facts, a money value among them, with room to
   spare** (`apps/web/src/app/globals.css:1809-1826`; test `apps/web/e2e/world.spec.ts:452-467`).
   - At 768 in the fixture workspace the strip reads "Target Data quality…", "Work area" broken
     over two lines with "Manches…", and "Budget Up to £1,50…" (`you--768x1024.png`,
     `you--what-we-know--768x1024.png`).
   - In another workspace: "Work area Leeds", then a wide gap, then "Budget Not confir…"
     (`you--role-or-explore--768x1024.png`).
   - Cause: each fact gets an equal share (`flex: 1 1 0`), so short facts leave space unused while
     long ones are cut. The strip's second row also has empty room.
   - Why it matters: F14's point was "the person's facts come first". A budget cut inside its
     digits isn't shown in pounds, and an unconfirmed state cut to "Not confir…" is barely
     readable. The test asserts only that the labels exist.
   - Fix:
     - let each fact take its own width and shrink only when it must (`flex: 0 1 auto`), or let
       the facts wrap to the second row before anything is cut;
     - keep labels on one line;
     - never cut a money value inside its digits (for example, show the total only at this width
       and leave the monthly part to What we know);
     - extend the F14 test to assert at 768 that no fact's words are clipped (`scrollWidth <=
       clientWidth`), in the fixture workspace and in one with "Not confirmed".
2. **Each suggestion's reason now says the same thing twice, and a reused line breaks the
   sentence rule** (`apps/web/src/components/Directions.tsx:261-299, 476-478`;
   `apps/web/src/lib/vocabulary.ts:269-276`; the API's bullet from
   `backend/src/careerwright/profile/exploration.py:688-693`).
   - Skill-joined card: the bullet "…ESCO lists 9 of the same essential skills for both, so
     Careerwright joined them by those skills." is followed at once by "Careerwright joined them
     by these skills: …" (`you--slate--1440x900.png`, `--390x844.png`, `--768x1024.png`).
   - Connection card: it is always found by a role join with shared skills
     (`profile/slate.py:657-661`), so the same bullet is followed by "Careerwright joined this to
     your role, “…”, by N essential skills ESCO lists for both." That states the same fact twice.
   - The connection line quotes ESCO's title as "your role" (`role_title` is "the person's role
     as ESCO titles it", `exploration.py:321`), while the bullet above quotes the person's own
     words. Where they differ, the card gives the person's role two different names in a row.
   - The disclosure's "These are the skills ESCO lists for both roles." (the API's
     `still_uncertain`, newly shown) says what a list contains, which the sentence rule forbids.
   - Why it matters: the product owner's own session comment was "too much helper text … the
     cognitive load is too high", on this very screen. The brief's sentence rule says "say less",
     and R14 keeps sentence-rule findings in the task. Session W2 is the product owner's next
     look at these cards.
   - Fix:
     - one statement per reason: show the named skills as the bullet's continuation, without a
       second "Careerwright joined them by";
     - on the connection card keep the kicker and the skills, not a second sentence restating
       the join;
     - say the role in the person's words, or as ESCO's title, never ESCO's title as "your role";
     - write the uncertainty as what Careerwright did or hasn't checked;
     - add a `Directions.test.tsx` case asserting the join is stated once per card, on a plain
       card and on the connection card.
3. **At 390 × 844, What we know's first action is off the first screen in the fixture
   workspace** (`apps/web/src/components/WhatWeKnow.tsx:103-137`; test
   `apps/web/e2e/conversation.spec.ts:474-478`; claim in `docs/reviews/sprint-w.md:41, 143`).
   - In P01 (four answers, two of them explained limits) the view ends the first screen inside
     the eight-name "Not asked yet" list, and "Edit answers directly" is below it
     (`you--what-we-know--390x844.png`). Anyone who has finished the demo's questions has as many
     answers or more.
   - The first-screen test uses `talkedWorkspace` (three short answers), where it fits. The
     reference fits only because its "Not asked yet" is one short line
     (`docs/design/screenshots/you--known--390x844.png`).
   - Why it matters: the brief's acceptance names this view ("At 390 × 844 the first decision of
     the … What-we-know views is in the first screen"), and the Sprint W review says "(tested)".
     The effect on the person is medium: they scroll to edit.
   - Fix: put the view's action under its heading, before the answers (as the suggestion card
     puts its choice first), and run the first-screen check on the fixture workspace.

#### Minor

(These wait for the final review unless the controller folds them into the fix round; 1 and 2 are cheap.)

1. **The design check's sideways-scroll exemption** (`docs/design/tools/screenshots.mjs:164, 173`).
   - What it guarded, design review I1 (What we know's answers cut mid-word inside an
     `overflow: hidden` box), is still caught: `.known-facts` computes `overflow-x: hidden`, not
     auto. So the check is **not weaker for the case it guarded**.
   - But the exemption is wider than its one case. It applies to any ancestor whose computed
     `overflow-x` is auto or scroll, and CSS gives that to any vertical scroller too. A future
     scrolling sheet or drawer would silently drop the horizontal check for everything inside it.
   - It also passes the phone's emphasis row with "Broader" showing as a few-pixel sliver and
     "More depth" fully out of sight, with nothing telling the person the row scrolls
     (`you--target-chosen--390x844.png`; reference `you--suggestions--390x844.png`). These are
     view controls, never limits, so the effect is low.
   - Fix: exempt only an element marked as a sideways row, and require a visible cue (the next
     option showing by at least about 24 px, or a fade).
2. **The demo's "couldn't note" line can point at nothing**
   (`backend/src/careerwright/profile/fixture_interviewer.py:89, 306`;
   `apps/web/src/components/Conversation.tsx:436-455`).
   - At "Do you have a role in mind, or would you like to explore?", typing the natural answer
     ("explore", "yes") brings "Tap an example reply, or say Skip." But that question shows the
     two ways on, not example replies.
   - On the sure path, a person who types their own role ("data analyst") is offered only "I want
     to be a nurse" or Skip. This is the "ideal job not appearing" frustration from the product
     owner's direction, in the demo.
   - Fix: at a target question, name the way on that exists ("Name a role", shown on the sure
     path's repeat too). Don't add patterns (R11).
3. **The Sprint W review overstates two results and misses two defects** (`docs/reviews/sprint-w.md:41, 141-152`).
   - It says each phone view's first decision is in the first screen "(tested)", which Important 3
     disproves.
   - It says the tablet strip "keeps the person's facts". Its visual findings miss the cut strip
     and the doubled reason lines.
   - Correct these with the fix round.
4. **The design references drift from rules this task set** (they stay the reference until
   Storybook takes over, R13).
   - The start (`you--default--*`) still shows Send filled on an empty field and no England line.
     Task 6d builds its first question from this reference.
   - The reference strip never shows Budget, though the app now does at 768 and up.
   - The rail marks Roles to Plan "not built yet" while those places draw their future designs
     (report concern 4). One line in the gallery index would explain it.
5. **On Routes, the app draws a grey trail from You to the destination; the reference draws none**
   (`routes--1440x900.png` against `routes--not-built--1440x900.png`). The card says no route has
   been worked out. The key explains grey trails as "not known yet", but the line can still read as
   a route. This predates the task; it belongs on Task M's list.
6. **The rail's line runs through the "not built yet" words** (every app capture's rail). This is
   already recorded in the Sprint W review for Task M's list. It is polish, not a contrast failure.
7. **The route preview's layout contracts left with it** (`apps/web/e2e/layout.spec.ts`). That is
   right while Routes isn't built. The lessons should go on Task 14's card so real Routes earns
   them again: V-03 (first route card in a phone's first screen, three on a tablet), V-04 (the
   sheet's peek content) and S0-V07 (a focused card never under the sheet).
8. **Evidence for session W2's package (Task 6e).** Add captures of: a demo question with its
   example replies; the connection card; "Name a role" landing in the form; and You with three
   long targets at 390 (the cannot-verify item above).
9. **The budget-reached note still offers "Try again"** (predates the task; `you--slate-note-retry--390x844.png`).
   The retry meets the same limit until the month turns, and the app has no control to raise it.
   This is F10's spirit, for Task 3b.

### The implementer's concerns, judged

- **Python one-token edit:** a process slip, disclosed, with no effect on what the person sees.
  Whether to accept it is the app half's call.
- **Ten-second bar not met:** accepted. Plan v1.5 moved it to Task 6d and Sprint M, and the
  Sprint W review records "not yet, honestly" without claiming it.
- **The rare demo case** (Skip after Keep none answers an earlier question): it is rare, and it
  shows before anything is saved, because the tray names the field. Acceptable as a recorded
  limit.
- **N1's browser test not run on the old build:** acceptable. The unit test shows the
  mechanism failing on the old code, the re-review's captures are the "before", and the new test
  reads live boxes with no scroll. The 768 and 390 What we know captures confirm the fix.
- **Sideways rows treated as not clipping:** not weaker for what it guarded (I1). It is wider than
  its case and hides a phone row's last options (Minor 1).
- **Route preview layout tests removed:** right now; carry them to Task 14 (Minor 7).

Questions for session W2, not findings: are the entry choices and the two ways on, edged and
lettered in sea-glass rather than filled, "a bright colour" enough? Does "An unexpected
connection" earn its name before Task 6d settles the product owner's "no revelation rests on
ESCO's essential skills alone" (ADR 0007 allows it until then)?

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The card's items are built and most work as the person needs: the demo moves on,
the chosen target is confirmed, the phone is far better, and N1 is fixed at its cause. Three
fixes are left, all small web changes:
- the tablet strip cuts the person's facts, a money value among them;
- each suggestion's reason says the same thing twice, against the product owner's own "too much
  helper text";
- What we know's action is off a phone's first screen in the product owner's own demo workspace,
  while the test and the review say it's in.
