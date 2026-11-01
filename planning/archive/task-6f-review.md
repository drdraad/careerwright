# Task 6f review: no job yet (range 7b3a41e..8f13dfd)

One reviewer, experience and code together (R16). Read only. I read the brief, the binding
dispatch, the report, audit findings 1, 3, 4 and 8, and design review I1. Then I read the
package in three passes: (1) backend source and migration, (2) web lib and components,
(3) tests, e2e, evaluation, ADRs and register. I skipped the generated client.

Focused checks outside the diff, one per named risk, all at 8f13dfd:
- Migration risk: `r0001_identity_workspaces_profiles.py` (the table, its comment, RLS, grants)
  and `migrations/env.py`. I also searched for any hash over a profile document (none).
- Basis risk: I ran `interview._basis` directly in `backend/.venv`, and the demo interviewer
  through `tools.evaluation.observe_interview_demo` with INT-15's case and a changed message.
  Neither writes anything.
- Phone risk: the committed 390x844 captures `you--390x844.png` and
  `you--type-ahead-partial--390x844.png` (31 Oct), read against the new layout.
- I did not re-run the implementer's suites.
- Integration, acceptance and Playwright not run: Docker down.

### Spec Compliance
- ❌ Issues found:
  - A qualification's status, and a work status that happens to be an everyday word, are
    labelled "You said" when the person never said them. A qualification someone is taking
    can show as achieved with "You said this"
    (`backend/src/careerwright/profile/interview.py:344-360`). This breaks the brief's
    "an expected qualification is shown as expected everywhere, never as achieved". It also
    contradicts ADR 0006's new line "a work status is always shown as a reading"
    (`docs/adr/0006-taxonomy-and-interview-contract.md:365`). See I1.
  - The demo interviewer reads "I have to retake my GCSE maths" and "I have failed my GCSE
    maths" as achieved qualifications
    (`backend/src/careerwright/profile/fixture_interviewer.py:115-119`). See I2.
- ✅ Everything else on the card, against the named risks:
  1. **"I haven't had a job yet".**
     - It is a field state on the current role, with no value. `checked_input` refuses it
       for any other field (`document.py:392`), so it is never a job title, Skipped or
       Unknown.
     - Any state other than "unasked" lights the light (`world/model.ts:41`).
     - The start goes to "How would you like to start?" with no origin fetched
       (`Conversation.tsx:222-232`).
     - The demo asks only unasked fields, so the job question never returns
       (`fixture_interviewer.py:181-190`, `:427-431`).
     - The live model sees the state, and its instructions say never to ask again for what
       the profile holds.
     - What we know offers it for the role only (`vocabulary.ts` `fieldStates`). It never
       gets a "less precise" line.
     - The browser test is written. It doesn't run here (Docker down).
  2. **The two new answers.**
     - Both use the one write path (`commit_profile_version`) and the interview contract.
     - Skip, Unknown and Prefer not to say come through the shared state control.
     - The demo never asks either question; the live instructions say "at most once".
     - The form never picks a status for the person: an unmarked row is refused
       (`profile.ts:230-235`).
     - Every place that shows a qualification goes through `describeValue`, so it carries
       its status: What we know, the review tray, the source drawer, the stale notice and
       the chapter "uses" list. No backend code reads qualifications yet.
     - The one gap is the "You said" label (I1).
  3. **Migration 0040.**
     - Append-only is a contract, not a convention. The table comment says "Append-only"
       (`r0001…:85-86`), the API role has only SELECT and INSERT (`:169-172`), and
       `test_isolation.py:199` checks it.
     - The migration runs as the owner. RLS is ENABLE, not FORCE, so the UPDATE reaches
       every row and no row is skipped silently.
     - It is forward-only (the downgrade raises).
     - `defaults || document || {schema_version: 4}` keeps every stored key, so each version
       reads exactly as before. `ProfileDocument._read_older_versions` already gives the
       same result at read time. Nothing hashes a document.
     - So the rewrite is safe and keeps every earlier version's meaning. It departs from the
       table's own contract, which isn't recorded anywhere (Minor M1).
     - An old receipt replay returns the old shape (Minor M2). This is a robustness point,
       not a truth problem: the receipt describes that version truly, and the two missing
       fields mean "not asked", which is what they read as now.
  4. **Nothing presumes a job.**
     - Opening: "What would you like your working life to be like?" (web and demo match).
     - "Your next step" replaces "this change", in the demo question, the hint and the live
       prompt.
     - One example reply isn't a job: "I help run a youth football team".
     - The demo asks an unsure person what they enjoy, right after the opening.
     - The live line is there word for word, and `interview-turn-5` is checked by a test.
     - "Show me suggestions" no longer waits for a role (`conversation.ts:113`).
     - "Closer to what I do" is hidden when the role isn't given (`Directions.tsx:689-691`).
     - The unknown-work note drops "yet" and is never shown after a no-job answer
       (`Directions.tsx:741`).
  5. **Support screen unchanged.**
     - `safety.py` and `SupportNote` are untouched. There is no Childline text, placeholder
       or version bump, and PROF-15 stays open with its reason.
     - A typed qualification name goes through the support screen (`commands.py:227-233`).
       A work status is skipped as a fixed choice.
  6. **The experience.**
     - On a phone the new button sits on the same row as "Skip for now". The 31 Oct capture
       has that row at about y=582 of 844, so it stays in the first screen even if the two
       buttons wrap onto two lines.
     - The partial question gains about one line. "None of these is my job" was at about
       y=630, so it stays in view. This is my reading only; UI-12 didn't run.
     - ESCO is named plainly at the partial question, the closest step and the role list's
       summary, the places design review I1 asked for.
     - R11 holds: the API carries only states and codes, and every new sentence is in
       `vocabulary.ts`.
  7. **Writes.**
     - `POST .../origin/role/no-job-yet` takes an expected version and an `Idempotency-Key`
       through `run_idempotent` (`routes_origin.py:169-204`).
     - New errors don't echo input: "Only the current role takes that answer." and "The same
       qualification appears twice."
     - DBOS `application_version` is unchanged.
