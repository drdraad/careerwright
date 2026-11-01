# Audit lens E: the person's practical path through Careerwright (L0, HEAD 8e78060)

Read-only. No app run, no browser, no live call. Evidence: the last acceptance captures, the
design references, the e2e specs, the web source, the fixture interviewer and the session
records. Severity is for usefulness to the person: **blocks** (they cannot go on), **hurts**
(they go on, worse off or confused), **minor**.

## Evidence base and freshness

- App captures: `apps/web/test-results/visual-{1440x900,768x1024,390x844}-*/screenshots/`,
  written 08:06 to 08:07 on 2026-10-31. Commit f179d0f is 08:12. f179d0f changes only
  `.popover` max-height (`globals.css`) and one keyboard test, so the captures show f179d0f
  except a long workspace menu, which no capture opens. **Not stale.** Below, `T/` stands for
  the capture folder of the stated width.
- Design references (`docs/design/screenshots/`, 07:36) show the design's intent, not the app.
  `docs/reviews/sprint-2/screenshots/` is the old light "Nessa" shell, used for comparison only.
- The captures use three workspaces:
  - P01 is the seeded fixture workspace (Ada).
  - "Conversation" is set up through the API (`e2e/api.ts:108-157`). Its role, enjoyed
    tasks and city were PUT directly, **not reached through the conversation**.
  - A new empty workspace.
  So no capture shows a person getting to the slate by talking.

## Summary

- **What a person can do today:** sign in, make a workspace, talk to an interviewer, review
  and save what it noted, edit answers, ask for up to six ESCO occupations, make one a target,
  and read ESCO's essential-skills list for that target. That is all of the You chapter. Every
  other chapter is a "Not built yet" card. The one exception is a synthetic route preview in
  the P01 workspace, labelled "not your routes".
- Of the specification's three questions:
  - "What work could suit my life?" is **partly** answered: a grounded slate of ideas.
  - "What would it take?" gets **only ESCO's generic skill list**.
  - "Which route is best?" gets **nothing about the person**.
- The demo (the only offline mode) breaks down as soon as a person answers in their own
  words. The fixture interviewer understands six fixed patterns and repeats its question
  otherwise. It can never take a target role (F1).
- The visuals cost most on phone and tablet. In long views the header and the world band take
  about half of the first phone screen. The band shows only "You" and the target. The world
  does not answer the slate, the tray or a choice (F7, F8, F9).

---

## 1. The path, step by step

### 1a. Demo mode: the P01 fixture workspace (Ada) and a new demo workspace

