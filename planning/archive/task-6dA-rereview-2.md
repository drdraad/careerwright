# Task 6d slice A, fix round 2: scoped re-review

Commits c78509c, e9e4e53 and 59095b8 (6c9e0a8..59095b8). I read the fix list
(`task-6dA-fix-round-2.md`), the report's "Fix round 2" section, and the whole 956-line diff.
I read code outside the diff only to check a named risk, one check per risk:
- **Does a read now store?** `resolve_target`'s helpers only read: `concept_keys`,
  `store.occupation_choices` (`profile/store.py:156`), `preferred_keys` (`taxonomy_store.py:394`)
  and `label_match_uris` (`:378`).
- **Is the pack loaded somewhere new?** `deps.pack_targets` (`api/deps.py:57-60`) already
  existed (slice A, 1577db2). It is a pure view of the pack and reference data the API loads
  and checks at startup. `capability/commands.py:94` `pack_targets` does no I/O.
- **Is there another caller, or a worker path?** I grepped every caller of the changed
  readers. Only the API routes and `capability_view` call them. The worker and
  `tools/evaluation.py` call none of them.
- **Can the guard be bypassed?** The only raw insert into `profile_versions` is inside
  `insert_profile_version` (`profile/store.py:286-298`). `seed_fixture`'s only production
  caller is `seed` (`cli.py:215-219`).

No suite was re-run, and no test was run.

### Spec Compliance
- ✅ Spec compliant. Each finding the fix list asked for now:
  - **Important 1 (a target with no record said "couldn't match"): addressed.**
    - `stored_targets` decides a title with no record by the one `resolve_target`
      (`targets.py:209`). The round 1 fallback record is deleted. There is no second matcher,
      and nothing is stored on a read.
    - Test: `test_targets.py:239`. It reads targets, sketch, matrices and readiness, takes both
      records away, and reads again. The reads must be equal and the records still missing.
      The report gives RED on round 1's code.
    - The 0034 assertion now reads true: "Saute cooks" is no longer unmatched at 0034
      (`test_migrations.py:509`). The slate decided on read equals the slate from 0035's
      stored records (`:510`). The change is disclosed.
    - The 0034 and 0035 tests now read the records from the table (`held_records`, `:389`), so
      a read that decides can't hide a missing row. That is right.
  - **Minor 1 (the sketch test hid the steps): addressed.**
    - `SketchCard.test.tsx:160-162` renders the three steps the API sends.
    - `:177` checks each target's own block (the title line's parent `div`) for "Not
      researched".
    - `:179-182` expects step 2's words unchanged.
    - RED is given (the old words fail the per-block check).
  - **Minor 3 (one record, two spellings): addressed.** ADR 0015 (`:198-201`) says both
    spellings share one key, and whichever is saved first stands for both. That is accurate:
    the concept key splits on brackets, and the bracket rule reads them.
  - Minor 2 and Minor 4 were carried to slice B and the final review. Not checked here.
- **The three questions:**
  - **Does any read path now store? No.** The only change on the read side is
    `targets.py:209`, and every helper `resolve_target` calls is a SELECT.
  - **Can deciding on read change a pinned past slate? No.**
    - At head, 0035 and every write path give each saved title a record, so a read decides
      only for a row that is missing.
    - When it does, it gives what would have been stored. `record_targets` passes a choice
      only for the title just chosen, and a read passes none, so both reach the same
      `resolve_target`. The 0035 test shows the two slates are equal (`:510`).
  - **Does passing the pack's targets to every reader add a pack load where the pack may be
    missing? No.**
    - Every route passes `deps.pack_targets`, built from the pack the API loads at startup.
      The API refuses to start without it, so a request can't run without it.
    - `capability_view` uses its own `data`.
    - No worker path or offline tool calls the changed readers.
- **The implementer's concern (the three guard tests also pass on round 1's code):** expected,
  and not a gap.
  - They guard a rule that already holds, so no code where it holds can make them fail. What
    matters is whether each fails when the rule breaks. By reading, each does on its own path:
    - **The architecture test** (`test_boundaries.py:226`, `:241`) fails on any new function
      in `careerwright` that calls `insert_profile_version`. Raw SQL can't route around it:
      SQL is confined to the store modules, and the one raw insert is inside
      `insert_profile_version`.
    - **The write-path test** (`test_targets.py:264`) reads the tables. It fails if a direct
      edit, a choice or a revert stops storing records. It takes a record away before the
      revert (`:289`), so the revert has to store it again.
    - **The seed and reset test** (`:303`) fails if `seed` or `reset_demo` stops calling
      `_record_fixture_targets`.
  - No break was made on purpose to watch them fail. So "would fail" rests on reading the
    code, not on a run.
- ⚠️ Cannot verify from diff:
  - `make check` (exit 0) and `make acceptance` (exit 0: 364 backend, 56 journeys) are the
    implementer's runs.
  - The RED runs of the integration tests.
  - The sketch and coverage words: not run, requires human (session W2).

### Strengths
- The fix is the smallest true answer. The round 1 fallback is gone, and its constructor and
  imports went with it.
- The read test proves both halves of the ruling in one place: the read matches what would be
  stored, and the table is unchanged afterwards.
- The migration tests switched to reading the table, so they still prove what 0034 and 0035
  stored, not what a read can work out.
- Each guard reads the tables themselves, and each says why an API read can't show a missing
  record.

### Issues

#### Critical
None.

#### Important
None.

#### Minor
1. **The guard admits the fixture writer, whose recording happens in its callers.**
   (`test_boundaries.py:226-231`, `cli.py:205-212`)
   - `_create_fixture_workspace` is allowed to write a profile version, but its records are
     stored by its callers (`seed`, `reset_demo`).
   - `seed_fixture`, used by the migration tests, writes the fixture's version without
     records, by design.
   - Nothing stops a future command from calling `seed_fixture` alone. Its targets would then
     be decided on every read, silently. Low risk: today only `seed` calls it.
   - **Fix (final review):** record the targets inside `_create_fixture_workspace`, or keep
     `seed_fixture` test-only and say so in its docstring.
2. **The guards were not shown to fail.** No break was made on purpose, for example removing
   `record_targets` from `commit_profile_version`, to watch each guard fail.
   - **Fix (final review):** one such run per guard, noted in the register row as other rows
     note theirs.

### Assessment
**Task quality:** Approved

**Reasoning:** A title with no record is now decided on read by the one resolver: true, never
stored, never an error. It can't change a past slate, and it loads nothing the API doesn't
already hold. Minors 1 and 3 are done as asked. The two Minors left are guard polish for the
final review.
