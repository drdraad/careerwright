# Task W2C part 1 review, Half A: design and experience

Reviewer: Claude (Opus 5.5), read-only. Range 166e4ef..6af1097 (92ea74f, 5c14792, 68c8b2f, 6af1097).

How I reviewed:
- I read the dispatch, the contract, the implementer's dispatch, the carry-forward and the report. Then I read the diff in passes: the design half (lines 5301–6237), the app chapter (globals.css, Conversation, Directions, ReviewTray, WhatWeKnow, YouChapter, ConversationTone, WorkspaceStrip, World, geometry) and the stories.
- I looked at every new and changed You reference in `docs/design/screenshots/`. I compared some with their 166e4ef versions, extracted to my scratchpad.
- I looked at the app's own captures from the final acceptance run, in `apps/web/test-results/visual-*/screenshots/`. They were written at 06:47–06:52, after 6af1097 was committed at 06:37.
- I checked the mirror with `cmp`: tokens and both fonts are identical.
- I recomputed one unrecorded pairing's contrast, and ran a rough colour-vision simulation of the new hues, in my scratchpad.
- I ran no test suite. I did not run `pnpm run contrast`, because it rewrites a tracked file.

## Spec Compliance

❌ Issues found:
- **The "What we know" reference is broken at all three sizes.** A CSS class collision causes it, and the same collision regresses the Routes and Plan references (I1, `docs/design/compositions/world.css:777` against `:926`).
- **One session 2 finding is missing.** The product owner said "too much helper text that isn't actually helpful because the cognitive load s too high". Plan section 4 says "Helper text appears only where it helps". The chapter does not apply this, and the report does not mention it (I5).
- **"One idea per view" is only partly applied.** The app's review view shows the tray and the next question together, and the reference shows only the tray (I4). "What we know" also carries the early sketch (M6).
- **The bright primary and "never overwhelming" are undercut in the suggestions view.** The bright action sits below the fold at 1440 × 900, under notes and a card of about 25 lines (I3).
- **On a tablet and a phone the You place loses its world (I2).**

Applied as recorded:
- Chat is immediate: the reply field and Send show from the first screen.
- The tone moved to the account menu.
- The suggestions have their own tab.
- Each view has one `.btn-primary`.
- Accept and undo are colour coded, and every pairing they use is in `contrast-pairs.json` and measured.
- Both limits are explained in What we know and in the tray.
- The strip uses plain words, has two rows at tablet width, and shows "Synthetic demo" at every width.
- The mirror is byte-identical.

ADR 0014 decision 5's addition records the two hues as provisional (R6). No human-only gate is claimed as passed: the report and README mark session W2, the hues' reading, the chapter's feel, VoiceOver, Safari and frames as "requires human".

⚠️ Cannot verify from diff (requires a human, session W2):
- whether the chapter feels like a world answering the person;
- whether leaf green and orchid read as accept and undo;
- the moving world's version of these views (every capture I saw is the still world);
- VoiceOver and Safari.

## Strengths

- At 1440 × 900 the console is a real glass panel at the origin. The person's light and their destination sit beside it, and the first view is calm: one question, a reply field, one bright Send. This is a clear step up from session 2's "mess of different things" (`you--1440x900.png`, app).
- The colour work is careful:
  - Two new semantic tokens, never primitives, each after its words and a glyph.
  - ΔE from every other hue is reported by the tool (`contrast.mjs:138-145`).
  - All 8 new pairings are measured on card and on glass, over the darkest ground and the brightest light.
  - Quiet actions stay white.
  - Teal is used only for the tab selection, chosen proposals, the open suggestion and the one primary.
- What a decision did is said where it was made, and focus moves to it: "Saved to What we know" with an orchid "Undo the last save". The notice is clean in both the reference and the app.
- The strip's plain words are good: "Answers saved", silent while updates are live, and the state named when they are not.
- The limits' explanations are plain and accurate ("Pay you'd give up while you train isn't part of it").

## Issues

### Critical

None.

### Important

**I1. A CSS class collision breaks the "What we know" reference and regresses the Routes and Plan references, and the checks pass it.**

Where: `docs/design/compositions/world.css:777-803` adds `.facts`, `.facts > div`, `.facts dt` and `.facts dd`. The older `.facts` at `world.css:926-940` comes later in the file, so it wins on `display`, `grid-template-columns: max-content minmax(0,1fr)` and `gap`.

What breaks in the You "known" state (`world.js:652`):
- The four `<div>` rows become cells of a two-column grid. The first column is as wide as the spending limit's explanation on one line.
- `overflow: hidden` then clips everything to its right.
- `you--known--1440x900.png`, `--768x1024` and `--390x844` show "Target roles" with no value, no "Work areas", no "Monthly payment limit", and the spending limit's plain-words explanation cut mid-word ("course fees, exams, equ"). Below it is a tall empty box.
- This is the reference that documents SW.4's "limits explained in plain words".