| # | Step | What they see / can do | What they learn about their career | Next action obvious? | Evidence |
|---|---|---|---|---|---|
| 1 | Sign in | A developer page: "Local sign-in through the Firebase Auth emulator", three "Seeded local identities", and an email/password form. | Nothing | Yes, for the owner. Jargon for anyone else. | `T1440/sign-in--1440x900.png` |
| 2 | Workspaces | "Your workspaces"; create one: Name, and "Data mode: Demo data / Live-assisted" with a one-line meaning. | Nothing | Yes: one primary, "Create workspace", which says why it is disabled | `T1440/home--empty--1440x900.png`; `WorkspaceList.tsx:22-26` |
| 3 | You: first ten seconds | "How would you like to start?" with two quiet buttons ("I know my direction", "Help me explore"), an empty reply field and a **bright Send**. World: P01 shows a lit "You" and the "Data quality analyst" light; a new workspace shows a dim dot. | Nothing new | Partly. The brightest control (Send on an empty field) does not answer the question asked. Choosing an entry changes nothing in the world. | `T1440/you--1440x900.png`; `T390/you--390x844.png`; `Conversation.tsx:155-183`; `model.ts:38-51` |
| 4 | Opening question | Explore: "What would you most like to be different about your working life?" Sure: "Which role are you aiming for, and at what level?" (asked even in P01, where the target is already set and shown). | Nothing | The question is clear. **The demo cannot use a literal answer** (F1). | `vocabulary.ts:220-223`; `Conversation.tsx:220-224`; `fixture_interviewer.py:209-223` |
| 5 | Send a message | Only messages that hit a fixture pattern get a useful reply: "I am a …", "I enjoy …", "N hours", "£N", an English city, "rather not say" with money. Otherwise the reply is "Demo interviewer (synthetic): Thank you." and the same question again. | Nothing; the reply is a count ("I noted 2 things") | The only hint is "synthetic answers from fixed patterns, not a model". It never says which patterns. | `fixture_interviewer.py:49-67, 115-187, 224-229`; `Conversation.tsx:456-458` |
| 6 | Review tray | "To review: 2 changes". Each change has Confirm/Accept (leaf green), Edit, Skip and Source. Each limit's meaning is in plain words. "Save to What we know" says why it is disabled. Keep none. The next question waits. | Their own limits, explained ("Pay you'd give up while you train isn't part of it") | **Yes on desktop.** On a phone the second proposal and Save are below the fold. | `T1440/you--reply-to-review--1440x900.png`; `T390/you--reply-to-review--390x844.png` |
| 7 | Saved | "Saved to What we know" and an orchid "Undo the last save", focused. Then the next question: "Do you have a role in mind, or would you like to explore?" | Nothing | The question is clear, but in the demo **neither answer can be understood** (F1). Nothing links to Suggestions. | `T390/you--saved--390x844.png`; `fixture_interviewer.py:45, 220-221` |
| 8 | What we know (tab) | Their answers (two limits explained), a "Not asked yet" list of 8 fields, "Edit answers directly", and "The early sketch for your target" in a closed disclosure. | A summary of themselves; what is still unknown | Yes | `T1440/you--what-we-know--1440x900.png` |
| 9 | Edit answers | A long form. Each field first needs "How you answer X" (Not asked yet / Answered / Unknown / Skipped / Prefer not to say) before its input. Target roles are free text, with no type-ahead. A stale save keeps the edits and explains them. | The rule behind each field ("Less precise without it: …") | Yes, but two controls per field | `T1440/you--answer-states--1440x900.png`; `T1440/you--stale--1440x900.png`; `profile.ts:191` |
| 10 | Suggestions (tab) | "Directions to explore": 5 emphasis buttons, a count line ("6 of up to 6, from 60 occupations found by 4 searches"), a "How Careerwright searched (n notes)" disclosure, groups, and one open card. Its actions come first: **Make this a target** (bright), Not for me, Exclude this kind of work, Source. Then what the work is, "Why this could suit you" (the written note quoting their words, and "How Careerwright found it"), "What might not suit you" and "Try it before committing". | **The most useful content in the app:** ESCO occupations linked to their role or tasks, each with a reason, its doubts and a cheap way to test it. The overlapping skills are only counted ("9 of the same essential skills"), never named (F4). | Yes on desktop. On a phone the first card starts below the fold, even in the design reference. | `T1440/you--slate--1440x900.png`; `T390/you--slate--390x844.png`; `docs/design/screenshots/you--suggestions--390x844.png` |
| 11 | Make this a target | The strip and world show the new target light. The button becomes "Already one of your targets." **The slate is then marked "Based on your earlier answers", and "Suggest again" becomes the bright action** (F5). No message says what was saved, and nothing points to what comes next. | That the target is saved | **No.** The app's own reaction suggests the person did something wrong. | `Directions.tsx:721, 735-741, 777`; `exploration.py:1280-1284` |
| 12 | The early sketch | Behind a disclosure at the foot of What we know: "What this work usually asks for, from ESCO" (essential skills, then "And N more"), the unresolved steps, and whether ESCO marks it regulated. An unmatched title offers "Use …" close matches. | **What the target usually needs (generic ESCO), not compared with them** | It is hidden. The person must know to look. | `SketchCard.tsx:45-120`; `YouChapter.tsx:340-346`; `e2e/conversation.spec.ts:146-153` |
| 13 | Roles, Skills, Options, Plan | A small card over the world: "Not built yet", the place's line ("The horizon: places you could head for"), one sentence on why it is empty, "Review what we know", and "More about this place". | Nothing | It is honest, but every one leads back to You | `ChapterView.tsx:35-66, 99-178`; `T1440/roles--1440x900.png`, `plan--1440x900.png`; `T390/roles--390x844.png` |
| 14 | Routes | **P01 only:** "Fixture preview: not your routes". Routes A to E, each with "Conditional: ready in N months, once its assessed report is passed" and "£X economic cost, £Y direct spending". A drawer shows payments and take-home pay by month and "Its print snapshot states…". **Any other workspace:** "Not built yet". | Nothing about themselves. It shows what a comparison will look like, in the words the product owner called "psychobabble" (F6). | No; it is a showcase, not a step | `ChapterView.tsx:220-246`; `T1440/routes--1440x900.png`, `routes--route-b--1440x900.png`, `routes--empty--1440x900.png` |

