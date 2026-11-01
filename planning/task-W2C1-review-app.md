# Task W2C part 1 review, Half B (app, truth and tests)

Reviewer: Claude (Opus 5.5), read-only. Commits 92ea74f, 5c14792, 68c8b2f, 6af1097 (166e4ef..6af1097).

How I read it: the dispatch, the contract, the implementer's dispatch, the carry-forward file and
the report, then the diff in passes (backend and tests; e2e; components; vocabulary, world,
stories, register, ADR 0007). I looked outside the diff only for named risks, listed with each
finding. No suite was re-run. One offline check of my own: a rough scan of the pinned ESCO zip
for the hyphen risk (M5), in the scratchpad. I also looked at the phone and tablet captures
already in `apps/web/test-results/` (written at 06:48 today on this tree, not by me).

## Spec compliance

**❌ Issues found**

- The carried truth fixes: every line the carry-forward file names now says what the match or
  search did, and each has a test that reads its words (table below). The nearest lines it did
  not name were missed: three OpenAPI descriptions still say what ESCO "does not hold" (I3).
- The hyphen: the committed test pins the database's own parse
  (`'first-aid' & 'first' & 'aid'`, `test_evaluation.py:533-549`), so the confirmation is on
  record, not just claimed. The fix reads a hyphen as a space in skill searches only, and it is
  disclosed in ADR 0007 decision 13 rule 1 and both docstrings. Accepted (one Minor note, M5).
- Strip and key: plain words, the update state shown only when not live, "Synthetic demo" at
  every width, and two rows at 768 px (the `you--unavailable--768x1024` capture confirms it). The
  key check now reads `data-keyed`, and a new test covers the empty key. The phone test is
  steadied by waiting, with its assertion unchanged. All done, but see M1: the product itself
  still jumps on a phone.
- "Your world" DOM list: it names every skill and gives openings one count line, with a test.
  Done.
- Invariants: no new code shows an API message. Enums, money and error codes come from the
  generated client. No rank is computed (the open suggestion is the first listed). Fixture
  content stays labelled ("Demo interviewer…" stays). Pause and sound are untouched. The still
  world gets a new identical-text test. DBOS `application_version` is still
  `careerwright-l0-1` (`identity/worker.py:30`), and nothing in `identity/` changed.
- Focus return: the report says "focus returning to what each step did". That's untrue for
  "Add the details yourself" (I2).
- Scope: nothing of part 2 is half-built. The world's skill and opening words are tested but not
  fed by the app yet. No visible placeholder was added, which is acceptable.

**⚠️ Cannot verify from the diff:** the `make check` and `make acceptance` passes on 6af1097
(not re-run, as instructed); the RED runs described in the report; every human-only gate (the
report rightly records them as "not run — requires human").

### The carried lines, checked

| Line | Now | Words tested by |
|---|---|---|
| Title idea's why-line (`exploration.py:651-653`) | names the idea, "matched that title to this occupation in ESCO" | `test_slate.py:683-708` (idea matched through another label) |
| Sketch "Several ESCO occupations have this title" (`sketch.py:143-144`) | "Matched to several occupations in ESCO" / "Careerwright matched this title to several…" | `SketchCard.test.tsx`, `test_discovery.py:525-556` |
| Sketch "Your own title, not in ESCO" | "Your own title: Careerwright couldn't match it in ESCO" | `SketchCard.test.tsx` |
| Sketch "No ESCO record…" (`sketch.py:167-168`) | "Careerwright couldn't match this title…" | `test_discovery.py:525-556` |
| Confirmed-title label (`concepts.py:36`) | "…that Careerwright couldn't match in ESCO" | `test_provisional_concepts.py:58` |
| Refusal "ESCO already lists this title" (found on the way) | "Careerwright matched this title to an occupation in ESCO…" | `test_provisional_concepts.py:77-79` |
| OpenAPI `unsupported_hypotheses`, `unmatched_titles`, `ambiguous_titles` | match words; client regenerated | client-drift check (not re-run) |
| Type-ahead `partial` | "Careerwright couldn't match that title in ESCO. Is it one of these?" | not rendered (part 2) |
| `_unmatched`, `_ambiguous`, empty join, web title-ideas line | words pinned | `test_slate.py:660-681`, `test_origin.py:183-199`, `Directions.test.tsx:216-221` |

