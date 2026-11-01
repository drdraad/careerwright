# Task W2E fix round 1: re-review, app, truth and tests half

Reviewer: Claude (Opus 5.5), read-only. Fix commits c91687f..60c8516 (on 98fd0a9). I read the
fix diffs in my half in full: the demo interviewer and its tests, `Conversation.tsx`,
`ProfileEditor.tsx`, `YouChapter.tsx`, `WhatWeKnow.tsx`, `Directions.tsx`, `vocabulary.ts`,
the unit and browser tests, and the register. I skimmed the strip and CSS changes. No suites
re-run, no probes needed: the two probes from my first review are now tests.

### Verdicts

**A-I1, the demo's way on: ADDRESSED.**
- The fix: `fixture_interviewer.py:319-326`.
  - After the last question (nothing in front, nothing after), any message, Skip included,
    gets "Thank you. I have no more questions. Open Suggestions for work that could suit you,
    or What we know to change an answer." (`:100-103`). It names only tabs that are always on
    screen, and never sends the person back to Skip.
  - At the role question the reply names the two buttons instead of example replies
    (`:97-99`). It is used only when the question is the role question, which is only ever
    asked of someone who isn't sure. That is exactly when the web shows the two buttons
    (`conversation.ts:134-146`).
  - Under every other demo question the old words stay, and that question always has example
    replies.
- Every case where the "couldn't note" reply is used now names a control that is shown.
- Both probes are tests:
  - Backend, `test_interview_agent.py`: the role-question test ("Explore", "I'd like to
    explore", "yes") and the last-question test ("What next?", Skip, Skip twice).
  - Browser, `e2e/conversation.spec.ts` "the demo's way on names only what is in sight…": the
    two probes on the real stack, each reply checked against the buttons and tabs actually on
    screen.
- The same reply comes back for every message after the end. That isn't a loop: it points to
  two views that exist, not back to Skip. The implementer disclosed this (ruling 5).

**A-I2, an example reply keeps focus: ADDRESSED.**
- The fix: `Conversation.tsx:457-462`. The tap moves focus to the reply field before
  sending. The field stays mounted and is never disabled (`:498-506`).
- Test: `YouChapter.test.tsx` "keeps keyboard focus when an example reply is tapped" (red
  before the fix, green after). See M-N1 for a phone side effect.

**A-I3, "Name a role" opens once: ADDRESSED.**
- The fix: the request is now a yes/no flag that the form clears once it has applied it
  (`ProfileEditor.tsx:83-92`, through `onTargetsOpened`). The parent keeps a stable callback
  (`YouChapter.tsx:150-153`). A later opening of the form changes nothing.
- Test: `YouChapter.test.tsx` "opens target entry once for Name a role…" runs my sequence:
  Name a role, close the form, Edit answers directly. Target roles stays "unasked" with no box
  shown, and a later save goes through with `target_titles` unasked.

**A-M1, the connection's words: ADDRESSED.**
- "These are the skills ESCO lists for both roles…" is gone. "Careerwright hasn't compared
  them with your own experience yet." replaces it (`vocabulary.ts`
  `SUGGESTION_WORDS.notCompared`, `Directions.tsx:271-273`).
- The line that called ESCO's title "your role" is gone. The card quotes only the person's own
  words, through the API's reason.
- Test: `Directions.test.tsx` "states the join once on each card, and never calls ESCO's
  title the person's role". The person says "cycle courier", ESCO says "bicycle courier".

**The UI-09 register fix: ADDRESSED.**
- `docs/requirements-register.md` UI-09: the evidence for the route preview's V-03 and V-04
  is marked retired.
- V-03, V-04 and S0-V07 are handed to Task 14's open part in plain words.

### New breakage in my half
No Critical or Important.

#### Minor

**M-N1. On a phone, tapping an example reply will probably open the on-screen keyboard.**
- Where: `Conversation.tsx:459`.
- What: focusing a text field from a tap's handler is what makes phone browsers raise their
  keyboard. So after each one-tap reply the keyboard likely covers about half the screen,
  hiding the reply and the next question.
- Why it matters: one-tap replies exist so the person doesn't have to type. I can't confirm
  this without a real phone (the Safari check, H-04, needs a human).
- Fix: the fix list also allowed focusing "the message just sent". Focusing that message, or
  the next question's heading when it arrives (it already has `tabIndex={-1}`), keeps focus
  without a keyboard. If kept as is, add it to the H-04 checklist.

### The implementer's concerns, judged
- **The browser test reached only the first probe on the old code:** acceptable.
  - The second probe's RED is the backend test, which calls the same `fixture_turn` the app
    runs.
  - By reading, the browser assertion `not.toMatch(/Skip|example repl/i)` would have failed on
    the old reply, which contained both.
- **Five `ConnectionOut` fields the web no longer shows** (`role_title`, `sentence`,
  `shared_skill_count`, `shared_skills`, `still_uncertain`): leaving them is right for this
  round, because removing them changes the API contract and the generated client.
  - `sentence` and `still_uncertain` are API prose that plan v1.5 wants out of the API.
  - Task M lights the connection in the world and may want `shared_skills` and `role_title`.
  - So the final review, or Task M, should drop the two prose fields and keep the facts.
    Already ledgered as a final-review note; I agree.

### Out of scope (one line each)
- The skills line now leans on the reason above it ("Among them: …"). The API keeps at most
  three reasons per card (`exploration.py:686`). On a rare card whose join reason is cut by
  that cap, "Among them" has nothing to refer to.
- STATE-09's status still names the original candidate (`c64b636`). The verified candidate is
  now `ba0846e` (register tidiness, final review).
- The purpose line's "plan a route you can afford" promises what Routes and Plan, marked "not
  built yet", don't do in this build. The words are the controller's example, and session W2
  judges them.

### Assessment
**Fix round quality:** Approved (app half).

**Reasoning:** All three Important findings, A-M1 and the UI-09 record are fixed. Each fix has
a test that reads what the person sees and failed before the fix. The one new Minor (a phone
keyboard after an example tap) can't be confirmed here and needs a real-phone check.
