# Task W2E review: app, truth and tests half

Reviewer: Claude (Opus 5.5), read-only. Commits 8410eff, 7c3a72b, c64b636, 4dcc2ca (base
ec4d060). The main tree's HEAD has moved on (Task 13a's commits), but none of them touch the
files below, so line numbers match the working tree. I read the backend, API, generated client,
web components, `vocabulary.ts`, unit tests, e2e tests, register rows and ADR lines in full, and
skimmed the design-reference diff. No suites re-run. I ran two small offline probes of the demo
interviewer (`fixture_turn` called directly with `uv run --locked python -I`, scratchpad
scripts, no database or network) to confirm finding I1.

### Spec Compliance
- ❌ Issues found:
  - "The demo conversation never loops" and F10's rule (words never name a control that isn't
    there): the demo's "couldn't note" reply sends the person to example replies that aren't
    shown, at the role question and after the last question (I1).
    `backend/src/careerwright/profile/fixture_interviewer.py:89`, `:306`
  - Fix round 1's focus rule, applied to the new controls: tapping an example reply drops
    keyboard focus (I2). `apps/web/src/components/Conversation.tsx:446-453`
  - "Name a role" opens target entry when asked. Today it opens it again every time the answer
    form opens later (I3). `apps/web/src/components/ProfileEditor.tsx:80-96`
- Compliant:
  - The current-slate rule: decided in code, small and pure, tested at domain and
    PostgreSQL level, recorded as an ADR 0007 amendment line that matches the code.
  - The API adds facts only, no new prose (R11): `DiscoveryOut.current` (bool),
    `ProposalOut.asks_about` (enum), `SuggestionOut.shared_skills` (labels). The client is
    regenerated and matches.
  - Rail marks, Routes "not built yet" in every workspace, F10's budget words in both places,
    the England line, "Hold the world still".
  - Focus to "Saved as one of your targets", to "Directions to explore" (both ways in) and to
    the target box.
  - N1, N2 and N3 each have a test that reads what the person sees.
  - The new demo patterns are only the ones the card names (R11).
- ⚠️ Cannot verify from diff:
  - The live bridge and a model's handling of the two buttons (no live calls; Task 3b).
  - That the new N1 browser test fails on the old build. It wasn't run there. The unit test
    shows the mechanism failing first, and the browser test reads boxes as they stand after
    each view change, so it should fail.
  - VoiceOver and Safari: not run, requires a human.

The implementer's concerns, judged:
- **The one-token edit made with a Python replace:** a process slip with no effect on the
  product. The change is in the reviewed diff. Nothing to do.
- **The ten-second bar:** plan v1.5 line 610 moves the ten-second test to S2.8, the first
  question (Task 6d). Not a W2E gap.
- **The rare demo case recorded as a limit:** fine as a limit, but wider than recorded. See M2.
  It is separate from I1, which isn't rare.
- **The N1 browser test, not run on the old build:** acceptable (see above).
- **The design check that treats sideways-scrolling rows as not clipping:** slightly weaker
  than what it guarded. See M5.
- **The route preview's layout tests, removed with the preview:** right, since the preview is
  gone from every page. But the register still cites those tests as evidence, and nothing
  hands their contracts to Task 14. See M6.

### Strengths
- `changed_only_by_choices` is pure and easy to read. `answers_current` only accepts an
  `occupation_choice` source whose run is this discovery, so a choice from ESCO or from another
  slate still marks the slate as based on earlier answers.
- The note's guard uses the same rule, and the note still quotes only the pinned answers
  (`_pinned_document`).
- Profile saves and stream events invalidate the whole workspace scope, so `current` stays up
  to date in the web (`queries.ts:208`, `:250`).
- Tapping an example reply never loses the person's typed draft: `send` clears the field only
  when the text sent is the draft (`Conversation.tsx:330-333`).
- "Show me suggestions" and the view's own button share one rule (`suggestionStart`), so they
  can't drift apart. Neither button commits anything (unit tests assert no other write).