What breaks in Routes and Plan:
- The new border, radius, `--line-reading-hairline` (#26324F) background and bold `dd` now also style the Routes facts (`world.js:749`) and the Plan facts (`world.js:764`).
- `routes--default` (3 sizes), `routes--failed` and `plan--default` (3 sizes) now show a slate block with the text flush to its edges. Compare `plan--default--1440x900.png` with 166e4ef.
- These are places outside this slice's scope.
- The text-on-#26324F pairing is in no pairs file. By my computation it is 7.89:1 and 11.75:1, so it passes, but it is unrecorded.

`checks.md` reports all of these captures as passing with "none" problems. No check looks for clipped text.

Fix:
1. Rename the new rules, for example `.known-facts` (or scope them as `.view .facts`).
2. Recapture, and look at each PNG.
3. Add one check to `screenshots.mjs`: any text element inside a `.panel` whose `scrollWidth > clientWidth`, or whose box passes its panel's right edge, is a failure.

**I2. On a tablet and a phone the You place loses its world (the implementer's concern 1, and more).**

The reference's phone default went from 7 names placed to 1 (`checks.md:11`):
- Before: the person's light, five skills, the target and the key.
- Now: only "Data quality analyst" shows above the console, and the person's light is under it (`you--default--390x844.png`).
- The panel still says "Records officers usually need these skills. Pick any you've used, and it lights up", about skills the person cannot see.

The cause:
- The new tabs make the console about 56 px taller.
- That shrinks the band above it below `MIN_BAND` (240 px, `apps/web/src/lib/world/geometry.ts:78`).
- So the new backdrop rule takes over (`geometry.ts:119-126`; `world.js:140`).

The app does the same. In `you--390x844.png` (app), only the target's light shows above the console, and "You" is hidden.

On a tablet:
- The review, known and suggestions references place 0 names (`checks.md`).
- The app's tablet review, What we know and suggestions captures show no world at all.
- So in three of four views at 768 the chapter is a form over a dark backdrop. The You place is "the origin: the person's light" (plan section 4), and it is not in view.

Fix:
- On a phone, the top bar already names the chapter "You". Make the console's own "You" heading visually hidden there (keep it for assistive tech), or fold it into the tab row. That gives back about 60 px, so the band clears 240 px and the light and its trails show again.
- On a tablet, keep a world band of at least `MIN_BAND` above the console in every view: the console starts below the band and scrolls with the page, rather than standing in front of the world.
- Recapture `you--default--390x844` and the three tablet states. Add a screenshot check that fails when the You place shows no "You" name at 768 or 390 in its default view.

**I3. In the suggestions view the bright action sits below the fold, under notes and a long card, and the reference draws a calmer view than the app builds (the implementer's concern 2).**

Before the first title (`apps/web/src/components/Directions.tsx:552-613`), the person sees:
- the heading and a two-line helper;
- three emphasis buttons and the count line;
- every `fewer_reasons`, `notes`, salary-floor and AI-filter line as its own paragraph (`:577-586`);
- any note-recovery alert;
- a group heading.

The open card then holds, in order:
- the workday text, about five lines;
- "Why this could suit you", with the written note and its provenance;
- "How Careerwright found it";
- "What might not suit you";
- "Try it before committing";
- the evidence gaps;
- and only then the four actions (`:298-363`).

In the app's 1440 × 900 capture (`you--slate-note-unavailable--1440x900.png`), the card runs from y≈290 to beyond 900 before its actions. So "Make this a target" is off screen even with the card at the top, and narrower widths are taller. Session 2's complaint was "I found the button, but it did not stand out enough". It is now bright, but it is not in view.

The reference (`world.js` "suggestions" state) shows none of this: no controls, no notes, and a three-line open card. That draws the attractive fixture only. Plan section 5 says "Never approve only the attractive fixture", so session W2 would score a calmer screen than the one built.

Fix:
1. Keep the count line. Fold the notes into one disclosure under it, "How Careerwright searched (n notes)". Each note keeps its words one step away; nothing is dropped, and none reads as "none found".
2. In the open card, put "Make this a target", "Not for me" and the one-line "why" right after the title and kind of work. The detail sections follow below, or sit in a "More about this" disclosure.
3. Redraw the reference with a real slate's controls and notes, so session W2 sees what ships.

If the controller prefers to leave the layout to the product owner, capture both versions for session W2. Do not ship only the calm reference.

**I4. The review view holds two ideas at once in the app, and the reference shows one.**

`Conversation.tsx:345-370` renders the tray (`review`), then the next question with its helper, then the reply field.

With a reply to review, the app's view (`you--reply-to-review--1440x900.png`, `--768x1024`) holds:
- your message and the reply;
- the tray heading;
- two proposals with four actions each, two kind lines and a limit explanation;
- Save, its reason and Keep none;
- a helper paragraph;
- then the next question ("Do you have a role in mind, or would you like to explore?"), its helper, the reply field, Send, "Pause the interview" and the demo note.

That is about 14 controls and two decisions in one view, at 1440, 768 and 390. Plan section 4 says each view has "one question or decision". The reference `review` state (`world.js` "review") shows only the tray and the reply field, so the reference and the app disagree.

Fix: while a tray is pending (`primary === "review"`), hold the next question back until the tray is decided. It then appears under the save notice, as the `saved` reference already draws it. The reply field can stay, as the quiet secondary it already is. This also shortens the distance to the field (concern 3).

**I5. Session 2's "too much helper text" finding is not applied, and the report does not list it.**

The record ("Looks like one product", desktop 3): "Generally there is too much helper text that isn't actually helpful because the cognitive load s too high." Plan section 4: "Helper text appears only where it helps."

The rebuilt chapter adds the limit explanations, which were asked for. It also keeps:
- every procedural line: "Accept, confirm or edit at least one first." (`ReviewTray.tsx:281`) and "Skipped changes are not saved. Every saved answer keeps where it came from; an answer you edit is saved as yours." (`:303`);
- "Answer in your own words, or say Skip, Unknown or Prefer not to say." under every question (`Conversation.tsx:366`);
- the two-bullet gloss of the entry choices (`vocabulary.ts:210-214`);
- "A limit or target: needs your confirmation." on each proposal (`ReviewTray.tsx:47`).

The report's "Readings" section does not mention the finding.

Fix: go through each helper line.
- Keep the lines an invariant needs: the synthetic labels, "Careerwright's reading, not a fact until you accept it", "not a judgement of fit: no score or percentage", and the limit meanings.
- Cut or fold the procedural ones. Say "Skip, Unknown or Prefer not to say" once at the start, not under every question. The "at least one first" reason can stay, because disabled buttons must say why.
- List the result for session W2 as a reading.

### Minor

**M1. Bright fills compete with the one primary.**
- A chosen Confirm is a solid leaf-green fill (`globals.css:653-656`; `world.css:761-764`). Leaf green is as light and saturated as the bright teal.
- With one or two limits confirmed, the tray shows two or three bright fills next to the bright teal Save (`you--review--1440x900.png`).
- The "at most one filled primary" check counts `.btn-primary` only (`docs/design/tools/screenshots.mjs:166`), so it misses this.
- Fix: once chosen, show the leaf button as a leaf border and text on a faint leaf tint, with a tick ("Confirmed"). Measure the new pairing. Or count `.btn-accept[aria-pressed="true"]` as a bright fill in the check.

**M2. A chosen proposal is marked twice in two hues.** It gets the teal selection edge (`globals.css` `.proposal[data-chosen="true"]`) and the leaf fill. Consider dropping the teal edge on proposals now that the fill says the same thing. That keeps teal for selection among alternatives and the one primary.

**M3. Leaf green is close to destination orange for some colour-blind people.**
- This is a rough Viénot simulation in my scratchpad, not a validated tool.
- Leaf and destination orange: ΔE ≈ 15 for deuteranopia and ≈ 21 for protanopia, against 75 for typical vision.
- `contrast.mjs` measures only typical vision.
- Words and a glyph carry the meaning, so this is Minor.
- Fix: add colour-blind-simulated ΔE rows to the decision table. Session W2 can then judge whether the hue needs to move.

**M4. The tone setting misstates the current tone.**
- `ConversationTone.tsx:38-41` shows a disabled "Choose a tone" while the saved tone is null. The interviewer is using Practical in that case (`backend/src/careerwright/profile/preferences.py:78`).
- Saving shows no confirmation.
- The menu never uses the product owner's word "preferences", and it does not say the tone applies to this workspace only.
- Fix: show "Practical (the default)" while it is unset. Add a small "Preferences for this workspace" heading above the tone and calm mode.

**M5. "Version" is still on screen (the implementer's reading 8).**
- "What we know is unchanged at version N" (`Conversation.tsx:339-340`).
- "Based on your answers at version N" (`Directions.tsx:711`).
- The same plain-words rule applies. Say "What we know is unchanged" and "Based on your earlier answers".

**M6. "What we know" also holds the early sketch** (`YouChapter.tsx:313`). That is a second idea, a route sketch for the target, in a view meant for one. Fix: move it to the Suggestions view under the target, or behind a disclosure, or list it for session W2.

**M7. The world does not answer most of the chapter's decisions, and the report lists no slot for this.**
- Confirming a limit, saving, undo and switching views leave the world unchanged.
- In the suggestions view the world shows only "You" (app captures): no suggested destination is drawn as a ring, although README's colour table defines "one suggested (ring)".
- Opening a suggestion, which is a selection in the list, has no counterpart in the world.
- "Make this a target" commits with no preview. CLAUDE.md says "Decisions show their consequences before they are confirmed".
- Not this slice's card, but it is the gap between this chapter and "a world answering the person". Fix: record it as a part 2 slot, so the slate's suggestions appear as rings with the open one singled out, and a target proposal previews its destination before saving.

**M8. The reply field now sits in the flow (the implementer's concern 3).** Accept the change: the sticky field caused real `target-size` failures. With the last two turns shown and focus going to the save notice just above the next question, it stays close. No change is needed beyond I4.

**For Half B (read across the line).** The app's "What we know" sketch shows "Data quality analyst: Not found in ESCO" (`apps/web/src/lib/vocabulary.ts:450`). Its sibling `provisional` was reworded to say what the match did; `not_found` still reads as a claim about ESCO. Please judge it against the round 5 rule.

## Never overwhelming: what competes in each view

Counted from the app's final captures (still world), first screen. "World" is what the world names in view.

| View | 1440 × 900 | 768 × 1024 | 390 × 844 |
|---|---|---|---|
| Start | 1 question, 2 quiet choices with 2 glossing bullets, reply field and 1 bright Send, 1 note. World: You, 1 destination, a 2-row key. Calm. | Same panel. World below: You and the destination. | Same panel. World: the destination and the key button only; You is hidden (I2). |
| Reply to review | 2 messages, a tray of 2 proposals (8 actions, 3 helper lines, 1 limit meaning), Save with its reason and Keep none, a helper paragraph. Below: the next question, its helper, reply and Send, Pause, note. About 14 controls and 2 decisions (I4). World: You only. | Same. No world. | The tray alone is longer than a screen. No world. |
| What we know | 4 facts (2 explained), a not-asked list of 8, Edit, then the early sketch, a second idea (M6). World: You and the destination. | No world. | No world. |
| Suggestions | Heading and helper, 3 emphasis controls, count line, 2–4 notes, a group heading, then an open card of about 25 lines whose bright action is below the fold, then 5 titles (I3). World: You only. | No world. | No world. |

## Verdicts on the implementer's readings and rulings (Half A)

1. **Chat immediate means the reply field from the first screen, with the sure-or-unsure choice kept and Send as the start's bright action.** Accept, as the reading that changes least. One caveat for session W2: the brightest thing on the first screen, Send with an empty field, does not answer the question asked ("How would you like to start?"); two quiet buttons do. Part 2's typed first question resolves this.
2. **"Preferences" means the account menu.** Accept. Add a visible "Preferences" heading so the product owner's word maps to what they see (M4).
3. **A tab, not a modal.** Accept. The record allows either.
4. **One suggestion open, its choice bright, every title kept to scan.** The structure is accepted. As built, the bright button is out of view (I3).
5. **Two new hues, leaf green and orchid.** Accept the need: no meaning hue was free, and the ADR records them as provisional. Notes: the double bright fills (M1), the doubled marking (M2) and the colour-blind distance (M3).
6. **Pause the interview kept as a quiet action; the stored key's details moved to the end.** Accept.
7. **Count line and notes kept visible, for session W2 to judge.** Disagree with leaving it unchanged. "Never overwhelming" is already the product owner's binding bar, and the fix keeps every note one step away (I3). If it goes to session W2, capture both versions.
8. **"Version" kept outside the strip.** Accept as a scope reading. Recommend the same plain words (M5).

Concerns:
- 1, the phone light: Important (I2).
- 2, suggestions density: Important (I3).
- 3, the reply field in the flow: Minor, accept (M8).
- 4, "version": Minor (M5).
- 5, the provisional list: correct.

Contrast:
- All 8 new pairings are present and measured.
- The only unrecorded pairing is I1's accidental text on #26324F.
- Mirror: byte-identical (`cmp`, tokens and fonts).

## Assessment

**Spec compliance:** Issues found.

**Task quality:** Needs fixes.

**Reasoning:** The colour work, the tabs, the plain strip and the decision notices are sound. But one reference is broken and seven others regressed by a class collision the checks cannot see. The You place shows no world on a tablet or phone in most views. The review and suggestions views break "one idea per view" and "never overwhelming" in ways the references hide.
