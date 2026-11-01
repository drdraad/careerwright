# Task 6d slice B review: design and the person's experience (`design`)

Commits f7f0e4d..21a397d (dff9c2e, 2317e19, 21a397d). I read in passes: the reviewer contract,
the Task 6d card and its rulings, the slice B dispatch, the implementer's report, then the
diff. Read in full at 21a397d: `FirstQuestion.tsx`, `Conversation.tsx` (the new `Start`), the
`Directions.tsx`, `SketchCard.tsx`, `vocabulary.ts`, `queries.ts` and `globals.css` hunks, the
stories, `FirstQuestion.test.tsx`, the `YouChapter.test.tsx`, `Directions.test.tsx` and
`discoveryWords.test.ts` hunks, every e2e change, and the three You captures. I read the backend
only where it decides what the web shows: the origin schemas, `name_role`, `choose_role`,
`closest_offer`, `choose_closest`, `first_slate`, the slate's fewer reasons,
`titles.current_role` and `match_titles`. All line numbers are at 21a397d.

Focused checks outside the diff, one per named risk:
- **The start could hang on "Looking at your answer"** if the origin's role text differed from
  the profile's. `titles.current_role` returns the field's own value (`titles.py:47-61`), so
  `Conversation.tsx:244` matches. No issue.
- **A slate line could ask for another job after "None of these is my job".** `declined` is
  read only from a `none_of_these` record (`titles.py:57`), and only `choose_closest` writes
  one. The type-ahead's "None of these is my job" calls `name_role`. See I-2.
- **The first question could bypass the support screen.** `has_risk_stem` runs only on
  interview messages (`routes_interview.py:75`). See I-3.
- **The slate's familiarity heading for a role kept unplaced.** `Directions.tsx:688` is
  unchanged. See M-2.
- **The world's skills.** `lib/world/model.ts:54` always draws `skills: []`. See M-6.

No suite was re-run. No browser, Storybook or test was started.

The product owner's comments on this screen (R14), done or not:
- Session 2, "not sure" what the start is for: **done.** The purpose line still leads, now
  above the first question (`YouChapter.test.tsx`, the purpose-line test).
- Session 2, "Chat should be immediate": **done.** The reply field is on the first screen
  beside the first question (the three captures).
- Session 2, "too much helper text": **done** for the first question (a placeholder only). The
  closest step adds one line saying what Careerwright looked up.
- Session 2, "starting with a preference setting is off-putting": **done.** The start now
  opens with one plain question, not a setting.
- Session 2, "trying to do too much on one page": **partly.** The start now has two free-text
  fields, the title field and the reply field (M-9).
- Session 2, C1, "ditch the tone selection": **done** earlier and still absent at the start.
- The product owner's direction (2026-10-31), "the frustration of your ideal job not
  appearing as an option": **done for the first question.** Any title the UK index lists is
  offered, and "Use my own words" is always there.

### Spec Compliance
- ❌ Issues found:
  - Pressing Enter on a partial list saves ESCO's first guess and drops the person's words
    (I-1; `FirstQuestion.tsx:133-138`, `:171`, `:207`).
  - Acceptance 3 and the binding decision: after the type-ahead's "None of these is my job",
    the Suggestions view asks the person to "Choose the ESCO occupation closest to it" (I-2;
    `vocabulary.ts:711`, `exploration.py:911`).
  - The first free-text field at the start is not screened for distress (I-3).
- Acceptance, in the demo with no key and no network:
  1. ✅ `e2e/role-space.spec.ts`, first test. All four titles are offered as "UK job title
     (ONS)", "Use my own words" is offered for each, and no request leaves the machine.
  2. ✅ The pick keeps the exact words (What we know shows "Registered nurse"). The light comes
     on within the ten-second bound, and focus moves to "Which of these is closest?". Group 2221
     offers its ESCO occupations and "None of these is my job". The one-second figure is the
     API's (`test_first_answer.py`, not re-run). The browser asserts ten seconds, as the
     dispatch binds.
  3. ⚠️ Partly. The start keeps the words, says what isn't known yet and asks no closest
     question. The Suggestions view later asks for a different job (I-2).
  4. ⚠️ Not shown in the demo: the fixture proposer makes no title ideas. It is proven by
     `Directions.test.tsx`, `test_role_space.py` and DSC-20. The list's words match the card.
  5. ✅ For the start and the title-idea list ("Not compared with your experience yet."). The
     e2e's "no skills in the world" check can't fail (M-6). A nearby heading shows unknown
     familiarity as known (M-2).