## Strengths

- The truth fixes are complete for every named line, each read by a test, and the implementer
  found and fixed one more of the same kind (the refusal message).
- The hyphen fix is minimal, applies to both skill queries, and its test proves "first-aid" and
  "first aid" give the same total, skill count, exact flag and order.
- The key check no longer passes for "You" alone. The empty-key test is a real check (no key
  element at all).
- The phone strip test keeps its exact assertion and waits on observable conditions (saved
  state, live updates, fonts, two equal frames), not a longer timeout.
- "Keep none" now calls `onSaved`, so focus no longer drops there (an old gap, closed).
- Every changed assertion is disclosed. I checked the ones that looked weaker: V-02's
  heading-to-tab swap is equivalent, because the tabs render only after every load succeeds.

## Issues

### Critical

None.

### Important

**I1. Moving between the You chapter's views throws away what the person typed or chose.**

- **Where:** `apps/web/src/components/YouChapter.tsx:259`, `:297`, `:316`. Each view is rendered
  only while selected (`{view === "conversation" && …}`), so the others unmount.
- **What is lost:** each of these components keeps its state locally, so it is gone when the
  view unmounts:
  - **The reply being typed:** `Conversation.tsx:210`.
  - **The tray's Accept and Confirm choices and edits:** `ReviewTray.tsx:87-89`.
  - **The answer form's unsaved edits and its stale-save notice:** `ProfileEditor.tsx:53-58`.
    `editing` lives in YouChapter, so the form reopens showing the saved values. The person
    may not notice their edits vanished.
  - **The slate's view controls:** "Not for me" and the emphasis (`Directions.tsx:485-487`).
- **Example:** someone accepts two of four proposals, opens "What we know" to see what the limits
  mean, and comes back: both choices are gone. Before W2C everything was on one page, so this
  could not happen. Nothing warns them, and no test switches views mid-task.
- **How I know:** from reading the code and React's unmount rule. I didn't run it.
- **Why it matters:** silent loss of the person's input. "Failure is never an empty success"
  applies, and the tabs make it routine. It also makes M2 routine.
- **Fix:** keep the three panels mounted and hide the inactive ones (`hidden`). Each tab can then
  always point at its panel. Three things change with it:
  - Count visible primaries only in `YouChapter.test.tsx` `count()` and in
    `conversation.spec.ts`'s `main .btn-primary`.
  - Render `SaveNotice` once, or give each copy its own ref (both views use `notice` today).
  - Add a test: type a reply, accept one proposal, edit an answer, switch views and back, and
    all three are still there.

**I2. "Add the details yourself" drops focus to the page.**

- **Where:** `YouChapter.tsx:204-207` (`edit` switches to What we know); the button is at
  `Conversation.tsx:332-333`.
- **What:** the button sits in the conversation view, so switching views unmounts it. Nothing then
  takes focus: the "What we know" heading has no ref or `tabIndex` any more, and
  `ProfileEditor` focuses only a stale notice. A keyboard or screen-reader user lands on
  `<body>` during a failed-reply recovery.
- **Before:** in Sprint 2 the form opened under the conversation and the button kept focus.
- **The test misses it:** `conversation.spec.ts:283-290` checks only that the tab is selected.
- **Why it matters:** this is a regression of what UI-06 already relies on, it contradicts the
  report, and earlier rounds treated focus landing on nothing as Important (B-I4).
- **Fix:** after `edit()`, move focus to the answer form's first field, or to a focusable "What
  we know" heading. Assert it in `YouChapter.test.tsx` and in the phone journey.
- **Same pattern, older:** "Help me explore instead" (`YouChapter.tsx:318-334`) also unmounts
  itself; that one dates from before W2C.

