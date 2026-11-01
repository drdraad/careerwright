# Task 6d slice B, fix round 1: scoped re-review, design half (`design`)

Commits 81c3695..667426e (2e05426 to 667426e; Task 13b's integration and the CLAUDE.md line
before 81c3695 are not this slice's). I read the fix list and its rulings, the implementer's
"Fix round 1" section (as unverified claims), then the package. I read these in full at
667426e: `FirstQuestion.tsx`, `SupportNote.tsx` and `Conversation.tsx`'s `Start`. I also read
the web hunks of `Directions.tsx`, `vocabulary.ts`, `queries.ts`, the stories, every changed
test and e2e file, and the backend hunks that decide what the web shows:
- `routes_taxonomy.py` and `routes_origin.py`;
- `catalogue_schemas.py` and `interview_schemas.py`;
- `safety.py`;
- `exploration.py`'s `name_role`, `closest_offer` and `compute_slate`.

I looked at the four new 390 × 844 captures. Line numbers are at 667426e.

Focused checks outside the diff, one per named risk:
- **A typed risk phrase could reach a log through the type-ahead's URL.** The API's access log
  writes the path only (`api/guard.py:130`), and uvicorn's own is off (`logs.py:86`). No issue.
- **The title panel could sit somewhere the person can't see it.** The message panel renders
  above the reply field (`Conversation.tsx:567-575`), and its announcement says so
  (`YouChapter.test.tsx:1369`). The title panel renders below the title field
  (`FirstQuestion.tsx:269-277`). See R-I1.

No suite or browser was run.

### Spec Compliance
- **D-I1, Enter saves ESCO's first guess: addressed.**
  - No option is active until the person moves to one (`FirstQuestion.tsx:101-103`, `:212`).
    Enter with none active keeps the typed words without recording a refusal (`:169-174`).
  - The hook keeps no earlier list (`queries.ts`, `placeholderData` removed), and the field
    takes only the answer for the very words typed (`:111-112`).
  - Two tests cover it: "keeps the typed words on Enter…" and "never lets an earlier search's
    titles stand…". A narrow remnant remains (R-M1).
- **D-I2, "None of these is my job" in the type-ahead not recorded: addressed.**
  - The partial list's own-words option sends `none_of_these` (`FirstQuestion.tsx:155-159`).
    `name_role` records the refusal through the one write path.
  - The slate gives the role `title_kept_as_own` after a refusal, otherwise `role_not_matched`
    (`exploration.py:916-923`). Its words ask for no other job (`vocabulary.ts:720-721`).
  - Acceptance 3 now holds in the start and in Suggestions.
- **D-I3, the title field skips the support screen: addressed as ruled.**
  - The type-ahead screens what is typed (`routes_taxonomy.py:73`). `name_role` refuses a
    screened title (`exploration.py:1457`), and every refusal of it carries the panel
    (`routes_origin.py:132`).
  - The web offers nothing in those words and never repeats them (`FirstQuestion.tsx:121-123`).
    It shows the unchanged panel, which stills the world (`SupportNote.tsx`, moved as is).
  - The person can dismiss it, type again or skip. Nothing is stored (the report's tests; not
    re-run).
  - Placement and the panel's life are new findings (R-I1, R-M2).
- **The new line `SUPPORT_NOTE_TITLE`** (`safety.py:321-324`, `support-policy-8`):
  - **Tone:** consistent with the existing panel. It reuses the accepted first sentence with
    "typed" for "mentioned". It doesn't diagnose, name the matched words or repeat them.
  - **Sentence rule:** its second sentence says what Careerwright did ("hasn't kept it as your
    role").
  - **`CLAUDE.md`'s support invariant:** met as the ruling shapes it. A listed word shows the
    calm panel with the UK services beside the conversation, and nothing is stored or used for
    suitability.
  - **Honesty:** `REVIEW_STATUS` and the register say this use and its line are "not yet
    reviewed as built", so no human gate is claimed.
  - One gap is a question for the product owner (R-M3).
- **Item 9, D-M1 (WCAG 4.1.3): addressed.** The combobox is described by the partial question
  (`FirstQuestion.tsx:205`). One polite status region holds the partial question, none found,
  looking, the count and "Support information is shown below." (`:220-234`). Tested.
- **Item 10, D-M2: addressed.** "Something different" follows the API's `familiarity_known`
  (`Directions.tsx:693`; `exploration.py:943`). The "doesn't know your current work" line
  shows only when no title is given (`Directions.tsx:739`). Tested both ways.
- **Item 11, D-M3: addressed.**
  - Stories cover the type-ahead open (UK title, partial, none found).
  - Twelve captures cover the type-ahead and the closest step at all three sizes.
  - The phone e2e now checks the closest step's "None of these is my job", its first
    occupation, the kept-words line and "Help me explore" in the first screen
    (`e2e/conversation.spec.ts`).
  - The new partial capture shows a decision below the first screen (R-I2).
- **Item 12, D-M4 part 1: addressed.** "Change my job title" goes back to the first question
  with the title in the field (`FirstQuestion.tsx:378-382`; `Conversation.tsx:206`, `:219`,
  `:239-244`, `:261-264`). The same title returns to its closest question. Tested.
- **Item 13, D-M5 parts 1-2: addressed.**
  - Group headings use the name only, or "A group ESCO doesn't name"
    (`vocabulary.ts:894`), and a test checks no code shows.
  - No closest question is asked when no group holds an ESCO occupation
    (`exploration.py:1528-1530`). The start then shows the ONS kept-words line, which is true.
- **Item 14, D-M6: addressed.** `statesNoSkills` checks the origin the page reads (no
  occupation, usual skills or destinations) and can fail. It is an API check inside the browser
  test, which is acceptable here.
- **Item 15, D-M8: addressed.** Only the chosen answer says "Saving…", and one answer is sent at
  a time (`FirstQuestion.tsx:353-366`). A failed save clears `leaving`
  (`Conversation.tsx:228`; `FirstQuestion.tsx:132-135`). Tested, including N-M6.
- **Carried by the controller, not re-judged:** D-M4 part 2, D-M5's colour, D-M7 and D-M9.
- ⚠️ **Cannot verify from diff:**
  - A real phone's keyboard over the field's lines and the panel; VoiceOver; Safari. Not run,
    requires human.
  - The words, including the new panel line, judged at session W2 or by the product owner's
    review of the policy. Not run, requires human.
  - `make check` and `make acceptance` (the implementer's runs).

### Strengths
- The Enter fix is the fail-safe one. With nothing chosen, Enter keeps exactly what was typed,
  and the server still decides the title's kind.
- The support screen runs at all three doors: the type-ahead, the save, and every refusal of a
  screened save, a stale version included. The panel is the same component, still says nothing
  diagnostic, and never repeats the person's words.
- A slate line now waits for the API's own fact instead of a proxy: `familiarity_known`
  replaces "the role is provided".
- The closest step is calmer. Plain group names, one "Saving…", a way back, and no question
  with nothing to pick.

### Issues
#### Critical
None.

#### Important
**R-I1. On a phone, the title field's support panel likely sits under the keyboard**
(`FirstQuestion.tsx:269-277`; compare `Conversation.tsx:567-575`). New in this round's code.
- **What happens.** The panel renders below the title field, after the status line and the
  empty list. The message panel deliberately sits above the reply field, and its announcement
  says "above the reply field".
- **Why it matters.** While the person types on a phone, the keyboard covers the screen below
  the field. The panel appears exactly where the keyboard is. Nothing is offered, Enter does
  nothing (`:174`), and a sighted person in distress may see no response at all until they
  close the keyboard. The support panel is a high-effect item. The real-phone check is human
  (R2), but the risk follows from the layout.
- **Fix.** Show the panel above the title field, as the message panel sits above the reply
  field, and update `FIRST_ANSWER.supportShown` to match. Or bring it into view when it
  appears without moving focus. Add a phone e2e that the panel's heading is in view while the
  field has focus.

**R-I2. On a phone, a partial list's "None of these is my job" is below the first screen**
(`docs/reviews/sprint-2/screenshots/you--type-ahead-partial--390x844.png`; `FirstQuestion.tsx`
`OPTIONS_SHOWN = 8`, own-words option last). Present since slice B, shown by this round's new
capture.
- **What happens.** At 390 × 844, with no keyboard, the first screen shows "Is it one of
  these?" and five ESCO guesses. "None of these is my job / Use my own words" is out of sight.
  The UK-title capture shows the same for "Use my own words" and "Skip for now". This is
  beyond the keyboard case the controller kept as a human check.
- **Why it matters.** It pushes the person's own answer off the first screen. They may tap a
  guess that isn't their job, the same harm as D-I1 through a different door.
- **Fix.** In a partial list, put "None of these is my job" first, right under the question,
  or show fewer options on a narrow screen. Extend the UI-12 phone test to the partial list.

#### Minor
- **R-M1. An arrowed option can change under the person** (`FirstQuestion.tsx:125`,
  `:167-168`). The active option is an index. If the person presses Down while only "Use my own
  words" shows (still looking), then the titles arrive, index 0 becomes ESCO's first title, and
  Enter picks it. The window is short. Keep the active option by its key, or reset it when the
  list changes.
- **R-M2. Skipping or answering takes the panel away undismissed.** The title panel lives
  inside `FirstQuestion`. "Skip for now", or saving a different title, unmounts it and the
  world un-stills. The message panel stays until dismissed. Consider holding it where the
  message panel is held.
- **R-M3. A question for the product owner, with the line's review.** For an accepted false
  positive (a real job title holding a listed word), the panel says the title wasn't kept but
  names no way forward. The list is empty and Enter does nothing. The report's answer is "skip
  and name it in What we know". Whether the panel should say the person can skip this question
  is a policy-words question (the line is "not yet reviewed as built"). I propose no wording.
- **R-M4. "Skip for now" means something else while fixing a title** (`Conversation.tsx:241-244`).
  After "Change my job title", the button returns to "Which of these is closest?". It doesn't
  skip anything. The label could say so ("Back", or the question's name). Words for session
  W2.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** Every design finding from the first review is addressed, and the support line
fits the existing panel's tone and the invariant. Two phone-layout risks remain. The new
support panel likely appears under the keyboard (R-I1). The partial list's "None of these is my
job" sits below the first screen (R-I2). Both are small, local fixes.