- The first-screen tests are real geometry: the box is inside 0 to 844 and on top at its centre
  (`conversation.spec.ts:44-58`). The N1 test reads the "You" label's box and the console's box
  after each view change, with no scroll, plus an on-top tap check at each tab.
- The shared skills are proved equal to the database's shared set (`test_discovery.py`), and
  work found by a search names none.
- The backend walk test taps every example reply for both ways of starting and checks that no
  question repeats.
- Captures are from 11:17 to 11:18, after c64b636 (11:03), consistent with the reported run.

### Issues

#### Critical
None.

#### Important

**I1. The demo's "couldn't note" reply points to example replies the person can't see, and at
the end of the demo saying Skip just repeats it.**
- Where: `backend/src/careerwright/profile/fixture_interviewer.py:89` and `:306`, with
  `apps/web/src/components/Conversation.tsx:436-453`.
- What: the reply is "Thank you. I couldn't note anything from that. Tap an example reply, or
  say Skip." It is used whenever the question after a message equals the question in front.
  Two common cases have no example replies on screen. Both confirmed by probe:
  - At "Do you have a role in mind, or would you like to explore?", the web shows "Show me
    suggestions" and "Name a role" instead of example replies (the e2e test asserts the group
    is absent). The most natural typed answer, "Explore" or "I'd like to explore", gets this
    reply.
  - After the last question nothing is in front and nothing comes after, so `None == None`.
    Any message ("What next?", "Hello", even "Skip") gets this reply, with no question and no
    examples. Saying Skip, as told, returns the same sentence forever.
- Why it matters: the person is told to use a control that isn't there, which is the defect F10
  fixed for the budget words. At the end of the demo it is a loop, the thing the card's first
  item removes.
- Test gap: the backend walk test's own table claims example replies exist at the role
  question (`test_interview_agent.py`, `EXAMPLE_REPLIES[TARGET_TITLES]`), but the web hides
  them there. No test covers the role question or the end of the conversation.
- Fix:
  1. Use the "couldn't note" reply only when a question is in front (`after is not None`).
     Otherwise say "Thank you."
  2. Make the role question's way on true: either show its example replies beside the two
     buttons, or word the reply so it names only what is always there ("say Skip").
  3. Add a test for each case.
  4. STATE-09 should stay planned until this is fixed.

**I2. Tapping an example reply drops keyboard focus.**
- Where: `apps/web/src/components/Conversation.tsx:446-453`, with `ExampleReplies` at `:205`.
- What: the examples render only while `sendBlocked === undefined`. The tap starts the send,
  `sender.pending` sets "Sending…", and the group unmounts with focus on the tapped button.
  Focus falls to the page body.
- Why it matters: a keyboard or screen-reader user loses their place on the conversation's main
  new action. The same file's rule is "the button goes; focus is never lost (M-1)" (`:471`).
  Fix round 1's "Help me explore instead" concern was this same kind of defect. Accessibility
  findings stay in the task (R13).
- Fix: move focus to the reply field, which stays mounted, when an example is tapped (or keep
  the group mounted and disabled while sending). Add a unit test that focus is on the reply
  field after a tap.

**I3. "Name a role" fires again every time the answer form opens later.**
- Where: `apps/web/src/components/ProfileEditor.tsx:80-96`, with `YouChapter.tsx:144`,
  `:243-247`, `:364-374`.
- What: `openTarget` counts requests and never resets. The editor applies the request in an
  effect, and an effect runs on mount. Closing the form ("Close the answer form") unmounts the
  editor. The next "Edit answers directly" or "Add the details yourself" mounts it with
  `openTargets` above 0 again. That switches Target roles to Answered in the draft, and the
  first route also moves focus into the empty "Target role 1" box.
- Why it matters: after one "Name a role", a person who later opens the form to change
  something else finds a field changed that they didn't touch. Saving is then refused with
  "required" on Target roles (`lib/profile.ts:118`, an empty answered list) until they set it
  back by hand. The brief asks for "Name a role" to open target entry when asked, not on later
  openings.
