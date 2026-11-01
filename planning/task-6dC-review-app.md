# Task 6d slice C review: Half B, the app, the truth and the tests (`app`)

Reviewer: agent, read-only. Commits 51ca593..8292c6a. I read the review diff's backend, test,
evaluation, register, ADR and plan parts in full, and the web parts that use the API
(`TitleDetails.tsx`, `queries.ts`, `vocabulary.ts`, `ReviewTray.tsx`, `YouChapter.tsx`, the e2e
specs). The code was read at 8292c6a. I ran no suites. Each check outside the diff is named
below with the risk it covered.

### Spec Compliance
- ❌ Issues found: one Important (typed details lost when a mark is toggled, below). Everything
  else in this half meets the card, the dispatch's rulings and the Global Constraints.
- What I checked, by the dispatch's list:
  - **Migration 0039** (`r0039_title_details.py`): forward-only (`downgrade` raises). Row-level
    security is on, with the same `api_workspace` policy as `target_records` (0034). Grants are
    `SELECT, INSERT` only, so the table is append-only for the API role. `ON DELETE CASCADE`
    covers `make reset-demo`, which deletes the fixture workspace and seeds it again
    (`cli.py:253`). `test_isolation.py:191` already fails on any table without RLS. The CHECKs
    repeat most rules (`title_use`, `version >= 1`, text 1 to 120 characters, NULL for "not
    given" with no default). The marks have no CHECK (Minor M2).
  - **"Not part of my job" is display only.** Outside its own module, only `routes_origin.py:66`
    reads it (`role_marks`), and `usual.usual_skills` turns it into a boolean on the origin's
    skills. Nothing in capability, readiness, the slate, the sketch, the strength or the records
    reads `title_details`. A mark adds no `skill_evidence` row and leaves the capability version
    unchanged (`test_title_details.py:139`). The marks are checked against the same occupation
    the origin lists: both use `role_record`, then `titles.role`, then the one occupation's
    essential skills.
  - **Matching ignores seniority and industry**: nothing reads them. The origin's role and
    destinations are the same before and after a save (`test_title_details.py:72`).
  - **The connection is gone, and no consumer broke.** `Connection`, `unexpected_connection`,
    `ConnectionView`, `_connection`, `ConnectionOut`, `SlateOut.connection`,
    `OriginOut.connection` and `taxonomy_store.shared_essential_skills` are all removed.
    Consumers I checked:
    - the workspace export carries `DiscoveryOut` (its proposal and note), never `SlateOut`, so
      export format 4 doesn't change;
    - `slate_explanation.build_input` never read the connection;
    - no tool, e2e spec, story or fixture adapter mentions it any more;
    - `tsc` and the generated-client check passed in the implementer's `make check`.
    `first_slate` also lost its `stored_targets` call. That call only fed `_connection`, and
    reads never store anything (`targets.py:324`), so nothing else changed. The plain line
    stays covered by `joined_by_skills` (`evaluation.py:347`, `reason.shared >=
    MIN_SHARED_SKILLS`). Nothing in the API still reads as a revelation.
  - **support-policy-10**: the panel is worked out again from each request and never stored.
    The decision receipt is still the plain `DecisionResult` (`routes_interview.py:230`–`:234`), and
    the details receipt is the plain `TitleDetailsOut`. Both are tested: no receipt holds
    "support". Nothing is used for suitability. The tests use only the existing fixtures
    (`test_interview_choices.DISTRESS`, and "I volunteer on a suicide prevention helpline." in
    the web tests).
  - **Every write takes an expected version and an `Idempotency-Key`**:
    `PUT .../profile/titles` goes through `run_idempotent`, with the title's own version. A
    stale save gets 409 `STALE_INPUT_VERSION`, and an unchanged save gets 200 with no new
    version.
  - **No echo**: the error details carry only `field`, `reason` and `current_version`. The
    validation handler returns location and type, never the input (`envelope.py:104`).
  - **R11**: the new fields are codes and values. `TITLE_USE: Record<TitleUse, string>` is
    exhaustive. The person's own words come back as given, which the R11 carve-out allows.
  - **The CV deferral is recorded**: plan section 1, ADR 0015's slice C line, PROF-12
    "deferred", and PROF-07's Task 6d part closed as deferred.
- **The report's decisions and concerns, judged:**
  - *The connection removed, not kept.* This is sound. The plain line ("ESCO lists N of the
    same essential skills for both…") was already on every joined suggestion. The only thing
    the rule added was singling one suggestion out, which is what the product owner said no to.
  - *The CV's four reasons.* I checked them against the code, and they hold:
    - `interview.MAX_MESSAGE = 2_000`, `MAX_PROMPT_BYTES = 8_500` and `HISTORY_MESSAGES = 6`
      (the message plus five earlier ones) are as stated;
    - a message is sealed as typed, so a CV's referee details would need a separate input that
      removes them first;
    - the fixture interviewer reads only fixed sentence shapes (`fixture_interviewer.py`
      docstring);
    - so it fails the dispatch's "small" bar on the redaction, demo and no-live-qualification
      conditions.
  - *Acceptance run 1's two still-world failures.* These are not a defect in this slice.
    Neither fix commit after run 1 touches the world: `561f9f2` changed no world file and
    `a9dbe67` is an ADR only. So run 3 passed on the same world code that failed in run 1,
    which makes the failures timing, not code. The slice's only world change is a shorter
    caption, which can't make the moving world name nothing at all. The test's fixed 900 ms
    settle is a likely cause of the flake, and it predates this slice (Minor M10).
  - *Run 2.* The diff doesn't touch `evidence/` or `acquisition.py`, so the acquisition worker's
    unhealthy container was outside this slice.
  - *The export, the interviewer and `CLAUDE.md`.* All three gaps are honestly recorded. The
    export gap joins an existing one (Minor M9). PROF-08 stays "planned" for the interviewer.
    `CLAUDE.md` is the controller's (Minor M8).
- ⚠️ Cannot verify from diff:
  - session W2's judgement of the new words (not run, requires human);
  - VoiceOver, Safari and a real phone's keyboard (not run, requires human);
  - the implementer's `make check` and the three `make acceptance` runs (not re-run, as the
    dispatch says).

### Strengths
- A clean, complete removal of the connection: code, API fields, evaluation checks and tests
  together. The slate comparison against the recording still passes with only the `connection`
  key left out, and the JSON file is unchanged.
- `title_details` is a small, deep module:
  - the SQL stays in `profile/store.py`;
  - the module has one command, one read and one display helper (`role_marks`);
  - every rule (your title only, a listed skill only, unchanged means 200) is in one place.
- The kept-mark ruling (only newly added marks are checked) was found in self-review, proven
  RED first and tested (`test_title_details.py:172`).
- The review step's screen reuses `entered_words` by widening its input to answers by field,
  with no second word-diff. Replay and refusal behave as they do for What we know.
- The test changes are fully disclosed. Each removed assertion is about the removed rule.
- The ADR lines say the known limits plainly (the export, two spellings sharing details).

### Issues
#### Critical
None.

#### Important
- **I1. Details typed but not yet saved are lost when the person marks a skill.**
  `apps/web/src/components/TitleDetails.tsx:238` keys `DetailsForm` by `details.version`. The
  "Not part of my job" toggles (`:178`–`:186`) sit in the same title's section and stay enabled
  while the form is open. Each toggle saves the stored seniority and industry (`:181`), not the
  draft.
  - Sequence: the person opens "Add seniority or industry", types "Band 6", then opens ESCO's
    list and marks a skill before pressing Save. The mark saves version n+1, the query refetches,
    and the key changes. `DetailsForm` then remounts closed, and the typed words are gone with
    no notice. A second tab's save does the same mid-typing.
  - Why it matters: lost input is one of R14's "fix within the task" kinds. The words are short
    and optional, but they go without a trace.
  - Fix: reset the form only from what it shows, for example
    `key={`${details.seniority}|${details.industry}`}`. Or keep the draft while the form is
    open and reset it only on open, or after the form's own save. Add a component test: type,
    toggle a mark, and the draft is still there.

#### Minor
- **M1. A role or target whose title is only punctuation or emoji can't take details (500).**
  - `careerwright.concept_key` returns `''` for a title with no letters or digits, such as "-"
    (0034's function, `coalesce(…, '')`). `TextValue` accepts such a title.
  - `_views` (`title_details.py:83`–`:90`) lists the title with a version-0 view.
    `set_title_details` then inserts `title_key = ''`, which breaks 0039's
    `CHECK (title_key <> '')` (`r0039_title_details.py:28`). The `IntegrityError` isn't caught,
    so the person gets `INTERNAL_ERROR`. The failure is visible and the input isn't lost.
  - `compute_slate` already skips empty keys (`exploration.py:777`).
  - Fix: skip titles with an empty key in `_views`. They then fall to `not_your_title`.
- **M2. The marks have no CHECK.** 0039 has none for the marks' bound or shape
  (`r0039_title_details.py:32`): at most 100 (`MAX_MARKS`), no NULL elements, each once. The
  text CHECKs don't require trimmed words either. The API enforces all of this. Since 0039 is
  committed, the fix is a forward migration, for the final review:
  `CHECK (cardinality(not_part_of_job) <= 100 AND array_position(not_part_of_job, NULL) IS
  NULL)` and `seniority = btrim(seniority)`.
- **M3. PROF-11 says "verified", but its "search keeps them" part isn't built.**
  (`docs/requirements-register.md:465`.) The row itself says search keeps them "for Task 8's
  job search". The status should read "verified for display; search part T8", or the deferral
  should be recorded.
- **M4. Test gaps (not high effect: the code does the right thing).**
  - A replay is tested only for an unscreened details save (`test_title_details.py:265`). No
    test replays a screened details save or a screened decision to show the same panel again.
  - No backend test checks that an ordinary decision answers `support_note: null`.
  - No cross-actor test covers `GET`/`PUT .../profile/titles`. Both call `visible_workspace`,
    and RLS on the table is covered generically.
- **M5. The screened-entry pattern now exists three times.**
  - `put_profile` (`routes_profile.py:117`), `decide` (`routes_interview.py:250`) and
    `put_title_details` (`routes_profile.py:187`) each repeat the same block: screen, then
    `run_idempotent`, then a refusal with the panel, then a save with the panel.
  - Three `*SavedOut.saved` methods are identical (`interview_schemas.py:272`, `:324`, `:379`),
    and so are three `*RefusedOut` envelopes.
  - This is the third copy, so extract it at the final review (R13). The risk is a fourth
    copy that leaves the panel off a refusal.
- **M6. Small code notes.**
  - `routes_interview.py:214` builds the screened answers as a dict by field. In a crafted
    request that edits one field twice (refused as `edited_twice`), only the last answer is
    screened. The web never sends one. Screen a list of every edit's answer instead.
  - The unchanged check (`title_details.py:202`–`:203`) compares the marks in order, so
    reordering them makes a new version. The web only appends or removes, so this never
    happens today.
- **M7. A failed origin read looks the same as no ESCO list.**
  `TitleDetails.tsx:255` uses `origin.data?.usual_skills ?? []`. If the origin fails or is
  still loading, the role's ESCO list just doesn't appear, with no error. Low effect, since the
  origin also drives the world, but it is still failure shown as empty. Show `RequestFailure`
  when `origin.error` is set.
- **M8. Leftover words about the connection.**
  - `CLAUDE.md:44` still lists "an unexpected connection" among the revelations. That file is
    the controller's.
  - `FirstSlate`'s docstring still says "the essential skills it usually needs"
    (`exploration.py:1616`).
  - `lib/world/sound.ts:2` and `World.stories.tsx:196` still describe "a chime when a
    connection lights up". This is Task M's.
- **M9. The export doesn't carry title details.** This is recorded in ADR 0015. It joins an
  existing gap: format 4 doesn't carry target records, capability evidence or planning inputs
  either (`routes_export.py:51`). SEC-06 (T15, T16) should list `title_details` with them.
- **M10. A likely cause of the still-world flake.** `e2e/world.spec.ts:621` (`open`) and
  `:669` wait a fixed 900 ms for the moving world's names to settle. That is a likely cause of
  run 1's two "the moving world named nothing" failures. It predates this slice. For the final
  review: wait for a ready signal, not a fixed time.
- **M11. Questions for the product owner's session, not defects.**
  - The origin's `usual_skills[].not_part_of_job` has no web reader except an e2e check. The
    world and the You console draw a marked skill like any other. Should the world answer the
    mark? This is the design half's to weigh.
  - The workspace name (`WorkspaceList.tsx:55`) is typed by the person and isn't screened.
    This predates the slice and is outside it. Does "every place a person types" cover it?

### Assessment
**Task quality:** Needs fixes

**Reasoning:** The backend, the migration, the connection's removal, the support screen and the
CV deferral are correct and well tested. One web defect needs fixing before approval: toggling
"Not part of my job" silently throws away seniority or industry the person has typed but not
saved (I1). It's a small fix.