**The furthest real point is step 12:** a saved target and ESCO's generic list of what it
asks for. The scripted journey ends at the same point (`e2e/conversation.spec.ts:60-156`:
talk, review, undo, explore, choose, sketch). It types pattern-matching sentences such as "I
am a warehouse supervisor. I enjoy fixing bikes. I could do 5 hours a week in Leeds."
(`:77-80`).

### 1b. Live-assisted mode (the person's own Meta key)

| # | Step | Differences from the demo | Evidence |
|---|---|---|---|
| 1 | Create | "Live-assisted" warns that what they write goes to Meta's model. The box "This workspace holds synthetic test data only" is **ticked by default**: real data needs it unticked, and then the production model is used. | `WorkspaceList.tsx:22-26, 31-32, 76-85` |
| 2 | Key consent | Before the conversation: "Connect your Meta API key to talk with Careerwright", five bullets on storage and encryption, a key field, a consent box and "Store the key". "Not now? You can still edit your answers directly…" A clear gate, but long, and the first screen is about encryption, not careers. | `T1440/you--key-consent--1440x900.png`; `T390/you--key-consent--390x844.png`; `KeySetup.tsx:46-71` |
| 3 | Conversation | A real model reads free text. It should be able to take the target and Skip or Unknown, which the demo cannot, but this was not verified here (no live run). The reply streams, marked "not checked yet". | `Conversation.tsx:61-118`; `interview.py:453-465` |
| 4 | Suggestions | The model proposes searches and may suggest titles ("Titles Careerwright thought of but couldn't match…"). One written note is made per slate. | `Directions.tsx:577-593` |
| 5 | Spending limit | When the limit is reached the words say "Raise the limit or wait for the next month", **but there is no control anywhere in the web app to see spend or raise the limit** (F10). | `vocabulary.ts:251-253, 517-519`; the API has `routes_credentials.py:139-145`; no web call (`lib/queries.ts:12-60`) |
| 6 | Beyond You | The same placeholders. No preview in Routes (it is not the fixture workspace). | `ChapterView.tsx:227-246` |

The live path has never been exercised through the UI. The product path with real data (not
synthetic, production model) has never run live (F11).

### 1c. Chapter status

| Chapter | Status | Evidence |
|---|---|---|
| You | **Real**: conversation, review and save with undo, What we know, editing, the ESCO slate with its written note, choosing a target, the early sketch | `YouChapter.tsx:277-383`; captures `you--*` |
| Roles | **Placeholder** ("Role research isn't ready yet") | `ChapterView.tsx:36-42`; `roles--*.png` |
| Skills | **Placeholder** ("Skills checking isn't ready yet") | `ChapterView.tsx:43-49`; `skills--*.png` |
| Options | **Placeholder** ("Option research isn't ready yet") | `ChapterView.tsx:50-56`; `options--*.png` |
| Routes | **Partial in P01 only**: a synthetic TRACE-01 preview, "not your routes". A placeholder in every other workspace. | `ChapterView.tsx:220-246` |
| Plan | **Placeholder** ("Plan selection isn't ready yet…") | `ChapterView.tsx:57-65`; `plan--*.png` |

