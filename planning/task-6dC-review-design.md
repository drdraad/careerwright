# Task 6d slice C review, Half A: design and the person's experience (`design`)

Commits 51ca593..8292c6a. I read the reviewer contract, the Task 6d card and its standing rulings,
the slice C dispatch and its binding decisions, the implementer's report (as unverified claims),
slice B's last design re-review and the no-job-yet audit. Then the package's web, design and
document hunks in full (`TitleDetails.tsx`, `SupportNote.tsx`, `ReviewTray.tsx`, `YouChapter.tsx`,
`Directions.tsx`, `SketchCard.tsx`, `World.tsx`, `vocabulary.ts`, `queries.ts`, the stories, the
three e2e hunks, the web tests, `world.js`, the design README and the three ADR lines), and the
backend hunks only where they decide what the web shows (`title_details.py`, the schemas and the
decision route).

Focused checks outside the diff, each for one named risk: where else the web names ESCO
(`git grep` at 8292c6a); which `SupportNote` uses pass `actions` (only `FirstQuestion.tsx:256`, so
the move touches nothing else); `Button.tsx` (what `disabledReason` draws); `useCommand` (a save
resolves only after its refetch); `world/model.ts:54` (the app's world draws no skills yet);
`world.spec.ts` (the WLD-03 checks); where the support screen runs (`has_risk_stem` callers); and
every remaining "unexpected connection" in the repository. I looked at the review captures
`you--title-details` (3 sizes), `you--title-support--390x844`, `you--slate` (390 and 1440) and the
design references `roles--default--1440x900` and `you--suggestions--390x844`.

No suite, browser or test was run. No distress text was written. Line numbers are at 8292c6a.

### Spec Compliance

- ✅ **The connection as a plain line (binding decision 1).** In the web, nothing singles one
  suggestion out any more: the kicker, its "hasn't compared" line, `.suggestion-kicker` and the
  `connection` prop are gone (`Directions.tsx`, `globals.css`). Every joined suggestion keeps the
  same plain reason line and its skills (capture `you--slate--1440x900`: "Your current role:
  “warehouse supervisor”. ESCO lists 9 of the same essential skills for both…"). The test asserts
  no "unexpected" or "connection" on the card. No web consumer was left reading the removed fields
  (stories, tests and the client move together; the report's `tsc` run covers the rest). Two
  leftovers are documents and a design reference, not the product (Minor M1, M2).
- ✅ **ESCO's list is ESCO's (decision 2, first part).** "ESCO lists these for this kind of work:"
  in the sketch and a chosen target, the coverage line, the loading line, the world's caption and
  key, the role's list, and the design references. No "usual" or "usually" is left in a web
  string (`git grep`). Tests pin the words and their absence.
- ❌ **ESCO named plainly the first time it appears on a screen (decision 2): partly.** It is
  named where a list of skills first shows (the suggestions' header, the sketch, the role's
  list). It is not where a person first meets it: the first question (Important I1).
- ✅ **"Not part of my job" (decision 2).** A toggle per skill beside the person's own role only,
  one step away, with a plain line once marked. Nothing in the web reads the mark beyond that
  line. Details of the control: Minor M3, M4.
- ✅ **No revelation rests on ESCO's essential skills alone.** In the web, the strength and the
  slate are unchanged and the connection's mark is gone. The world draws no skills yet
  (`world/model.ts:54`), so its "ESCO lists it" caption is only in tests and references.
- ✅ **Seniority and industry (decision 3).** Optional, beside the role and each target; not
  given is said ("Seniority and industry: not given."), never a default; whitespace becomes null;
  120 characters as the API allows; "doesn't use them to match work" in plain words. One
  interaction loses typed words (Important I2).
- ✅ **The CV deferred (decision 4).** Sound. The message and prompt bounds (reason 1) and the
  missing pre-seal removal of referees' contact fields (reason 2) are each enough on their own;
  the product owner's school-leaver direction (reason 4) supports it. Reason 3 overstates the bar:
  the dispatch allowed "or says plainly that it needs a key", so the demo alone didn't rule it out.
  No fix needed.
- ✅ **R2-M1, "Keep it as my job title" on a phone's first screen.** Fixed at its cause:
  `SupportNote` renders its actions right after the line (`SupportNote.tsx:34-36`), Dismiss stays
  last. Both a document-order check and a 390 × 844 geometry check can fail. The capture shows
  Keep under the line with the first service still in view.
- ✅ **Every typed answer screened (carried item).** The review step's typed answers and the new
  detail fields bring the same calm panel, for a save and for a refusal. It stills the world, is
  kept until dismissed, and Dismiss returns focus to the save notice or the tray
  (`YouChapter.tsx:320-329`, `ReviewTray.tsx`). Tests use the existing fixture sentence only.
- ✅ **Nothing new presumes a job, and nothing is a dead end.** A person with no title meets
  nothing (`TitleDetails.tsx:271`, tested with no "job" or "ESCO" on the page). One who skipped
  the role but has targets sees only "Target role" entries and no skills list. "Not part of my
  job" (the card's own words) appears only beside a title the person gave at "What do you do
  now, or what did you do last?". Where a list is empty, nothing is shown, so no empty panel reads
  as a failure. A question about a role that isn't a job: Minor M8.
- ✅ **The decision stays on the first screen.** The shorter ESCO naming keeps "Make this a
  target" on a phone (UI-12, the reference capture). The new section sits below What we know's
  answers and never above its decision.
- ⚠️ **Cannot verify from the package:**
  - VoiceOver, Safari and a real phone's keyboard over the new form: not run, requires human.
  - The new words and both new screened places: session W2 and the support-policy review, not
    run, requires human (`REVIEW_STATUS` says "not yet reviewed as built").
  - That matching, readiness and the strength never read seniority, industry or the marks: Half B.
  - `make check` and `make acceptance`: the implementer's runs, not re-run.

**The report's concerns, judged:**
- *Anything left that reads as a revelation?* Not in the product. The Roles design reference still
  leads its panel with one pair and "Keep statistician in view" (M1), and the plan, `CLAUDE.md`
  and the sound cue still name the connection as a revelation or a Task M candidate (M2).
- *The CV's four reasons:* sound, with reason 3 overstated (above).
- *Acceptance run 1's still-world failures:* not a defect this slice touched. Its only world change
  is a caption string the app doesn't draw yet. The failing checks wait a fixed 900 ms for the
  moving world's names (`world.spec.ts:621`, the `open` helper), then compare. On a loaded machine
  that is a race, which fits "the moving world named nothing". It is a fragile test for the final
  review list (wait for the names, not a fixed time), not a person-facing defect.
- *The export, the interviewer, `CLAUDE.md`:* the export gap is recorded in ADR 0015 (Half B
  judges its effect); the interviewer gap is fine, since the card asks for optional fields beside
  a title, not for the interviewer to collect them; `CLAUDE.md`: M2.

### Strengths
- The connection went cleanly from the web: one plain line on every joined suggestion, the
  absence tested, the story renamed rather than left with a dead field.
- ESCO's list wording is one set of constants (`ESCO_LISTS`, `ESCO_NAMED`, `TITLE_DETAILS`), used
  everywhere it shows, with one test per fixed sentence.
- The shorter ESCO naming was the right "path first" call: the implementer measured the longer one
  pushing the first decision off a phone and cut words, not the check.
- The new section handles focus with care: Save moves focus to the title's heading, Cancel back to
  its opener, Dismiss to the heading; "Saved." is announced; each toggle carries `aria-pressed` and
  its skill's name for assistive tech.
- Unknown stays unknown: "not given" for each detail, never a placeholder value.
- R2-M1 is fixed for the right reason and guarded by a check that can fail.

### Issues

#### Critical
None.

#### Important

- **I1. ESCO is still unexplained where a person first meets it: the first question.**
  `vocabulary.ts:917-918` ("In ESCO as …", "Careerwright couldn't match that title in ESCO. Is it
  one of these?"), `vocabulary.ts:937-938` (the closest step: "…looked up the ESCO occupations in
  the group it's in."), `vocabulary.ts:954-955` (own words: "…couldn't match it in ESCO or the UK
  job-title index…"); used at `FirstQuestion.tsx:292`, `:362`, `:431` and `Conversation.tsx:315`.
  - What happens: the first screen a school leaver sees, within its first ten seconds, says "ESCO"
    with no words for what it is. The plain naming comes only later, on the suggestions or inside
    What we know's list. In What we know the same holds on a smaller scale: the disclosure's
    summary names ESCO (`TitleDetails.tsx:165`) before its intro explains it.
  - Why it matters: the dispatch's binding decision 2 says to explain ESCO "the first time it
    appears on a screen, or name it plainly". The ADR and the report narrow that to "where a view
    first shows its list" (disclosed). `CLAUDE.md` asks the same of any technical word, and the
    product owner's 1 November direction makes jargon at the start cost more. It touches the first
    ten seconds (R14 keeps that in the task).
  - Fix: name ESCO plainly once on the start, where it first shows (the partial list's question
    and the closest step's line are the natural places; the implementer picks the words), and in
    the role list's summary or just before it. Keep UI-12's phone checks for the partial list and
    the closest step green. If the controller accepts the narrower reading, record it in ADR 0015
    and this becomes Minor.

- **I2. Marking a skill throws away seniority or industry the person has typed but not saved.**
  `TitleDetails.tsx:236-243` (`<DetailsForm key={details.version}>`) with the toggles at
  `:170-188`.
  - What happens: the person opens "Add seniority or industry", types "Band 6", then (before
    pressing Save) marks a skill in the list just below. The mark saves a new version, the form's
    key changes, the form remounts closed, and "Band 6" is gone. The line under the title still
    says "Seniority and industry: not given." Nothing says the typing was dropped.
  - Why it matters: lost input is a high-effect kind (the contract; R14 keeps it in the task). The
    form and the list sit together in the same title's block, so doing one then the other is a
    natural order.
  - Fix: reset the form only after a save made from the form (for example, close and reset it in
    the form's own success path, and key it by something a mark doesn't change), so a mark keeps
    an open form and its drafts. Add a test: type in the open form, mark a skill, and the typed
    words and the open form are still there.

- **I3. If the role's ESCO list fails to load, it silently disappears.**
  `TitleDetails.tsx:206` and `:252-257` (`origin.data?.usual_skills ?? []`).
  - What happens: when `GET .../origin` fails, `ListedSkills` gets an empty list and renders
    nothing. The person sees exactly what a role with no ESCO list shows: no list and no way to
    mark anything, and no word that something failed. The other two requests in this component
    do show `RequestFailure` (`:260`, `:268`).
  - Why it matters: Global Constraint 6 (a failed state stays distinct from a zero result in the
    UI), and the contract lists a swallowed error as Important. The effect is small (a display
    feature one step away), so this is a one-line fix, not a redesign.
  - Fix: for the role, show `RequestFailure` with "Try again" when `origin.error` is set, as
    `TargetSaved` does for the sketch (`Directions.tsx:324`). A test with a failing origin route.

#### Minor

- **M1. The Roles design reference still singles out one pair as its panel's lead.**
  `docs/design/compositions/world.js:737-742`; capture `roles--default--1440x900`.
  - The panel opens with "ESCO lists 6 of the same essential skills for data quality analysts
    and statisticians." and its one bright action is "Keep statistician in view". The kicker is
    gone, so the line now reads as fact without the "an example" label it had.
  - Task 8 builds Roles to this reference. Built as drawn, it needs a rule that picks one
    suggestion, which is the rule this slice removed by the product owner's answer.
  - Fix: label the panel's lines as an example again, and note in the README that no suggestion
    is singled out (shared skills are a plain line on each), so Task 8 doesn't rebuild the rule.
- **M2. Documents still call the connection a revelation and a Task M candidate.**
  `CLAUDE.md:44`; `development-plan.md:164, 181, 193, 195, 488, 590, 604, 758` (SM.1's candidates
  include "the unexpected connection lit in the world"); `l0-sprint-tasks.md:414`; the sound cue
  "a chime when a connection lights up" (`world/sound.ts:2-12`, `World.stories.tsx:196`).
  - A Task 8 or Task M implementer reading these would build the moment the product owner just
    ruled out ("Always a plain line"). These are the controller's documents.
  - Fix: before Task 8 or M is dispatched, amend them to the product owner's answer. The chime was
    the product owner's own ask at session W1, so ask them whether it stays, with no trigger.
- **M3. The "Not part of my job" toggle doesn't look pressed, and every toggle flickers
  "Saving…".** `TitleDetails.tsx:175-190`; `Button.tsx` (`disabledReason`); no
  `.btn-quiet[aria-pressed="true"]` style in `globals.css`.
  - Pressed or not, it is the same underlined "Not part of my job" (capture
    `you--title-details--1440x900`). Only the line under a marked skill shows the state, and
    nothing on the control says a second press removes the mark.
  - While any save is pending, each of the role's toggles shows "Saving…" beside it: 70 times for
    the specialist nurse list, so the list jumps on every mark.
  - Fix: give the pressed toggle a visible state, and show "Saving…" once, beside the toggle
    pressed.
- **M4. The role's list doesn't say which ESCO occupation it is, and it sits under a heading
  about something else.** `vocabulary.ts:369-374`; `TitleDetails.tsx:165`, `:228-231`, `:273-275`.
  - Under "Your role: Registered nurse" it says "The 70 skills ESCO lists for this kind of work".
    The list is ESCO's specialist nurse, the person's closest pick, which is named nowhere in What
    we know. A person may mark skills against "registered nurse" that ESCO never listed for it.
  - The list and its marks sit inside the region "Seniority and industry", so someone who
    navigates by headings or landmarks won't find the skills under that name. Each title is also
    its own region landmark (nested `section`s with labels), which adds many landmarks.
  - Fix: say which ESCO occupation the list comes from, and give the section a name that covers
    both (or the list its own heading). Session W2 may judge the words.
- **M5. A refused save's reason shows below the open list.** `TitleDetails.tsx:260`.
  - The failure renders last in the title's block, after the skills list. With the list open, a
    stale save's reason is up to 70 rows below the form, and below the support panel whose line
    says the reason is "shown with them" (the same kind as slice B's R2-M4).
  - Fix: render the failure right after the form (before the panel and the list).
- **M6. `aria-controls` points at a form that isn't in the page.** `TitleDetails.tsx:53`.
  - While the form is closed, the opener names an ID that doesn't exist. `Directions.tsx` avoids
    this (`aria-controls={open ? body : undefined}`).
  - Fix: the same pattern.
- **M7. The title's heading changes the person's own words.** `TitleDetails.tsx:231`.
  - `sentence()` upper-cases the first letter, so a title typed as "iOS developer" shows as "IOS
    developer". The button beside it keeps the title as typed (`:60`). `CLAUDE.md`: a person's
    own title is always kept in their words. (`SketchCard` already does this for targets.)
  - Fix: show the title as held.
- **M8. A question for session W2: seniority and industry beside a role that isn't a job.**
  - A student who keeps "Student" at the first question sees "Your role: Student", "Seniority and
    industry: not given." and the hint "For example: trainee, senior or Band 6." It is optional and
    harmless, but job-shaped. Under the product owner's 1 November direction, ask whether it
    should show only for targets, or for a role they mark as work.
- **M9. A question for the controller: the workspace name is typed but not screened.**
  `WorkspaceList.tsx:50` (the new workspace's name); no `has_risk_stem` call covers it (the
  screen runs only in the interview, origin, profile and taxonomy routes). Whether "every place
  a person types" (the product owner, 31 October) includes it is the product owner's call.
- **M10. A fragile acceptance check (final review list).** `world.spec.ts:621` (`open`) and
  `:669` wait a fixed 900 ms for the moving world's names before comparing them with the still
  world's. Under load that races, which fits acceptance run 1's two WLD-03 failures. Wait for the
  names to be placed instead.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The connection's removal, ESCO's list wording, the support panel on every typed
answer and R2-M1 are done well and tested. Three small fixes remain before session W2: ESCO
unexplained at the first question (I1), typed seniority or industry lost when a skill is marked
(I2), and the role's list vanishing silently when it fails to load (I3).