**I3. Three published API descriptions still say what ESCO holds (the rule the carried fixes
apply).**

- **Where:**
  - `backend/src/careerwright/api/catalogue_schemas.py:311`: `ProvisionalConceptOut`, "A
    title the person verified that ESCO does not hold".
  - `api/discovery_schemas.py:577`: `close_matches`, "For a title ESCO does not hold".
  - `api/origin_schemas.py:61-63`: `RoleOut`, "an answer ESCO does not hold joins nothing".
  - All three are in the generated contract: `apps/web/src/generated/openapi.json:12510`,
    `:13522` and `:16757` (and `types.gen.ts`).
- **What:** these are the same false class as the carried items. "facade cleaner" matches
  nothing, yet ESCO lists "façade cleaner". The first is the API twin of the label fixed in
  `concepts.py`. The second sits 60 lines below the fixed `unmatched_titles`.
- **Why it matters:** the carry-forward made the OpenAPI lines must-fix. The dispatch asks for the
  rule to hold "in every case, including the nearest unnamed ones". These are developer docs
  only, not shown on screen.
- **Fix:** words only, then `pnpm run generate`. For example:
  - "A title the person confirmed that Careerwright couldn't match in ESCO"
  - "For a title Careerwright couldn't match to an occupation in ESCO"
  - "an answer Careerwright couldn't match in ESCO joins nothing"
- **For part 2:** the `RoleState.NOT_IN_ESCO` value is a contract, so keep it, but when part 2
  gives it words, they should say what the match did.

### Minor

**M1. On a phone, a strip that isn't live grows a second row.**

- **Where:** `WorkspaceStrip.tsx:74-102`. V-08's one-row rule applies only above 760 px
  (`globals.css:1699`).
- **What:** the capture `apps/web/test-results/visual-390x844-…/screenshots/you--unavailable--390x844.png`
  shows "Updates: Reconnecting" pushing the account menu to a second row, about 48 px. Compare
  `you--390x844.png`. "Updates: Connecting" is the same length class, so it likely also happens
  on every phone load. That matches the flake's 105 px then 57 px.
- **Why it matters:** the test is now steady, as asked. But the strip and everything below it
  still jump on a phone, and hiding the words while live widened the gap between live and not
  live.
- **Fix:** keep the phone strip one row. Either let the state's words shorten with an ellipsis
  (assistive tech still reads them all), or give the state a reserved slot. Add the
  reconnecting case to the phone strip test.

**M2. Opening the slate again re-sends a refused note request automatically.**

- **Where:** `Directions.tsx:494-506`.
- **What:** `asked` is a ref, so it resets whenever the slate remounts. If a request was refused
  with no run, `explanation` stays null, and the request goes out again on the next mount.
  The code's own comment, and ADR 0007 decision 12, say a refused request is sent again "only
  ever by the person's click".
- **Why it matters:** this happened before only on changing chapter; with tabs it happens every
  time the person opens Suggestions. If the refusal was the spending limit, and the limit has
  since been raised, the re-send could start a model call without a click.
- **Fix:** I1's fix (the slate stays mounted) covers the tabs. To also cover changing chapter,
  keep "asked" per discovery outside the component (the query cache or YouChapter).

**M3. The open suggestion's toggle says it is expanded but can't collapse.**

- **Where:** `Directions.tsx:284-296`, `:633`.
- **What:** clicking the open title does nothing.
- **Fix:** the ARIA accordion pattern says to mark that header `aria-disabled="true"`, or let it
  close.

**M4. Coverage gaps behind claims in the report and register.**

- **The tray's limit meaning (`ReviewTray.tsx:203-205`) is untested.** "explains the two limits
  … where they are shown" (`YouChapter.test.tsx:327`) checks only What we know.
- **The keyboard journey stops before Suggestions** (`keyboard.spec.ts:68-123`). Neither the
  suggestion toggle nor "Make this a target" is reached by keyboard, though UI-06 now says "the
  chapter completes from the keyboard alone".
