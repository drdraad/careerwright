# Task W2E fix round 1: scoped re-review, design and experience half

Reviewer: independent agent, read-only. Fix commits c91687f..60c8516 (on 98fd0a9). I read:
- the fix list and the "Fix round 1" section of the report;
- the whole fix diff (`review-98fd0a9..60c8516.diff`);
- the new captures.

No suite re-run. No browser, no Docker, no live call.

Captures: `apps/web/test-results/visual-*/screenshots/` were written 13:03 to 13:04 on
2026-10-31, after ba0846e (12:35, the last code commit) and before 60c8516 (13:10, documents
only). **They show the final code; not stale.** The report says it read run 1's captures; the
ones on disk are run 2's.

## Verdicts

| Finding | Verdict | Evidence |
|---|---|---|
| **D-I1** the tablet strip cut all three facts | **ADDRESSED** | See D-I1 below. |
| **D-I2** the join said twice; ESCO's title as "your role"; the list-contents line; helper lines | **ADDRESSED** | See D-I2 below. |
| **D-I3** "Edit answers directly" off a phone's first screen; `sprint-w.md` "tested" | **ADDRESSED** | See D-I3 below. |
| **The product owner's start-page comment** ("not sure" what it's for) | **ADDRESSED** (the words are for session W2) | See the start-page comment below. |

**D-I1, the tablet strip:**
- Each fact now takes its own width and wraps whole; nothing is cut (`apps/web/src/app/globals.css:1824-1833`).
- `you--768x1024.png` and `you--what-we-know--768x1024.png`: "Target Data quality analyst",
  "Work area Manchester", then "Budget Up to £1,500, at most £1,500 a month", all whole.
- `you--role-or-explore--768x1024.png`: "Budget Not confirmed" whole, on one row.
- The test now reads each fact's words, checks each label sits on one line and each value is
  not cut, at 768, in the fixture workspace and with three long targets
  (`apps/web/e2e/world.spec.ts:456-518`).

**D-I2, the join said once:**
- `you--slate--1440x900.png` and `--390x844.png` show the API's reason once, then "Among them:
  create a work atmosphere …, give instructions to staff and manage dispatch software
  systems.", then "The other 6 skills".
- The connection line is gone, so ESCO's title is never called "your role". The list-contents
  line is replaced by "Careerwright hasn't compared them with your own experience yet."
  (`apps/web/src/components/Directions.tsx` `JoinedBy`; `apps/web/src/lib/vocabulary.ts:275-281`).
- The test counts "joined" once per card, on a plain card and on the connection card, and checks
  that the card quotes the person's "cycle courier", never ESCO's "bicycle courier", and never
  says "your role" (`Directions.test.tsx`).
- Every helper line on the card is listed as cut or kept in the report. The two "…is below"
  lines are cut.

**D-I3, What we know's action on a phone:**
- `you--what-we-know--390x844.png` (the fixture workspace, four answers, two of them explained
  limits): "Edit answers directly" sits under the heading at y≈415.
- `apps/web/src/components/WhatWeKnow.tsx:108-120` (the button, then the form, then the answers).
- The first-screen test now checks What we know in the fixture workspace
  (`apps/web/e2e/conversation.spec.ts:566-570`).
- The reference shows the same order (`docs/design/screenshots/you--known--*`).
- `docs/reviews/sprint-w.md:149-158` corrects the "(tested)" claim and names what the first
  candidate missed.

**The start-page comment:**
- One sentence before the entry choice, start only
  (`apps/web/src/components/Conversation.tsx:186`; `vocabulary.ts:266`).
- `you--390x844.png` and `you--768x1024.png`: the line sits above "How would you like to
  start?", and the two choices are still in the first screen at 390.

## The implementer's two layout changes, judged

- **The fixture workspace's tablet strip is three rows instead of two** (`you--768x1024.png`):
  - The rows are the label, target and work area; then the budget; then the saved state and menu.
  - It is about 20 px taller.
  - **Acceptable.** The person's facts are whole, which was F14's point. At 768 the light still
    stands above the console, the key is clear of the tabs, and the start's choice and What we
    know's action stay in the first screen.
  - Polish for the final-review list: the budget's row has room for the saved state and the
    menu, so the strip could stay two rows (the states row takes the full width today).
- **The console's "You" title hidden in a window too short for a band**
  (`globals.css:1724`, ≤ 967 px wide and ≤ 560 px tall):
  - **Acceptable.** Above 760 px the rail still names the current chapter "You", and assistive
    tech still reads the heading.
  - It keeps a sideways phone's entry choice in its first screen under the purpose line (the N3
    test).
  - It applies only to the You chapter.

## New breakage in my half

No Critical or Important.

Minor, waiting for the final review:
1. **Tapping an example reply now focuses the reply field** (`Conversation.tsx:460`).
   - On a desktop and for assistive tech this is right.
   - On a phone, focusing a text field inside a tap usually raises the on-screen keyboard. So each
     one-tap reply could bring up the keyboard over the review tray that follows. That works
     against the one-tap idea.
   - I can't verify it here: real-Safari checks are human-only.
   - The fix list also allowed moving focus to the message just sent, which would avoid the
     keyboard. Check at the Safari check (H-04), or switch.
   - The same focus pattern already existed at `Conversation.tsx:481`.
2. **"Among them:" follows the reason list as a loose line.** On a card where the shared-skills
   reason is not the last one (`explain()` can add a skill-search reason after it), "them" no
   longer points at the skills. This is rare; a wording edge.

## Out-of-scope notes (one line each)

- The purpose line's "plan a route you can afford" uses "afford", which the planning rules avoid
  ("not feasible in this monthly model", never "cannot afford"), and Routes and Plan aren't built
  yet. These are the controller's suggested words; session W2 judges them.
- "Tap Show me suggestions or Name a role." names the buttons without marking them out
  (quotation marks or bold); session W2 judges the wording.
- On a card joined by both the role and a target, the skills listed are the suggestion's
  combined set, so "The other N skills" may not add up to either reason's count. This is the app
  half's truth question.
- With three long targets at 768 the strip wraps the target value by words, which could make it
  several rows tall. It is tested whole, but there is no capture and no first-screen check at
  that size.
- My earlier Minors stay as ledgered, among them the sure path's way on in the demo and the
  references' start.

## Assessment

**Fix round quality:** Approved (design half)

**Reasoning:** All three Important findings and the product owner's start-page comment are fixed.
The captures and the tests read what the person sees. The two layout trade-offs the implementer
raised are reasonable. Two new Minors wait for the final review.