**Built behind the API, but the person cannot reach it** (the web imports only workspaces,
profile, preferences, turns, discoveries, slate, sketch, explanation, credentials and
sources: `lib/queries.ts:12-60`):

| Capability | API | Why it matters to the person |
|---|---|---|
| The unexpected connection, with the shared skills named | `SlateOut.connection` (`api/discovery_schemas.py:451-475, 525-526`) | A revelation already computed. The UI drops it. |
| The first answer by ESCO type-ahead, the skills usual in that role, the first destinations, the overlooked strength | `routes_origin.py:44-56, 109-190`; `routes_taxonomy.py:61` | The plan's "first ten seconds" (plan line 178), and it works without a model |
| Job research and listings (Adzuna, pages), favourites | `routes_research.py:57-274` | Roles: real openings for any title and city, in live mode |
| Capability matrices, questions, readiness | `routes_capability.py:43-208` | Skills. It covers only 4 fixture targets (F12). |
| The planning catalogue's options | `routes_planning.py` | Options. It covers only 4 fixture targets (F12). |
| Export, spend | `routes_export.py:153`; `routes_credentials.py:139-145` | Taking their data away; seeing and raising the model budget |

### 1d. Desktop and phone, side by side

| View | 1440 × 900 | 390 × 844 |
|---|---|---|
| Start | A 600 px console at the left with the question, the two choices, the reply field and Send. The world on the right shows You and the target. Calm, everything in view. | A 125 px header, about 360 px of world (You, the target, the key button), then the console from y≈485. The question is at y≈580 and the reply field at y≈672 to 752. |
| Reply to review | Two messages, the tray and Save (y≈795) are in view. The world shows only "You". | A header plus a 300 px band. The sheet starts at y≈425. The first Confirm is at y≈825; **the second proposal and Save are below the fold.** |
| What we know | Everything up to the sketch disclosure is in view. | **The key button covers the Suggestions tab** (F8). The facts start at y≈580. |
| Suggestions | The choice sits near the top of the open card (the reference has it at y≈716). The world shows only "You". | **The first card starts at y≈830 even in the design reference**, so the choice is a scroll away. |
| Not built yet | A small card at the bottom left; most of the screen is empty world. | The card fills the lower half; the world the upper half. |

Tablet (768): the world band is about 350 to 460 px high above the console (`T768/you--768x1024.png`,
`you--reply-to-review--768x1024.png`). The strip drops work area and budget but keeps "Pause
motion" and "Sound" (F15).

---

## 2. Findings

