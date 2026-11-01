# Task W2, slice W2C part 1 report: the You chapter in the world

Branch `l0-local-release`, from `166e4ef`. Implementer: Claude (Opus 5.5). No subagents, no live
model call, no web request, no headed browser, no frame measurement, `spikes/world` and the
running `careerwright-l0-*` stack untouched, `answers-2.md` not staged, DBOS
`application_version` still `careerwright-l0-1`. The only Docker use was the browser-test
project `careerwright-l0-webtest` (cached images), as `make acceptance` uses it.

## Status

DONE_WITH_CONCERNS. Every carried item and SW.4 finding is applied with tests; `make check`
and one `make acceptance` pass on the final commit `6af1097`. Concerns at the end (phone first
view, suggestions density, provisional choices for session W2).

## Commits

| SHA | Subject |
|---|---|
| `92ea74f` | The truth fixes carried from W2B: every line says what the match did, and a hyphen is read as a space |
| `5c14792` | Design references for the You chapter rebuilt in the world, and the two decision colours |
| `68c8b2f` | The You chapter rebuilt in the world, the strip in plain words, and every light named |
| `6af1097` | The You chapter, acceptance fixes: the reply field in the flow, a suggestion's details named only while open |

`6af1097` came from the first `make acceptance` (below): axe found two real defects, and one
journey (`access.spec.ts`) still opened the answer form from the conversation.

## 1. The truth fixes carried from W2B (commit `92ea74f`, on its own)

Rule (W2B round 5): every line says what the search or match did, never what ESCO contains.

| Carried item | What closed it | Test that reads its words |
|---|---|---|
| Title idea's why-line, "Careerwright thought of this title from it, and ESCO lists it" (`exploration.py` `explain`) | Now names the idea: "Careerwright thought of the title “dog groomer” from it and matched that title to this occupation in ESCO." | `tests/domain/test_slate.py::test_a_title_idea_names_the_idea_and_says_careerwright_matched_it` (an idea matched through another label, "dog groomer" → Animal groomer). RED on the old line, GREEN after. |
| Sketch "Several ESCO occupations have this title" (`vocabulary.ts` and `sketch.py`) | Web: "Matched to several occupations in ESCO"; sketch note: "Careerwright matched this title to several occupations in ESCO. Choose the one you mean." | `SketchCard.test.tsx` (new); `tests/integration/test_discovery.py::test_the_sketch_says_what_matching_each_title_did_never_what_esco_holds` |
| Sketch "Your own title, not in ESCO" (`vocabulary.ts`) | "Your own title: Careerwright couldn't match it in ESCO" | `SketchCard.test.tsx` |
| Sketch "No ESCO record, so no requirement list yet." (`sketch.py`) | "Careerwright couldn't match this title to an occupation in ESCO, so there's no requirement list yet. Not researched." | `test_the_sketch_says_what_matching_each_title_did_never_what_esco_holds` |
| Confirmed-title source label "A title you confirmed that ESCO does not list" (`profile/concepts.py`) | "A title you confirmed that Careerwright couldn't match in ESCO" | `tests/integration/test_provisional_concepts.py` first test (reads the stored label) |
| Found on the way, same class: the API refusal "ESCO already lists this title" (`concepts.py`) | "Careerwright matched this title to an occupation in ESCO: choose that occupation instead." | `test_an_esco_title_or_alias_is_refused_with_the_occupations_that_hold_it` (reads the message) |
| OpenAPI descriptions "Titles … that ESCO does not list" (`discovery_schemas.py` `unsupported_hypotheses`, `unmatched_titles`; also `ambiguous_titles` "that ESCO lists for several occupations") | Each says what Careerwright's match did; client regenerated (`pnpm run generate`) | developer docs; `make check`'s client-drift check passes |
| Type-ahead `partial` "ESCO doesn't list that title. Is it one of these?" (`catalogue_schemas.py`, `taxonomy.py` comment, ADR 0007) | "Careerwright couldn't match that title in ESCO. Is it one of these?" | nothing renders it yet (part 2's interface owns it); the OpenAPI description is the contract |
| `_unmatched`, `_ambiguous`: no test of their words | One assertion each | `test_slate.py::test_a_title_matched_to_none_or_several_says_what_the_match_did` |
| First slate's empty join: no test of its words | One assertion | `tests/integration/test_origin.py::test_a_role_no_other_occupation_joins_says_what_careerwright_found` (the sample's cook joins nothing) |
| Web title-ideas line (`Directions.tsx`): no test of its words | One assertion | `Directions.test.tsx` first test |
| **Hyphen check** | Confirmed on the test stack (real PostgreSQL 16.15): `SELECT plainto_tsquery('english', 'first-aid')` gives `'first-aid' & 'first' & 'aid'`, and "first-aid" reached nothing. Fix: a hyphen in a skill search is read as a space before the search (`taxonomy_store._skill_words`, used by `essential_skill_reach` and `essential_skill_reach_among`); thresholds and ranking unchanged. Disclosed in ADR 0007 decision 13 rule 1 and the docstrings. | `tests/integration/test_evaluation.py::test_a_hyphen_in_a_search_is_read_as_a_space` on the full release: RED (`assert 'provide first aid' in set()`), then GREEN with the same total, skill count, exactness and order as "first aid". All 19 discovery cases still pass (16 passed in that file). |