- Fix: treat the request as a one-off. Clear it in the parent once applied (an
  `onTargetsOpened` callback that resets `openTarget`), or keep the last request applied in the
  parent. Add a unit test: Name a role, close the form, open it with "Edit answers directly",
  and Target roles is unchanged with focus on the form's heading.

#### Minor

**M1. The unexpected connection's words.**
- Where: `apps/web/src/components/Directions.tsx:285-299` and `lib/vocabulary.ts:273`.
- What: two problems.
  - The card now shows the API's `still_uncertain`: "These are the skills ESCO lists for both
    roles. They aren't compared with your own experience yet." The first sentence says what a
    list contains (the sentence rule).
  - The new line quotes ESCO's title for the person's role ("your role, “bicycle courier”").
    The why line on the same card quotes the person's own words for it
    (`exploration.py:691`). When the person's title is an ESCO alternative title, the card
    shows two different quoted names for "your role".
- Why it matters: low effect, but R14 applies the sentence rule to every sentence a person
  reads, so it shouldn't wait.
- Fix: write the uncertainty line in the web and say less ("Careerwright hasn't compared them
  with your own experience yet."). Drop the quotation marks around ESCO's title, or name the
  role as the why line does.

**M2. The recorded limit is wider than the register says.**
- Where: `fixture_interviewer.py:135-149`.
- What: the question in front is recomputed from the current profile. So an answer saved in
  What we know while a demo question is on screen also shifts it. Example: with "Which English
  cities…?" showing and cities filled in the form, "Skip" proposes skipping weekly hours, a
  question the person never saw.
- Why it matters: it is only a proposal the person reviews, and nothing is saved without them.
- Fix: widen STATE-09's "Accepted limit" wording to cover answers saved outside the
  conversation, not only Keep none.

**M3. No negative test for the run filter in `answers_current`.**
- Where: `exploration.py:241-263`.
- What: no test shows that a target chosen from another discovery's slate, or straight from
  ESCO (`discovery_id` null), makes the slate stale. Breaking the `source.run_id == run.run_id`
  filter would pass every test.
- Fix: add one integration case to `test_discovery.py`.

**M4. Live: the two buttons show under any question at a certain stage.**
- Where: `lib/conversation.ts:134-146`.
- What: they appear under whatever the model asks once the four early answers are in and there
  is no target, not only under a question about a role. This is the implementer's ruling 2,
  since a model's question is never classified.
- Fix: none now. Worth one look in Task 3b's first live run, or as a session W2 question.

**M5. The design check's sideways-scroll exemption is broader than it needs to be.**
- Where: `docs/design/tools/screenshots.mjs:160-176`.
- What: `if (scrollsAcross(a)) break;` stops the walk at the scroller. Words inside it are no
  longer checked against the panel or any clipping box outside the scroller. A scroller wider
  than a panel that clips would hide words for good and still pass. This doesn't happen in
  today's references, but the check now guards less than before.
- Fix: at the scroller, keep walking outwards with the scroller's own box in place of the
  word's. The design half owns the references, so pass this to them.

**M6. UI-09 still cites the removed route-preview tests as evidence.**
- Where: `docs/requirements-register.md`, UI-09.
- What: the row's T6c part still names `e2e/layout.spec.ts` for V-03 and V-04 (first route
  cards, the sheet's peek). Those tests left with the preview, and no row hands the contracts
  (V-03, V-04, S0-V07) to Task 14, which builds real routes.
- Fix: mark the T6c evidence as retired and add the three contracts to Task 14's part of
  UI-09. This is a register-tidiness item, batched for the final review.

### Assessment
**Task quality:** Needs fixes

**Reasoning:** The backend rule, the API facts and most of the web are correct and well tested.
But the demo still has a loop: it tells the person to tap example replies that aren't on screen
(I1). Tapping an example reply loses keyboard focus (I2). "Name a role" changes the answer form
again on later openings (I3). Each is a small, local fix with a focused test.