| ID | What the person hits | Evidence | Severity | Recommendation | Confidence |
|---|---|---|---|---|---|
| **F1** | **The demo interviewer cannot take an answer in the person's own words, and loops.** (a) "Help me explore": a literal answer to "What would you most like to be different…" gets "Thank you." and **the same question again**, while nothing is known yet. (b) "I know my direction": the fixture has no target pattern, so "Which role are you aiming for…" is asked **on every turn, for ever**. (c) "Do you have a role in mind, or would you like to explore?" has no pattern for either answer, so it repeats. (d) "Answer in your own words, or say Skip, Unknown or Prefer not to say" is shown, but the fixture understands none of these words except "rather not say" next to money. The only ways on are the "What we know" form or the Suggestions tab, and the conversation never points to either. | `fixture_interviewer.py:49-67` (patterns, none for a target or for skip/unknown); `:214-223` (question rules); `:190-191` (`_nothing_known`); `Conversation.tsx:387-391` (the hint) | **Blocks** (demo, which is the only offline mode and the one human testing starts in) | Give each demo question one-tap example replies ("I'm a warehouse supervisor", "5 hours a week", "Leeds", "Skip"), add a target pattern ("I want to be a …") and the skip/unknown words. For "role in mind or explore", add two buttons: **"Show me suggestions"** (opens Suggestions and starts it) and **"Name a role"** (opens target entry). The live model also benefits from that bridge. | High (code); not observed in a run |
| **F2** | **The journey ends inside You.** Four of six chapters are cards that lead back to You. Routes is a fixture preview that is not theirs. The rail draws all six chapters the same way, so the person finds each dead end by clicking it. | `ChapterView.tsx:35-66, 220-250`; `ChapterNav.tsx` (no built or not-built marker); `T1440/roles--1440x900.png`, `plan--1440x900.png` | **Blocks** the specification's questions 2 and 3 | Mark the unbuilt chapters in the rail (for example "coming later"), or hide them until each holds something of the person's. Put build effort where the person's path stops (section 4). | High |
| **F3** | **Computed revelations never reach the screen.** The slate's unexpected connection (with the shared skills named) and the origin endpoints (type-ahead, usual skills, first destinations, strength) are built and tested but not rendered. | `api/discovery_schemas.py:451-475, 525-526`; `routes_origin.py:44-190`; `lib/queries.ts:12-60` (neither is imported); `Directions.tsx` (no "connection") | **Hurts** | Make W2C part 2's wiring the next build. It is the cheapest new value for the person, because the backend is done. | High |
| **F4** | **The reason a suggestion fits is a count, not the skills.** "ESCO lists 9 of the same essential skills for both, so Careerwright joined them by those skills": which nine is never said. The transferable skills are the insight a person changing career most wants. The written note above it repeats the link and adds a 2-line provenance caveat, so one reason takes about 8 lines. | `exploration.py:634-639`; `T1440/you--slate--1440x900.png`; `T390/you--slate--390x844.png` | **Hurts** | Name the shared skills (the first few, the rest one step away). The connection already carries them (`SharedSkillOut`). Fold the note's provenance line into its Source. | High |
| **F5** | **Choosing a target makes the app call the slate out of date.** `choose_target` commits a new profile version, so the view shows "Based on your earlier answers… Suggest again", turns "Suggest again" into the bright action and demotes "Make this a target". Nothing says what was saved or what to do next, and the sketch stays hidden in another tab. | `exploration.py:1280-1284`; `Directions.tsx:721, 731-741, 777`; no test reads this state (`e2e/conversation.spec.ts:142-145` checks only the version and the strip) | **Hurts** | Do not treat a version that changed only the targets from this slate as stale (or say "Your target is saved"). After the choice, show "Saved as a target: what it usually asks for" with the sketch in place. | High (code); not captured |
| **F6** | **The only screen past You uses the words the product owner rejected.** Session 2: "No idea. Sounds like psychobabble", "don't understand 'conditional', or 'fixture' or the difference between economic cost and direct cost… 'Its print snapshot states' – frankly, the language is inaccessible", "Confusion can make one indecisive and give up." The screen still says "Conditional: … once its assessed report is passed", "economic cost", "direct spending", "fixture's baseline", "Its print snapshot states…". Routes are called "Route A" to "E", with nothing about what each one involves. W2D plans only two of these phrases. | `docs/reviews/session-2-answers.md:7-10`; `T1440/routes--1440x900.png`, `routes--route-b--1440x900.png`; `RoutePreview.tsx:206`; `l0-sprint-tasks.md` (W2D list) | **Hurts** | Either take the preview out of the person's path (keep it in Storybook and design review), or rewrite every phrase in plain words and name what each route is. Do it before any session where the owner reads Routes again. | High |
| **F7** | **On a phone, the world takes about half the first screen in long views, and the first decision is a scroll away.** The header is 125 px; the band is `max(300px, 34vh)`. In the tray view the first Confirm is at y≈825 of 844 and Save is below the fold. In Suggestions the first card is at y≈830 even in the reference. What the band holds: "You" and the target name (`worldFromProfile` draws no skills, openings or suggestions). Fix round 1 left this open as concern 1. | `globals.css:1683-1691`; `model.ts:44-53`; `T390/you--reply-to-review--390x844.png`; `docs/design/screenshots/you--suggestions--390x844.png`; `task-W2C1-report.md` fix round 1, concern 1 | **Hurts** | On a phone, size the band to what it has to show: a slim band (about 100 to 140 px, "You" and the target) when the world holds no skills or suggestions, or when the view has a pending decision. Keep the tall band for the start view and for revelations. Measure "first decision in the first screen" as a check. | High |
| **F8** | **On a phone, the key button covers the Suggestions tab** in the What we know view: "What the lights mean" sits over "Suggestions", so a tap there opens the key. The automated checks report no problem for this capture. "You" is also hidden under the console's edge. | `T390/you--what-we-know--390x844.png` (cropped and checked); `checks-390x844.json` (`overprinted: []`) | **Hurts** (it blocks the route to Suggestions on that view) | Keep the key inside the band, clear of the console's top edge, or move it into the menu on phone. Add an "on top" check for the three tabs at 390 and 768. | High |
| **F9** | **The first ten seconds don't meet the plan.** The plan: "within ten seconds the person has changed something and the world has answered" (`CLAUDE.md`), with a browser test "a first answer changes the world within ten seconds" (`development-plan.md:536`). In the app, the light lights only after a **saved** answer. In the demo that takes a message matching a pattern, a worker run, a review and Save. Choosing an entry changes nothing in the world. No e2e test measures it. The type-ahead first question that would do it is built in the backend (F3). | `model.ts:38-51`; `Conversation.tsx:155-183`; e2e test list (no such test); `development-plan.md:178, 536` | **Hurts** | Make the first screen the plan's first question ("What do you do now, or what did you do last?") with the ESCO type-ahead, lighting the origin and its usual skills on the pick. Add the ten-second browser test. | High (absence); medium (time to first light, not measured) |
| **F10** | **A live person who reaches the model budget cannot raise it.** The words say "Raise the limit or wait for the next month"; the web app has no spend view or limit control, though the API has both. | `vocabulary.ts:251-253, 517-519`; `routes_credentials.py:139-145`; no `/spend` call in `apps/web/src` | **Hurts** (live) | Add a small "Model spending" line (spent this month, the limit, Change) to the account menu's "Preferences for this workspace". Until then, change the words to say where the limit can be raised. | High |
| **F11** | **The real-data live path has never run.** The ledger's production-model calls are the two Sprint 0 spike calls. Every interview, discovery and note evaluation used the test model, and the last ran on 2026-10-28, before the W2B and W2C changes. The session W2 sheet lists "the discovery prompts, untested live". | `docs/evidence/live-usage.md` rows 6-7 (production), 13-26 (test model); `l0-sprint-tasks.md` session W2 sheet | **Hurts** (unknown quality for a real user) | Before human testing, run one budget-capped turn, discovery and note through the UI path on the model chosen for testing (ties to A1's Muse Wonder question). | High (ledger) |
| **F12** | **The deeper chapters can serve only four fixture target and city pairs, but the slate invites any ESCO occupation.** The option pack and the capability reference each hold 4 targets (data quality, IT support, nurse, bookkeeping, one city each). Someone who makes "logistics and distribution manager" a target will find Skills, Options and Routes cannot cover it, and nothing tells them that at the choice. | `catalogue/packs/england_option_pack/england-option-pack-0.2.0.json` (`targets`: 4); `capability/reference/capability-reference-0.2.0.json` (`targets`: 4) | **Hurts** (it sets the ceiling on later chapters) | Say it where a target is chosen ("In this version Careerwright researches courses and routes for 4 roles; for others it shows ESCO's skill list"). Weigh ESCO-wide features (the slate, shared skills, usual skills compared with the target's) above pack-bound chapters when ordering work (section 4). | High (data); judgement on order |
| **F13** | Answering means two controls per field: "How you answer X" must be set to "Answered" before the input works. Target roles are free text, with no type-ahead. It is form-like, the thing the product owner rejected. | `T1440/you--answer-states--1440x900.png`; `T390/you--source-drawer--390x844.png`; `profile.ts:191` | Minor | Open each field ready to type, with Unknown, Skip and Prefer not to say as quiet choices beside it. Reuse the ESCO type-ahead for target roles and current role. | Medium |
| **F14** | On a tablet the strip drops **work area and budget** but keeps **"Pause motion" and "Sound"**: the world's controls outrank the person's facts. | `T768/you--768x1024.png`; `WorkspaceStrip.tsx:170-178`; `task-W2C1-review-app.md` M6 | Minor | Keep budget and work area at 768 and move the motion and sound switches into the account menu below desktop width. | High |
| **F15** | "Not for me" and the emphasis buttons are view-only by design (ADR 0007), so they vanish on reload or "Suggest again", and nothing says so. | `Directions.tsx:515` (local `useState`) | Minor | Label it "Hide for now", or keep the hidden list in browser storage as view state, never as a limit. | High |
| **F16** | The P01 demo's own target, "Data quality analyst", does not match ESCO. Its sketch offers close matches ("Call centre analyst", "Data analyst", "Water quality analyst"), while the capability reference maps it to "data quality specialist". So the flagship demo shows no requirement list until the person picks a close match. | `docs/reviews/sprint-2/screenshots/you--1440x900.png` (older wording); `capability-reference-0.2.0.json` target 1 note | Minor | Seed P01 with the ESCO-resolved title, or include "data quality specialist" among the close matches. | Medium (current sketch not captured) |
| **F17** | Two pauses on one screen ("Pause motion" in the strip, "Pause the interview" under the reply field). The start screen's bright action is Send on an empty field, under a question answered by two quiet buttons. | `T1440/you--1440x900.png`; `task-W2C1-review-design.md` verdict 1 | Minor | Rename the world's pause "Still the world", or move it to the menu. Make the entry choice the bright action until the first answer. | Medium |

**Where work is lost:** fix round 1 closed the large case: the views stay mounted, so a
typed reply, the tray's choices and form edits survive tab changes (`YouChapter.tsx:18-20, 243-254`).
What is left is minor. A reload drops a typed reply and the tray's choices (normal), and
drops "Not for me" (F15). A stale save keeps the edits and shows the newer value
(`T1440/you--stale--1440x900.png`), which is good.

---

## 3. The world: where it helps the work and where it costs it

| | Helps | Costs |
|---|---|---|
| Orientation | The target as a warm light on the horizon is an instant "where I'm heading". On a phone it is the **only** place outside What we know that names the target, because the phone strip hides it (`WorkspaceStrip.tsx:170`; `T390/roles--390x844.png`). | On desktop it repeats the strip (target shown in both: `T1440/you--1440x900.png`). |
| Space, desktop | The console stays a readable 600 px column; the world uses spare width. | About half the width shows a single dot in most views (`you--slate`, `you--reply-to-review`, `you--stale` at 1440). Long forms scroll in a narrow column beside empty sky. |
| Space, phone and tablet | It keeps "the place" present (session W1's choice). | About 300 to 360 px of 844 for "You" plus 0 to 3 names. With the 125 px header, about half the first screen in long views (F7). The key button covers a tab (F8). On a tablet, 350 to 460 px above the console. |
| Attention and decisions | Colour-coded Accept (leaf) and Undo (orchid), and one bright primary per view, answer session 2's "could be easier with colour coded buttons" and "needs to be a bright colour" (`T390/you--saved--390x844.png`). | The world does not answer the decisions: the slate shows no rings, the open suggestion is not singled out, a target is not previewed, and confirming, saving and undoing change nothing (`task-W2C1-review-design.md` M7; `model.ts:44-53`). The picture and the decision live in different places, so the person reads text and the world is backdrop. |
| Words and picture | Every light has its words in the DOM, and the still world says the same (`World.tsx:1-8`). | The words carry all the career content. The design references draw skills and connections in the world (`docs/design/screenshots/you--default--390x844.png`, `roles--default--1440x900.png`) that the app does not have yet, so a reviewer judging references sees more than a person gets. |
| Header chrome | Pause and Sound respect the person's choice. | "Pause motion" and "Sound" take the strip's second row on desktop and outrank work area and budget on a tablet (F14). |
| Build effort | Session W1 chose a direction and the chapter is calmer than session 2's "mess". | Fix round 1's largest visual change (the band on tablet and phone) is what put the first decision a scroll away (F7). The world's next slices (W2C part 2, W2D frame re-measure) come before any chapter that answers "what would it take". |

**Net:** on desktop the world costs little and adds a sense of place. On phone and tablet it
costs real screen and moves decisions down, while showing almost nothing yet. It will earn
its space once it draws the computed things (usual skills, suggestions as rings, the
connection). Until then, shrink it to what it shows (F7).

---

## 4. The most useful thing today, and the shortest path to the next one

**Most useful today:** a person states their current role and the tasks they enjoy, and gets
**up to six ESCO occupations found from their own words.** Each comes with a plain reason,
what might not suit, a cheap way to try it, and (with a target chosen) ESCO's list of what that
work usually asks for. It is grounded and honest ("ideas to test, not a judgement of fit").
In the demo, a person reaches it only by typing the fixture's patterns or using the form (F1).

**Shortest path to the next most useful thing: "What could I do, and which of my skills carry over?"**
It reuses backend that is already built, needs no model and works for any ESCO occupation (not
only the 4 pack targets):

1. **Unblock the demo conversation** (F1): example replies, a target pattern, and the two
   bridge buttons "Show me suggestions" and "Name a role". This is small, and human testing
   depends on it.
2. **The first question with the ESCO type-ahead** (`/taxonomy/titles`, `POST /origin/role`):
   the role is picked, not parsed, and its usual skills appear at once. This meets the
   ten-second bar (F9) and gives the slate a solid role to search from.
3. **Name the shared skills** in each suggestion, and show the unexpected connection the slate
   already returns (F3, F4).
4. **After "Make this a target"**: no stale warning, and the target's skill list shown in place
   (F5). Mark which of its essential skills the person's role usually shares, as "usual in
   your role, not confirmed yet". This is a first, ESCO-only "what would it take", for any
   target.

Then, for "what would it take, really": Roles over Adzuna (built in Task 7, live only, any
title and city) gives real openings and pay. The pack-bound Skills, Options and Routes
chapters serve 4 target and city pairs (F12) and should come after, presented as such.

Items 1, 3 and 4 are mostly web work over existing endpoints; item 2 is W2C part 2's first
item. Session W2's world polish (rings, frame re-measure, hues) can follow without blocking
any of them.

---

## 5. What I could not check

- **Anything live:** how the real model handles free text, targets and "Skip"; reply
  latency; the quality of the slate and the note on a live discovery; the budget-exceeded
  path end to end. The ledger shows no UI-path live run (F11).
- **Time to the world's first answer** in a new demo workspace: worker latency is not in any
  capture (the e2e specs allow up to 60 s: `conversation.spec.ts:82-84`).
- **The moving world.** Every capture is the still world; motion, sound and frame rate are
  not visible headlessly.
- **States not captured:** the Suggestions view at scroll top on phone and tablet, the screen
  after "Make this a target" (F5), the current P01 sketch (F16), the 390 px chapter menu, and
  the "I know my direction" Suggestions view with its focus loss.
- **Human-only judgements:** whether it "feels like a world answering the person"; colour
  reading; VoiceOver; Safari. These are not run and require a human (ruling R2).
- I read the fixture interviewer's rules from code, not from a run. F1's loops follow
  directly from `fixture_interviewer.py:209-223`, but no capture shows a repeated question.