## 2. SW.4: session 2's findings and how the chapter applies them (commit `68c8b2f`)

The chapter is the origin's console: a 600 px glass panel beside the person's light (the W2A
reference's `.panel`), the world in view to its right on a wide screen, below it on a tablet,
and behind it as a backdrop on a phone. Its three views are ARIA tabs (arrow keys, Home, End).

| Finding (the product owner's words) | How the chapter applies it |
|---|---|
| "Chat should be immediate" | The reply field and Send are there from the first screen; the entry choice is the first question's two quick answers. Typing first is allowed (the API and interviewers accept a null entry). |
| "ditch the tone selection - this should be in preferences"; "Starts with How Nessa talks with you - this is a preference" | "How Careerwright talks with you" moved to the account menu (`ConversationTone`), beside calm mode; the same expected-version command. |
| "need minimum ideas per page"; "trying to do too much on one page" | One idea per view: Conversation, What we know, Suggestions. The two-column layout, the "What we know" jump link and "Both lead to the same plan chapters" are gone. |
| "The suggested jobs should pop out into it's own modal or be on a separate tab" | Their own tab. Within it, one suggestion is open at a time (edged as the selection); the rest are titles to scan. |
| "I found the button, but it did not stand out enough. Needs to be a bright colour" | The open suggestion's "Make this a target" is the view's one bright primary; so is "Suggest directions" before there are any (and Try again after a failed search, unless "Suggest again" is shown). |
| C3: "could be easier with colour coded buttons" (accept or undo) | Accept and Confirm in leaf green (filled once chosen), Undo in orchid, each after its words and a glyph (a plain tick, a turn back). New tokens, measured. |
| "total spending limit and monthly payment limit - what do these mean??" | Each limit's plain meaning beside it wherever shown: What we know, the tray, the answer form's hint. Labels kept. |

What a decision did is said where it was made: after saving the tray, "Saved to What we know"
with Undo appears right after the reply and takes focus; after Undo, "Save undone: your answers
are back as they were before it." takes focus; Keep none says "Nothing saved" (before, focus
was lost there). The world answers at the same time (the person's light, the destinations).

## 3. The strip and the key (carried from W2A)

- Plain words: "Answers saved" or "Nothing saved yet" (the version is in `data-version` for
  tests); live updates say nothing while they work (the announced status region stays); a state
  that isn't live names itself ("Updates: Reconnecting", "Updates: Stopped: sign in again").
  "Synthetic demo" shows at every width (top bar on a phone). `WorkspaceStrip.test.tsx`.
- Two rows on a tablet: the synthetic label and the target (one line, ellipsis), then the
  states and controls. The workspace switcher, work area and budget show from 1180 px (the
  account menu names the workspace and leads to the others; What we know holds the answers).
- The key check (`e2e/world.spec.ts`) now reads which shown names the key explains
  (`data-keyed`, every light but the person's), and a new test covers the empty-key case: a
  new workspace names only "You" at You and Roles, and no key is shown.
- The flaky phone strip test measures once the strip has settled: saved state and live
  updates in, fonts loaded, the same height two frames running (`settledHeight`); the
  assertion is unchanged (the strip keeps its height).

## 4. "Your world" names every light

The DOM list names each skill (with "usual in your role, not confirmed yet" or "you said
you've done it") and counts the openings in one line ("7 openings: small lights around the
places you chose"); the key lists said, usual and openings when drawn. `World.test.tsx` "names
every skill and counts the openings…". The app passes no skills or openings to the world yet
(part 2 and Roles do), so the canvas holds nothing unique when they arrive.

## Readings I chose where the record was unclear (for session W2)

1. "Chat should be immediate" read as the reply field from the first screen, not removing the
   sure or unsure choice (C1 said the start screen "makes sense" apart from the tone). Send is
   the start's one bright action; the two choices stay equal and quiet.
2. "In preferences" read as the account menu's settings (where calm mode already is).
3. "Its own modal or a separate tab": a tab (the record allows either; a tab keeps one
   persistent console).
4. "Bright colour" for choosing, with one primary per view: one suggestion open at a time,
   its choice bright. Scanning stays (C4 "easy to scan: yes"): every title is listed.
5. "Colour coded buttons": no meaning hue was free (orange, teal, the journey's blue and
   violet, crimson and sand all mean something), so two new semantic tokens, leaf green
   (`#A6E25A`) and orchid (`#FFAAFF`), chosen by measured distance from every other hue
   (ΔE76 ≥ 56 and ≥ 44). Recorded in ADR 0014 decision 5, provisional (R6).
6. Pause the interview is not mentioned by the record: kept, as a quiet action under the reply
   field. The stored key's details moved to the end of the conversation view.
7. The suggestions view keeps its count line and notes visible (they carry the slate's
   honesty: what found nothing, what a join kept, the salary floor); with a real slate they
   push the first suggestion down the first screen. Left for session W2 to judge.
8. "Version" stays in the answer form and the failed-reply alert ("unchanged at version N");
   only the strip and the new notices drop it (the carried item named the strip).

## Slots left for part 2

No visible placeholder was needed (and a "coming soon" card would be noise). The places in code:
- The first question and its type-ahead: the conversation view's question (`EntryChoice` is
  the first question today); `partial`'s words are in the OpenAPI description.
- The overlooked strength's proposal and confirm: `Conversation`'s `review` slot, right after
  the reply (where the tray and the save notice go). Never ask on a support turn (`held_back`).
- "Usual in your role, not confirmed yet" and the strength's destinations on the horizon: pass
  `skills` (and destinations) to the world input; the DOM list, captions and key already name
  them.
- The unexpected connection lit in the world, and a risk word holding back revelations: not
  touched.

## Design references (commit `5c14792`)

`docs/design`: the You console's tabs on every You page, and four new states at 1440×900,
768×1024 and 390×844: review, saved, known, suggestions (the gallery links them). The strip in
plain words. Tokens v0.2.2 with the decision colours, mirrored byte-identical to
`apps/web/src/design`. `contrast.mjs` also reports each decision hue's ΔE76 from every status,
meaning and other decision hue. Where the panels leave no room, the world is a backdrop
standing behind them (both trees: `world.js`, `geometry.ts`; `geometry.test.ts` "stands the
backdrop behind the panels…"), which a tall console on a tablet needed (a skill light peeked
out beside the panel with no room for its name).

## Contrast pairs added (8)

`--decision-accept` on `--surface-card` (text and non-text); `--text-on-decision` on
`--decision-accept`; `--decision-undo` on `--surface-reading` over the ground and white (text
and non-text) and on `--surface-card` (text and non-text); `--light-person` on
`--surface-reading` (the app key's said disc and opening dot). All pass.

## Checks run

On the final commit `6af1097` (tree unchanged during the runs; the test stack is down after):

| Command | Result |
|---|---|
| `make check` | exit 0: ruff format and lint clean, mypy clean (323 files), backend pytest 1,552 passed / 332 deselected, fixture validator passed; web: generated client matches OpenAPI, Biome clean (139 files), `tsc` clean, Vitest 36 files, 313 tests passed |
| `make acceptance` (none running before, checked with `pgrep`) | exit 0: integration and stack pytest 332 passed (8 min 28 s); Storybook build completed; Playwright 47 passed (6.2 min). Neither known flake occurred. |
| `pnpm --dir docs/design run contrast` | 131 of 131 measurements pass (99 pairs); smallest status/meaning ΔE76 53.0; smallest decision ΔE76 44.5 (orchid vs the journey's violet) |
| `pnpm --dir docs/design run screenshots` (runs `check-data`) | check-data 64 assertions pass; 43 of 43 captures pass |
| `cmp` tokens, and `designMirror.test.ts` | identical |

On the way:
- First `make acceptance` (on `68c8b2f`, `access.spec.ts` edited before its browser phase):
  pytest 332 passed; Playwright 44 passed, 3 failed: Storybook axe (`aria-valid-attr-value`:
  a closed suggestion's `aria-controls` pointed at details not in the page) and the visual
  package at 1440 and 390 (axe `target-size`: the floating reply field covered the tray's Save
  and the start's choices). Fixed in `6af1097`; rerun of those suites (Storybook, visual,
  conversation, access): 15 passed; then the final full run above.
- Focused browser run on `68c8b2f`'s working tree before commit (world, keyboard,
  conversation, session, journey): 32 passed, including every new test.

TDD evidence (RED then GREEN):
- Hyphen: `test_a_hyphen_in_a_search_is_read_as_a_space` RED on the test stack (`assert
  'provide first aid' in set()`; the database's parse `'first-aid' & 'first' & 'aid'`
  asserted), GREEN after `_skill_words`; `tests/integration/test_evaluation.py` 16 passed.
- Title idea: `test_a_title_idea_names_the_idea_and_says_careerwright_matched_it` RED (the old
  sentence), GREEN.
- Web: the four tests the rebuild changed failed first on the new code (strip live words, the
  sure person's "Help me explore instead", focus after save, the start's primary), then were
  updated to the intended behaviour (listed below); the new tests were written beside the code.
- Not shown failing first: the `_unmatched`, `_ambiguous`, empty-join and title-ideas word
  tests read lines W2B had already reworded (they pin the words; no RED exists). The geometry
  backdrop test fails on the old rule by construction (`clearArea` returned undefined).

Focused integration runs (real PostgreSQL 16.15): `test_origin.py`, `test_discovery.py`,
`test_provisional_concepts.py` 36 passed.

## Changed tests (disclosed)

- `YouChapter.test.tsx`: "asks first…" opens the Suggestions tab before "Help me explore
  instead"; the undo test expects focus on "Saved to What we know" and then "Save undone"
  (was "What we know"), the announcements' new words, and the accept and undo classes; the
  primary-action test expects Send at the entry (was none: chat is now immediate) and opens
  What we know before "Edit answers directly". New: the reply field at the start and no tone in
  the chapter; the views as tabs; the limits explained.
- `WorkspaceStrip.test.tsx`: live updates now say nothing (was "Updates: Live"). New: plain
  saved words and `data-version`.
- e2e: `liveUpdates(page, "Live")` reads the strip's `data-events`; the saved version comes
  from `data-version` (`saved`, `savedVersion`); journeys open the You views they use. The
  key check reads `data-keyed` (was any name). The phone strip test waits for the strip to
  settle. New: the empty key; the chapter's text identical in moving, reduced motion, calm and
  paused, in every view, at three sizes; keyboard-only completion with focus return; visual
  shots of what we know and a decided reply.
- `geometry.test.ts`: the no-room phone case now expects a backdrop `Clear` (was undefined);
  the view is unchanged. New: the backdrop stands behind the panels.
- `access.spec.ts`: the two-tab stale save opens What we know before "Edit answers directly".
- No assertion was weakened. The phone strip test's assertion is unchanged; only its
  measuring waits for the strip to settle.

## Requirement candidates for W2D

- The You chapter is one idea per view, as tabs; chat is immediate; the tone is a preference
  (`YouChapter.test.tsx` "has the reply field…", "opens on the conversation…";
  `ConversationTone.test.tsx`).
- Accept and undo are colour coded with measured decision tokens (`YouChapter.test.tsx` undo
  test; `contrast-report.md`).
- The limits are explained in plain words wherever shown (`YouChapter.test.tsx` "explains the
  two limits…").
- One bright primary per view, including the open suggestion (`Directions.test.tsx` "opens one
  suggestion at a time…", "makes asking for suggestions the bright action…").
- The strip speaks plainly (`WorkspaceStrip.test.tsx` "says what is saved in plain words…").
- The canvas holds nothing unique: skills named, openings counted (`World.test.tsx`).
- The key shows when a light it explains is named, never for the person's light alone
  (`e2e/world.spec.ts` "with no light the key explains…").
- The You chapter says the same in the moving and still world, every view, three sizes
  (`e2e/world.spec.ts`).
- The You chapter completes from the keyboard, focus returning to what each step did
  (`e2e/keyboard.spec.ts`).
- With no room, the world stands behind the panels (`geometry.test.ts`).
- A hyphen in a skill search is read as a space (`test_evaluation.py`; DIV1 family).

## Not run, requires human

Session W2's design scores; whether leaf green and orchid read as "accept" and "undo" to the
product owner; the chapter's feel ("a world answering the person"); VoiceOver; Safari; frame
measurement (W2D, after warning the product owner). No live calls: cost $0.

## Concerns

1. On a phone, the start's console (tabs, the two choices with their lines, the reply field)
   is tall enough that the person's light sits under it; the world shows only above. Part 2's
   first moment ("the origin ignites") will want a shorter first view there.
2. With a real slate, the suggestions view's count line and notes come before the first
   suggestion (kept visible: they carry what found nothing and what was left out). Session W2
   should judge the density.
3. The reply field no longer floats at the bottom of the window (it covered buttons in the
   narrower console); it sits under the question. A long conversation shows its last two turns,
   so it stays near, but it is a change from Sprint 2's sticky field.
4. "Version" remains in the answer form and the failed-reply alert, outside the strip.
5. Provisional (R6) for session W2: the two decision colours, the tabs, Send as the start's
   bright action, and the account menu as "preferences".

## Paths a reviewer can skip

- `apps/web/src/generated/**` (regenerated by `pnpm run generate`)
- `docs/design/screenshots/*.png`, `docs/design/screenshots/checks.md`,
  `docs/design/tokens/contrast-report.md` (generated by the tools)
- `apps/web/src/design/tokens/tokens.css` (byte-identical mirror)

---

# Fix round 1

Implementer: Claude (Opus 5.5), fresh. Dispatch `task-W2C1-fix-round-1.md`; findings from
`task-W2C1-review-design.md` (D) and `task-W2C1-review-app.md` (A). No subagents, no live model
call (cost $0), no web request, no headed browser, no frame measurement, no Docker pull;
`spikes/world`, the running `careerwright-l0-*` stack, `answers-2.md`, `.env` and
`~/.careerwright` untouched. DBOS `application_version` still `careerwright-l0-1` (no backend
step changed).

## Commits

| SHA | Subject (shortened) |
|---|---|
| `d3a9164` | The truth words: three API descriptions and the sketch's unmatched title say what the match did; the hyphen's exactness disclosed |
| `c798ea4` | The design references: What we know whole again, Routes and Plan restored, a clipped-text check, the light above the console on tablet and phone, a real slate, a chosen Accept on a faint tint |
| `ec5ec8e` | The You chapter: views stay mounted, one decision at a time, notes one step away and the choice up the card, the light above the console, focus kept, plain words, fewer helper lines |
| `f179d0f` | Acceptance fixes: a menu longer than the window scrolls inside it; the keyboard journey names the suggestion's header exactly |

`f179d0f` came from the first `make acceptance` (below). One part of it is outside the
findings, disclosed: the workspace menu had no height limit, so with 19 workspaces (the new
keyboard test made the nineteenth) it ran past the bottom of a 900 px window and its last items,
"All workspaces" among them, could not be reached; `world.spec.ts` "the menus open over the key"
caught it. `.popover` now has `max-height: var(--radix-popover-content-available-height)` and
scrolls. No test was changed for it.

## What changed, finding by finding

**D-I1 (the `.facts` collision).** The new rules are `.known-facts` (`world.css`, `world.js`
known state); Routes and Plan use the old `.facts` alone again. Every affected reference was
recaptured (`you--known` ×3, `routes--default` ×3, `routes--failed`, `plan--default` ×3, and every
You state). `screenshots.mjs` gained a clipped-text check: a text's box must stay inside every
box that clips it, up to its panel, and a text that clips itself must show all its words (text
for assistive tech only and text in a closed disclosure are skipped). RED: with HEAD's
`world.css`/`world.js` and the new tool, `you--known` fails at all three sizes ("Target roles
passes the edge of a box that clips it", …); GREEN after: 43/43.

**D-I2 (the world on tablet and phone).** Below 968 px (the rail's 96 + margin 32 + console 600 +
`MIN_CLEAR` 240) the console starts below a band of world, `max(300px, 34vh)`, in every view, in
the app (`globals.css`, `.workarea:has(> .chapter-you)`) and the references (`.work:has(>
.console)`); a short console sits low (`margin-top: auto`), a long one scrolls with the page. On a
phone the console's own "You" title is visually hidden (the top bar names the chapter). 256 px
was tried first: at 768 and 390 one or two of the reference's five skills went unnamed; 300 px
still left one at 768; `max(300px, 34vh)` names every light. The reference's console is now
600 px wide, like the app's (was 560). Tests: `screenshots.mjs` now fails a You state at 768 or
390 if the world falls back to a backdrop (`__worldCheck.backdrop`, i.e. a band under
`MIN_BAND`) or "You" is not named (RED on HEAD's references: 7 You captures fail; GREEN 43/43);
`e2e/world.spec.ts` "the person's light stands above the You console in every view" (768 and
390): measures the band from the bars to the panel, `>= 240`, and "You" named, in each view.

**D-I3 (the suggestions view).** The count line stays; every `fewer_reasons`, note, salary-floor
and AI-filter line, the unmatched-titles line and the "doesn't know your current work" line now
sit in one disclosure, "How Careerwright searched (n notes)", each with its words. In the open
card, "Make this a target", "Not for me", "Exclude this kind of work" and "Source" come right
after the title and kind of work; the details follow, visible (nothing about what might not suit
is folded away). The reference's suggestions state is redrawn from the "data analyst" slate
(W2B's DSC-10: its six titles, its two notes' words; counts and the open card's lines labelled
as examples): the five view controls, the count line, the notes disclosure, three group
headings, one open card with its choice up the card. At 1440 × 900 the bright action sits at
y ≈ 716. Tests: `Directions.test.tsx` (notes behind the disclosure, visible once opened; the
choice precedes "Why this could suit you").

**D-I4 (one decision at a time).** While the tray is the view's decision (`primary ===
"review"`), the next question is held back; after the decision it appears under the save notice.
Tests: `YouChapter.test.tsx` "asks the next question only once the tray is decided…" (RED on the
old component), the tray test (no question while it waits), `e2e/conversation.spec.ts`
(`.question` count 0 while reviewing, 1 after saving).

**D-I5 (helper text).** Every helper line in the chapter, cut or kept:

| Where | Line | Now | Why |
|---|---|---|---|
| Start | The two glosses under "I know my direction" / "Help me explore" | Cut (`ENTRY_MODE` is labels only) | Procedural; the choices name themselves |
| Conversation | "Answer in your own words, or say Skip, Unknown or Prefer not to say." | Folded: once, under the first question only | Said once at the start, not under every question |
| Conversation | Paused: "Nothing is asked and nothing can be sent until you resume. Everything you have said and saved is kept." | Kept | Truth about a state (nothing lost) |
| Conversation | Failed reply: the failure's action, "What we know is unchanged. Your message is kept above." | Kept, "at version N" dropped | Failure is never a success |
| Conversation | "Demo interviewer: synthetic answers from fixed patterns, not a model." | Kept | Synthetic label |
| Conversation | Send's reasons ("Paused: resume to send.", "Careerwright is still replying.", "Sending…") | Kept | A disabled button says why |
| Conversation | Reply states ("Writing a reply, not checked yet", "Stopped: not checked, nothing saved") | Kept | Provisional versus checked |
| Conversation | The key's consent bullets and "Not now? You can still edit your answers directly…" | Kept | Consent to storing a key needs them; what works without a key is a gate in plain words |
| Tray | "A limit or target: needs your confirmation." | Cut | Procedural; the Confirm button names the limit |
| Tray | "You said" / "Careerwright's reading, not a fact until you accept it" | Kept | Truth statement |
| Tray | A limit's meaning | Kept | Session 2 asked for it |
| Tray | "Accept, confirm or edit at least one first." | Kept | A disabled button says why |
| Tray | "Skipped changes are not saved. Every saved answer keeps where it came from; an answer you edit is saved as yours." | Cut | Procedural; provenance is one step away under Source |
| Tray, Source | "Saving creates profile version N. Nothing changes until you save." | Cut | Procedural, and "version" |
| Tray, Source | "You said this; not verified" / reading, the message, "Why: …" | Kept | Reason one step away |
| Tray, stale | "Your answers changed after you sent …, so its n proposed changes can't be applied…" | Kept | A stale state and the one way on |
| Notices | "Nothing saved: You kept none of the changes." / "Save undone: Your answers are back…" | Kept | What the decision did |
| What we know | Both limits' meanings; "Not asked yet" list; "Nothing saved yet." | Kept | Asked for; unknown shown, never blank |
| What we know | The early sketch | Folded behind "The early sketch for your target" (D-M6) | A second idea |
| Answer form | "Version N, with unsaved changes" | "Unsaved changes", only while there are some | Plain words (D-M5) |
| Answer form | "Saving makes a new version." | Cut | Procedural, and "version" |
| Answer form | "Unknown, Skipped and Prefer not to say are answers too." | Kept | Unknown is an answer, never a blank |
| Answer form | Each field's hint; "Less precise without it: …" | Kept | Each defines its answer or states a rule (privacy, list limits, the salary floor's rule, the three evidence kinds) or a consequence |
| Answer form | Stale-save notices and conflict lines | Kept, without version numbers | Failure and conflict |
| Suggestions | "Up to six occupations from ESCO, found from your own answers and chosen to differ from each other. They are ideas to test, not a judgement of fit: no score or percentage." | Shortened: "Occupations from ESCO, found from your own answers. Ideas to test, not a judgement of fit: no score or percentage." | Kept the truth statement, cut the procedure (the count line says "up to 6") |
| Suggestions | Count line | Kept | What the search found |
| Suggestions | Notes, fewer reasons, salary floor, AI filter, unmatched titles, familiarity unknown | Folded into "How Careerwright searched (n notes)" | One step away (D-I3) |
| Suggestions | Note recovery alert, the written note's provenance, "not covered" line | Kept | Failure says why; what was checked |
| Suggestions | Card details (workday, why, what might not suit, try it, evidence gaps) | Kept | REC-1's content |
| Suggestions | "You know your direction, so suggestions are optional." and the disabled reasons | Kept | Why the view is empty; why a button can't act |
| Suggestions | "Based on your answers at version N" | "Based on your earlier answers" | Plain words (D-M5) |

For session W2 to judge: the result as a reading of "Helper text appears only where it helps".

**A-I1 with A-M2 (nothing typed is lost).** The three views are always mounted, the inactive ones
`hidden`; each tab's `aria-controls` always points at its panel. The save notice has one copy
per view with its own heading ref, and focus goes to the copy in the view shown. The slate asks
for its written note only once the person can see it (`shown`, the Suggestions view open), and
every request for a discovery's note is kept in the query client for the page's life
(`useNoteRequests`: a mutation key with `gcTime: Infinity`, read with `useMutationState`), so a
view change or a change of chapter never asks again, the refusal is still shown when the slate
returns, and only the person's click sends it again. Tests: `YouChapter.test.tsx` "keeps a typed
reply, the tray's choices, the answer form's edits and the slate's picks" (RED on the old
`YouChapter.tsx`: the reply came back empty); `Directions.test.tsx` "asks only once the person
can see the slate" and "never sends a refused request again when the slate shows again, only by
a click" (both RED on the old code: 1 request where 0 expected; 2 where 1 expected).

**A-I2 (focus after "Add the details yourself").** It opens What we know, the answer form, and
moves focus to the form's heading ("Edit your answers", `tabIndex=-1`, via `headingRef`). Tests:
`YouChapter.test.tsx` "moves focus to the answer form…" (RED on the old component),
`e2e/conversation.spec.ts` phone journey asserts the heading is focused.

**A-I3 and the sketch's `not_found`.** `ProvisionalConceptOut`, `close_matches` and `RoleOut` say
what Careerwright's match did; client regenerated (`pnpm run generate`). `RESOLUTION.not_found`
is "Careerwright couldn't match it in ESCO". Test: `SketchCard.test.tsx` adds a `not_found` title
and forbids "Not found in ESCO" (RED on the old word, GREEN after).

**Minors.**
- D-M1: a chosen Accept or Confirm sits on a faint leaf tint (`--surface-decision-chosen`, leaf at
  16 % over the card) with a doubled edge, never a solid fill. `--text-on-decision` is gone
  (nothing used it); tokens v0.2.3, mirrored byte-identical. The one-primary checks now count by
  computed fill (the primary's sea-glass and both decision colours), not by class:
  `screenshots.mjs` ("Bright fills") and `e2e/helpers.ts` `brightFills`, asserted in
  `conversation.spec.ts` with four proposals chosen (1).
- D-M2: no teal edge on a chosen proposal (app and reference; `data-chosen` removed).
- D-M4: the tone shows "Keep this practical (the default)" while unset, says "Saved." after a
  save, under a "Preferences for this workspace" heading. Calm mode is this viewer's (browser
  storage), so it sits above that heading, not under it (`ConversationTone.test.tsx`).
- D-M5: no "version" on screen in the chapter: the failed-reply alert, the stale discovery, the
  answer form and its stale-save notices, the tray's Source sheet (`ProfileEditor.test.tsx` and
  `YouChapter.test.tsx` assert no "version" text). The strip's `data-version` keeps the number
  for tests.
- D-M6: the early sketch is behind "The early sketch for your target" in What we know.
- A-M1: on a phone the update state's words take the room left and end in an ellipsis
  (assistive tech reads them all), so the strip stays one row; a failed refresh takes a row of
  its own. `conversation.spec.ts` V-08 test now also runs at 390 × 844 (reconnecting equals live).
- A-M3: the open suggestion's header is `aria-disabled="true"` and does nothing
  (`Directions.test.tsx`).
- A-M4: the tray's limit meaning is asserted (`YouChapter.test.tsx` "explains the two limits…");
  the keyboard journey now opens a suggestion and makes it a target (`keyboard.spec.ts` "a
  suggestion opens and becomes a target from the keyboard"; `talkedWorkspace` moved to
  `e2e/api.ts` for it); the moving/still identical-text test still runs on the fixture
  workspace's states only, so its requirement candidate is narrowed (below).
- A-M5: the docstrings (`taxonomy_store._skill_words`, `essential_skill_reach`) and ADR 0007
  decision 13 rule 1 say that a hyphenated skill name typed with its hyphen no longer counts as
  exact; ranking unchanged.
- A-M7: while paused, "Resume the interview" is the view's primary, in the Paused section; Send is
  secondary; "Pause the interview" stays quiet under the reply field. Focus moves with the
  change ("Paused", then the question or the reply field) (`YouChapter.test.tsx` "makes Resume
  the one primary action while paused…", RED on the old component).

Not fixed, by ruling: D-M7 (carried to part 2); D-M3 and A-M6 (to session W2's sheet).

## Rulings I made

1. The slate's note is asked for once the Suggestions view is open, not on chapter load (the
   views are now mounted hidden; "when the slate first shows" read literally). A page reload
   starts a new query client, so a request refused with no run is asked again after a reload, as
   before.
2. While paused, Resume is primary even over a pending tray's Save (the review's words: "while
   paused, make Resume the view's primary").
3. D-M5 covers the answer form too (the reviewer's M5 names reading 8, which included it).
4. D-I3: the card's details follow the actions, visible, rather than in a "More about this"
   disclosure, so nothing about what might not suit is one step further away than the reasons
   for.
5. The band is `max(300px, 34vh)`, not a bare `MIN_BAND` + margin, because the reference's five
   skills need it to be named (above).

## Disclosed test changes (inputs and assertions)

- `YouChapter.test.tsx`: tabs test, the hidden reply field is `not.toBeVisible()` (was
  `toBeNull()`: views stay mounted), plus each tab controls its panel; "shows only the checked
  reply…", the turn is now decided (the question waits for an undecided tray), plus "said once";
  the tray test, `/needs your confirmation/` is now absent (was visible), plus the reading line,
  Save's reason and no question; failed reply, "unchanged at version 1" became "unchanged." and
  no "version"; the primary-count tests count only the view shown; "explains the two limits…"
  adds a tray turn and two tray assertions. Four new tests.
- `Directions.test.tsx`: three tests open the notes disclosure before reading a note; the
  one-at-a-time test adds the order and `aria-disabled` assertions. Two new tests.
- `ProfileEditor.test.tsx`: the version words became plain words ("Saved.", "Your answers changed
  while you were editing", "The newer answers changed: …", "The newer answers have £900 here…",
  "…and the newer ones couldn't be loaded"); one test renamed ("…and says it is saved"); added
  "no version" and "Unsaved changes" assertions. The PUT bodies' `expected_version` assertions
  are unchanged.
- `ConversationTone.test.tsx`: "Choose a tone" became "Keep this practical (the default)"; heading
  and "Saved." added.
- `SketchCard.test.tsx`: a third, unmatched title and its words.
- e2e: `access.spec.ts` and `journey.spec.ts` read "Saved." in the form and the strip's
  `data-version` (was "Saved as version N."), and the stale notice's new words; `visual.spec.ts`
  the stale words; `conversation.spec.ts` the "needs your confirmation" check is replaced by the
  held-question and bright-fill checks, `main .btn-primary` counts `:visible` only, the sketch is
  opened from its disclosure, focus after "Add the details yourself" asserted, and the V-08
  strip test runs at 390 too; new tests in `keyboard.spec.ts` and `world.spec.ts`.
- `States.stories.tsx`: the stale story's words.
- No assertion was weakened: each change follows an intended behaviour change listed above.

## Checks run

On the final tree (`f179d0f`):

| Command | Result |
|---|---|
| `make check` | pass: ruff format and lint clean, mypy clean (323 files), backend pytest 1,552 passed / 332 deselected, fixture validator passed; web: client matches OpenAPI, Biome clean (139 files), `tsc` clean, Vitest 36 files, 319 tests passed |
| `make acceptance`, run 2 (none running before, `pgrep`) | exit 0: integration and stack pytest 332 passed (9 min 15 s); Storybook build completed; Playwright 50 passed (6.6 min). The durable-runs shutdown hang did not occur |
| `cd docs/design && pnpm run contrast` | 132 of 132 measurements pass (100 pairs); smallest decision ΔE76 44.5 |
| `cd docs/design && pnpm run screenshots` | check-data 64 assertions pass; 43 of 43 captures pass with the new clipped-text, light-above-the-console and bright-fill checks |
| `cmp` tokens and the mirror; `designMirror.test.ts` | identical |

On the way:
- `make acceptance` run 1 (on `ec5ec8e`): pytest 332 passed, Storybook built, Playwright 48
  passed, 2 failed: `keyboard.spec.ts` (my new test: the open card's header name also matched
  "Make this a target : Pesticides sprayer" and two more; now `exact: true`) and `world.spec.ts`
  "the menus open over the key to the lights" (the workspace menu overflow above). Both fixed in
  `f179d0f`, then run 2 passed in full.
- RED runs (old code, new tests): `SketchCard.test.tsx` (the "Not found in ESCO" words);
  `Directions.test.tsx` "asks only once…" (1 request, 0 expected), "never sends a refused
  request again…" (2, 1 expected) and the accordion test; `YouChapter.test.tsx` with the old
  `YouChapter.tsx` only: "keeps a typed reply…" (the reply came back empty), "moves focus to the
  answer form…" (not focused), "makes Resume the one primary…"; with all old components, "asks
  the next question only once the tray is decided…" (the question was there). The reference
  tool with HEAD's `world.css`/`world.js`: 8 of 18 You captures passed (the known state clipped
  at all three sizes; I printed only those three failures' reasons, the other seven are 768 and
  390 captures, where the new light-above-the-console check applies).

## Requirement candidates for W2D (changes to the list above)

- New: moving between the You chapter's views keeps what the person typed or chose
  (`YouChapter.test.tsx` "keeps a typed reply…").
- New: on a tablet and a phone the person's light stands above the You console in every view
  (`e2e/world.spec.ts`; `screenshots.mjs`).
- New: one decision at a time: the next question waits for the tray (`YouChapter.test.tsx`).
- Narrowed: "The You chapter says the same in the moving and still world, every view, three
  sizes" holds for the fixture workspace's states (no tray, no slate) (`e2e/world.spec.ts`).
- Register rows updated: STATE-06 (tint, the tray's limit meaning, the held question) and UI-06
  (keyboard to a target, focus after "Add the details yourself", nothing lost between views).

## Not run, requires human

Session W2's scores; whether the faint leaf tint reads as "chosen"; the helper-text result;
the chapter's feel; VoiceOver; Safari; frame measurement (W2D).

## Concerns

1. On a phone the band of world takes about 300 px, so a long view (the tray, the suggestions)
   starts lower and its first decision is a scroll away. That is the ruling's trade (the light
   in every view); session W2 should see it.
2. The chosen Accept is now told from an unchosen one by a faint tint and a doubled edge, not a
   solid fill. Whether that reads as "chosen" is for session W2.
3. "Help me explore instead" (a sure person, Suggestions) still drops focus when the view
   changes beneath it: older than W2C, named by the app review, not in this round's list.
4. The keyboard test reaches a target from the slate of the e2e ESCO sample; the
   identical-text test still compares only the fixture workspace (no tray, no slate), and its
   requirement candidate says so.
5. `docs/plan/l0-sprint-tasks.md` shows as modified in the working tree; I did not change it and
   did not stage it.

## Paths a reviewer can skip (this round)

- `apps/web/src/generated/**` (regenerated)
- `docs/design/screenshots/*.png`, `docs/design/screenshots/checks.md`,
  `docs/design/tokens/contrast-report.md` (generated)
- `apps/web/src/design/tokens/tokens.css` (byte-identical mirror)