- ⚠️ Cannot verify from diff:
  - The integration tests (0040, the no-job endpoint, the round trip), the browser test that
    the world answers within ten seconds, the UI-12 phone checks and `make acceptance`: not
    run, Docker down.
  - Whether the live model keeps from asking the job question again under `interview-turn-5`
    is Task 6e's capped run.
  - Session W2's judgement of the words: not run — requires human.

### Strengths
- `no_job_yet` as a role-only state is the simplest truthful model. It can't be mistaken for
  a title or a skip, and it needed no new column.
- The form never defaults a qualification's status. The display always prints it, and
  "expected, not achieved yet" says it plainly.
- INT-15 runs offline on the demo interviewer through the same check the live run uses.
- Each changed test input and assertion is disclosed with its reason.
- The migration is careful (key order, the `||` direction, both `schema_version` places) and
  has a focused integration test, written but not run.

### Issues

#### Critical
None.

#### Important

**I1. "You said" is shown for a qualification status, or a work status, that the person never
said. (R16: truth.)**
- Where: `backend/src/careerwright/profile/interview.py:344-348` (qualifications) and `:360`
  (work status, through the generic text branch).
- What happens:
  - For a qualification, `_basis` checks only that the name is quoted. The status is never
    checked.
  - Reproduced: for the message "I am taking A-level biology this year.",
    `achieved: A-level biology` comes back `stated`.
  - The review tray then shows "Qualifications: A-level biology (achieved)" with "You said
    this; not verified" (`ReviewTray.tsx:61`, `:154`).
  - A work status takes the generic branch. Reproduced: "working" from "I am working towards
    my A-levels" also comes back `stated`. ADR 0006's new line says a work status is "always
    shown as a reading", so the ADR is wrong too.
- Why it matters:
  - The status is the consequential part. It is what Skills and Options will read as an
    entry fact met or not.
  - Careerwright here vouches for words the person never said, which makes a wrong "achieved"
    easier to accept.
  - The salary floor already sets the precedent: "the period is part of the value: a
    defaulted or different one is not their words" (`interview.py:353-356`).