- The report's concerns:
  - **Would each test fail without its code?** Yes for the web tests: each needs the new
    component, constants or region. One e2e assertion can't fail (M-6). No test presses
    Enter on a partial list (I-1).
  - **The first question before the entry choice, with "Skip for now":** within the card.
    Plan section 4 says the sure or unsure entry follows the first answer. On a phone the
    field is in the first screen at 390 × 844 (the capture and the UI-12 e2e). The closest step
    and the kept-words entry are not checked on a phone (M-3). By my layout estimate,
    "None of these is my job" sits about 600 px down, inside the first screen.
  - **Not built: making an index title idea a target from its list.** Not required. The card
    says "become suggestions", and acceptance 4 asks for the list, its answers and its words,
    not an action. A question for session W2 (M-7).
  - **Not built: "Which do you mean" in the start for own words that several ESCO
    occupations hold.** Not required: the card's closest question is about an ONS title's
    groups. The slate then says "until you choose which one you mean" with no control for the
    role (M-4).
  - **The heredoc slip:** process only. The file was restored and redone with Edit, and the
    product is unaffected.
  - **Seeding needs the index first:** the app half.
- ⚠️ Cannot verify from diff:
  - A real phone's keyboard over the options list; VoiceOver; Safari. Not run, requires human
    (R2).
  - The words, the layout and session W2's questions. Not run, requires human. The report
    claims no human gate.
  - `make check` and `make acceptance` (the implementer's runs).

### Strengths
- The start is one decision at a time: the first question, then the closest question for a UK
  title, then how to start. Focus follows each decision to the next heading
  (`Conversation.tsx:255-260`). "Skip for now" saves nothing, and its focus is tested by
  keyboard (`e2e/keyboard.spec.ts`).
- The type-ahead is a proper ARIA combobox. It has an `aria-activedescendant`, a hidden
  listbox when closed and 44 px options. A UK title's accessible name is "Registered nurse,
  UK job title (ONS)", read after a pause. Options never take focus, so Tab goes straight to
  "Skip for now".
- Every new line says what Careerwright did: "found … in the UK job-title index and looked up
  …", "keeps … as your role, in your words", "couldn't match it in ESCO or the UK job-title
  index". None claims what a list contains. Unknown is said plainly ("What this work asks for
  isn't known yet") and never as zero. The plural for a title in several groups is right
  (`vocabulary.ts:876-887`).
- `ROLE_KEPT` and `TITLE_IDEA_SHOWN` are exhaustive maps over generated unions. `FOUND_NO_WORK`
  and `TOO_GENERAL_BY` replace the old branching, and the words that can be reached are
  unchanged.
- "None of these is my job" comes before the occupations, so the way out stays in the first
  screen even for a 91-occupation group. Groups show 12 at a time, and focus moves to the
  first newly shown occupation.
- No new colour pairing. The selected option is edged in the selection colour, which is its
  meaning.

### Issues
#### Critical
None.

#### Important
**I-1. Enter saves a title the person didn't choose** (`FirstQuestion.tsx:133-138`, `:171`,
`:207`; `queries.ts:585`).
- **What happens.** Every keystroke resets the active option to the first (`:171`), and that
  option is drawn as selected (`:207`). Enter picks it (`:133-138`). In a partial list the
  first option is ESCO's closest guess. So typing "Bookkeeping assistant" and pressing Enter,
  the usual way to submit a field, saves ESCO's "bookkeeper": `choose_role` stores the ESCO
  label (`exploration.py:1357-1379`).