- **The moving/still identical-text test runs only on the fixture workspace's states**
  (`world.spec.ts:378-408`). Neither a tray nor a slate is compared.
- **Fix:** one assertion each, or narrow the register's words to what is tested.

**M5. The hyphen fix also changes the "exact" check for a hyphenated skill name.**

- **Where:** `taxonomy_store.py:242-247` with `:266-269`.
- **What:** a search typed exactly as such a name (for example "use e-learning platforms") is
  no longer "named by exactly its words". The query drops the whole hyphenated word, and the
  skill's vector keeps it. That flag exempts a search from being too general
  (`slate.py:195-199`).
- **Real effect today:** none that I found. My rough offline scan of v1.2.1's 350 hyphenated
  essential skill names (crude tokens, not PostgreSQL's parser) found no search that flips to
  too general.
- **Fix:** say so in the docstring and the ADR ("ranking is unchanged; a hyphenated skill name
  typed with its hyphen no longer counts as exact"), or compare against the label read the
  same way.

**M6. The tablet strip drops work areas and budget.**

- **Where:** `WorkspaceStrip.tsx:172-177`, `globals.css:1707-1726`.
- **What:** the specification (line 193) lists both for the desktop shell, which the tablet
  uses (it has the rail). The report says so in section 3, but doesn't list it as a reading
  for session W2.
- **Fix:** list it for session W2, or keep a short budget in row one.

**M7. While paused, the bright primary is a Send that can't send.**

- **Where:** `Conversation.tsx:410`, `:418-424`.
- **What:** Send stays the view's bright primary while disabled, and Resume, the only way on, is
  now a quiet button under the reply field. Before, it was a secondary at the top.
- **Overlap:** this crosses into Half A's primary-action work.
- **Fix:** while paused, make Resume the view's primary and Send secondary.

## Assessment

**Spec compliance:** ❌ Issues found (I3; the focus claim, I2).
**Task quality:** Needs fixes.
**Reasoning:** The truth fixes, the hyphen, the strip, the key and the DOM list are done well
and honestly tested. But the new tabs silently discard what the person typed or chose (I1) and
drop focus on a recovery path (I2), and three API descriptions still break the carried rule
(I3). All three are small, local fixes.

## Verdicts on the implementer's readings and rulings (my half)

- **Section 1, every carried line:** accepted. The extra refusal message is right (an API
  message, never shown by the UI, and its test reads it). Leaving the type-ahead's `partial`
  words to the OpenAPI description until part 2 renders them is right.
- **"Not shown failing first" for the four pinned-word tests:** accepted. They pin words W2B
  already changed, so no failing run could exist.
- **The hyphen:** accepted. Confirmed by a database parse that the test pins, fixed within the
  carried bounds (thresholds unchanged), disclosed in ADR 0007 as provisional for session W2.
  Tested on the full release. See M5 for one precision.
- **Reading 6 (Pause kept, quiet, under the reply field):** keeping it is right. Its rank while
  paused is not (M7).
- **Reading 8 ("version" kept in the answer form and the failed-reply alert):** accepted. The
  carried item named the strip, and the form's version ties to the stale-save conflict. It's
  already listed as concern 4 for session W2.
- **The strip:** saying nothing while live (the status region kept), and `data-events` and
  `data-version` for tests: accepted.
  - Hiding the workspace switcher below 1180 px: accepted (the account menu names the workspace
    and links to all of them).
  - Hiding work areas and budget at tablet: a specification change to list for session W2 (M6).
- **The key check by `data-keyed`:** accepted, and not passing by construction. Which names are
  shown and where the key is placed come from separate code. The empty-key test is real.
- **The flaky phone test:** accepted as asked (waits only, assertion unchanged). The jump it
  waited out is real (M1).
- **"Your world" DOM list:** accepted.
- **Slots for part 2 without a visible placeholder:** accepted. Nothing is half-built.
- **Changed tests:** each is justified and none is weakened.
- **Requirement candidates for W2D:** fine. Once I1 is fixed, add one: "moving between the You
  chapter's views keeps what the person typed or chose".