- Fix:
  - Return `Basis.INFERRED` for every qualifications change. The status is always a reading,
    which the code's own comment already says.
  - Return `Basis.INFERRED` for every work_status change, so the code matches the ADR.
  - Correct the ADR 0006 line if the wording changes.
  - Add the two reproductions above as tests.
  - Update `test_a_qualification_is_proposed_achieved_or_expected_stated_only_from_their_words`,
    which asserts `STATED` (disclose the changed assertion).

**I2. The demo reads a retake or a failed exam as an achieved qualification. (R16: truth.)**
- Where: `backend/src/careerwright/profile/fixture_interviewer.py:115-119`.
- What happens:
  - `_ACHIEVED` makes the "'ve / have" optional and accepts a bare "have" as the verb.
  - Reproduced through `observe_interview_demo`:
    - "I have to retake my GCSE maths." gives `{'name': 'to retake my GCSE maths',
      'status': 'achieved'}`, basis `stated`.
    - "I have failed my GCSE maths." gives `failed my GCSE maths`, achieved, `stated`.
- Why it matters:
  - Both are the exact case the brief rules out: something not achieved shown as achieved.
  - Both are labelled "You said".
  - The demo is where the product owner and the first testers meet this (session W2). These
    are reproduced defects, so R11 allows the fix.
- Fix:
  - Fail-safe, not a new language rule: accept only an explicit verb (`I got`, `I've got`,
    `I have got`, `I passed`, `I've passed`), never a bare "have".
  - I1's fix then marks every demo qualification as a reading.
  - Add both sentences as `test_interview_agent.py` cases (no proposal, or not achieved).

#### Minor
(List; these wait for the final review.)
- **M1.** `r0040_work_status_and_qualifications.py:35-48` rewrites rows in a table whose
  contract is append-only (`r0001…:85-86`). It keeps their meaning, and the read-time default
  already gives the same result.
  - Record the exception in ADR 0006's amendment ("a schema migration may add not-yet-asked
    answers in place; nothing else changes"), or drop the rewrite and keep the read-time
    default.
  - The brief asked for a migration, so either choice meets it.
- **M2.** A replayed receipt from before 0040 returns a document without `work_status` and
  `qualifications`. The web reads `document[name].state` for every field
  (`world/model.ts:41`, `WhatWeKnow.tsx:105`), so a replayed result put into the cache would
  throw.
  - This only happens if a retry carries the same key across an upgrade, which is very
    unlikely locally.
  - Note it in the report or runbook. No code needed now.
- **M3.** `Directions.tsx:689-691`: if "Closer to what I do" was chosen before the role
  stopped being known, it stays applied with its button hidden. The implementer disclosed
  this. Reset the emphasis to balanced when it isn't offered.
- **M4.** Design I1 is only partly closed. "In ESCO as …" (`vocabulary.ts:985`) under a full
  type-ahead list, and the own-words line (`vocabulary.ts:1026`), still say "ESCO" with no
  explanation.
  - The places the design reviewer named are done, so this is polish.
  - Raise it at session W2's "words you didn't understand" question.
- **M5.** `vocabulary.ts:218`, `:225`: in What we know these read "Less precise without it:
  Nothing for now: Careerwright keeps it to check where you can start later." That's two
  colons, and "less precise" followed by "nothing" contradicts itself. Reword at session W2,
  or don't show the line for optional fields that nothing reads yet.
- **M6.** The UI-12 phone test (`e2e/conversation.spec.ts` "phone, first screen") doesn't
  check that "I haven't had a job yet" is in the first screen. It is the school leaver's first
  decision. The captures say it fits; add one `firstScreen` call so the test holds it there.
- **M7.** The demo misses some common ways of saying what someone is doing now. "I'm a sixth
  form student" sets no work status: `_STUDYING` allows only one word before
  "student" (`fixture_interviewer.py:99`). Known limit (R11): record it, don't widen the
  pattern.

### Assessment
**Task quality:** Needs fixes

**Reasoning:** The card is built faithfully: the no-job answer, the two answers through the
one write path, the opening without a job, the support screen untouched, and a safe
migration. Two truth defects remain. A qualification someone is taking, or a retake, can be
shown as achieved with "You said", which is exactly what the brief rules out. Both are small,
fail-safe fixes for the one allowed fix round.