- **A second path.** `useTitleMatches` keeps the previous query's list as placeholder data
  (`queries.ts:585`), and `FirstQuestion.tsx:90` accepts it as the answer for the new text.
  For one request's length, the list and its partial flag belong to the last settled text. An
  Enter or a quick tap then saves a title from that earlier list.
- **Why it matters.** The person's words are lost on the start's main path. The card's "Is it
  one of these?" is answered yes on their behalf. The start moves on to "How would you like to
  start?" with no line saying what was saved, and the wrong occupation then drives the origin
  and the slate. A screen-reader user hears the first option as selected but not the partial
  question (M-1).
- **Fix.**
  - Make no option active until the person moves to one, so Enter with none active keeps
    their own words. At the least, make "None of these is my job / Use my own words" the
    default in a partial list.
  - Ignore placeholder data (`found.isPlaceholderData`, or compare `found.data.query` with the
    typed text). Show "Looking for job titles…" and only the own-words option until the
    fresh list arrives.
  - Add a test: type a partial title, press Enter, and expect `name_role` with the typed words.

**I-2. After "None of these is my job" in the type-ahead, Suggestions asks for another job**
(`FirstQuestion.tsx:118-122`; `titles.py:57`; `exploration.py:911`; `vocabulary.ts:711`).
- **What happens.** The partial list's "None of these is my job" calls `name_role`, which
  records nothing about the refusal. `declined` is read only from a `none_of_these` record,
  which only `choose_closest` writes. So for "Bookkeeping assistant" (acceptance 3), any slate
  with fewer than six suggestions carries `title_not_matched`: "Careerwright couldn't match
  “Bookkeeping assistant” to an occupation in ESCO, so it can't join other work to that title
  by shared skills. Choose the ESCO occupation closest to it."
- **Why it matters.**
  - It asks for a different job right after the person said none of ESCO's titles is theirs.
    That breaks acceptance 3, the binding decision, and ADR 0015's amendment line ("nothing
    asks for another job").
  - The app has no control for that action. The type-ahead and the closest step exist only in
    the start, which is gone once an entry is chosen or a message is sent.
  - The same line follows "Use my own words" for any title neither list holds.
- **Fix.** This is a reproduced defect, so R11 permits a change. Say less:
  - Record the type-ahead's "None of these is my job" as the person's refusal, so
    `title_kept_as_own` words it.
  - For a role kept in the person's words with no closest question, word `title_not_matched`
    without "Choose the ESCO occupation closest to it", or give that case a reason of its own.
  - Add one slate-words test for a role kept in the person's own words.

**I-3. The first question bypasses the support screen** (`FirstQuestion.tsx:107-124`;
`exploration.py:1407`; `Conversation.tsx:289-296`; screen only at `routes_interview.py:75`).
- **What happens.** This slice puts an unscreened free-text field above the reply field, at
  the most exposed moment of the start. A risk phrase typed there is offered back as "Use my
  own words: “…”" and saved as the role. The start then echoes it: "Careerwright keeps “…” as
  your role, in your words. … what this work asks for isn't known yet." No calm panel is
  shown, and the world doesn't still. The same text typed in the reply field would show the
  panel.
- **Why it matters.** The support panel is a high-effect item (R14; the contract's
  calibration). `CLAUDE.md` says any listed risk word shows the panel beside the conversation,
  and this question sits in the conversation view.
- **Fix.**
  - Run the same deterministic screen on the title before saving. When it triggers, show the
    panel as a message does, still the world, and don't echo the words as "your role".
  - Whether direct entries in What we know are screened too is a policy question: ask the
    product owner in one sentence (R14). The first question's case doesn't wait on it.

#### Minor
- **M-1. Status lines aren't announced** (`FirstQuestion.tsx:179-186`, `:197`).
  - Screen readers don't hear "Careerwright couldn't match that title in ESCO. Is it one of
    these?" or "Careerwright found no job title holding those words." The first is linked
    only by the listbox's `aria-describedby`, which `aria-activedescendant` navigation doesn't
    read. The second is in no live region. The result count isn't announced either.
  - This is WCAG 2.2 4.1.3, an accessibility rule, so R13 lets it stay in the task.
  - Fix: describe the combobox, not the listbox, and put the partial and none-found lines in a
    polite status region.
- **M-2. "Something different" for a role Careerwright couldn't place** (`Directions.tsx:688`,
  `:771-773`).
  - `familiarityKnown` is true whenever the role is provided. For a role kept in the person's
    words (acceptance 3) or after "None of these is my job", the backend had no familiar
    families. Its suggestions in the less-familiar direction are still headed "Something
    different", a claim of difference from their work that nothing computed.
  - The logic was there before this slice, but this slice makes it the main path for own
    words. It is the R14 "unknown versus known" kind, so the controller may keep it in the
    task.
  - Fix: take familiarity from the API's own fact, not from "role provided".
- **M-3. The new start states aren't checked on a phone, and the reference set is thin.**
  - UI-12 checks only the title field. The closest step and the entry choice with its
    kept-words line are not checked at 390 × 844.
  - No capture or story shows the type-ahead open (UK title, partial question, none found)
    or the closest step at phone size. Those are what session W2 will judge, and stories
    become the reference once a chapter is built (R13).
  - Whether a real phone's keyboard hides the options, "Use my own words" (last) included,
    needs a human check (R2).
- **M-4. The type-ahead and the closest question live only in the start.**
  - There is no way back from "Which of these is closest?" to fix a wrongly picked title.
  - Once an entry is chosen, or a message is sent while the closest question shows (the reply
    field is visible), the question is gone for good.
  - A role named later (the conversation, What we know) never sees either. An ambiguous
    own-words role gets no "which do you mean", while the slate says "until you choose which
    one you mean".
- **M-5. Words for session W2** (questions, not defects):
  - The group headings show "(ISCO-08 2221)", an unexplained code (`vocabulary.ts:880-881`).
  - "None of these is my job" is the step's only choice edged in the action colour, while the
    occupations are secondary (`FirstQuestion.tsx:306-336`). This may nudge toward "none".
  - A title whose groups all hold no ESCO occupation still asks "Which of these is closest?"
    with nothing to pick.
- **M-6. A vacuous e2e assertion** (`e2e/role-space.spec.ts:91`, `:121`). "No skill labels in
  the world" can't fail, because the world never draws skills (`model.ts:54`). Acceptance 5's
  browser check proves nothing yet.
- **M-7. Index title ideas have no action** (`Directions.tsx` `UkTitleIdeas`). A suggestion
  that can't be made a target where it's shown is a practical gap. The card doesn't require
  it, and REC1-06 records it. A question for session W2.
- **M-8. Two small closest-step glitches.**
  - While a closest choice saves, every occupation button shows its own "Saving…" beside it,
    13 or more at once (`FirstQuestion.tsx:293`, `:306`, `:332`).
  - `onAnswered` sets `leaving` before the save and never clears it on failure
    (`FirstQuestion.tsx:110`, `:295`; `Conversation.tsx:255-260`). A role that arrives later
    by another path moves focus unasked, which the N-M6 rule forbids.
- **M-9. Two free-text fields at the start**: "Start typing your job title" and "Reply in your
  own words", with "Use my own words" in the list. A person may answer the first question in
  the reply field. This echoes session 2's "trying to do too much on one page". A question for
  session W2.

Agent pre-review, not the required human review: the start is built to plan section 4's words
and order. The world's answer is the person's light coming on, and the type-ahead itself is a
plain list. That meets R13's bar for a path task. The moment is judged at Task M.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The flow is right: the plan's order and words, focus following each step, and
every new line saying what Careerwright did. But three paths can mislead or harm the person.
Enter replaces their typed title with ESCO's guess (I-1). "None of these is my job" is followed
by a request to pick another job (I-2). A distress phrase typed at the first question gets no
support panel and is echoed back as their role (I-3).
