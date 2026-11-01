# Task 6d slice A review: the target-record half

Reviewer: target-record half (dispatch `task-6dA-review-dispatch.md`). Commits 1577db2 and
8ad36a6 on top of 86d7ead. Read in full: migration 0034, `profile/targets.py`, the
`records.py` and `store.py` additions, `titles.py`, `sketch.py`, `capability/commands.py`
(with the removed `matrix.py` resolvers), `strengths.py`, `choose_target` and the slate's
target hunks in `exploration.py`, `profile/commands.py`, `cli.py`, the API routes and
`TargetRecordOut`, `deps.py`, `tools/evaluation.py`'s target hunk, the web consumers
(`Directions.tsx`, `SketchCard.tsx`, `WorkspaceShell.tsx`, `queries.ts`, `world/model.ts`,
the coverage words in `vocabulary.ts`), the target tests (domain, integration, migrations,
capability) and the ADR 0015, 0012 and 0007 amendment lines. The facts half was skimmed only
where it touched targets.

Focused checks outside the diff, one per named risk:
- Older pinned profiles: `_pinned_document` (`profile/exploration.py:635`) reads the run's own
  profile version, and `discovery_slate` and `submit_explanation` pass that document to
  `stored_targets` (`exploration.py:728-729`, `:1166`).
- Other stored keys: `concept_key` appears only in migrations 0008 (one expression index, the
  provisional-title trigger) and 0034. No Python path writes a key except `target_records`.
- The accent table: Python check, no stack. 162 letters on each side, and each maps to its NFKD
  base in lower case.
- The old pack-title key: `uv run python -c` on `evidence.jobs.title_key`, no stack.
  "Registered nurse (adult)" gives "registered nurse".
- Write paths: every `commit_profile_version` caller that can change the targets passes `pack`
  (conversation, `write_profile`, `revert_profile`, `choose_target`). `choose_role` changes only
  the role. Only `cli.py:187` writes a profile version outside it, and the seed records it.
- The worker role: no worker path reads `target_records`. The readers are the API (routes for
  discovery, capability, planning and the origin) and the offline evaluation.
- RLS: the policy is the same shape as `profile_versions` and `source_references` (migration
  0001).

No suites were re-run (the dispatch says so). The implementer reports that `make check` and
`make acceptance` passed. I didn't re-run them.

### Spec Compliance
- ❌ Issues found:
  - "Existing profiles migrate forward: a stored target title gets its record" is met only for
    each workspace's latest profile version. A discovery pinned to an older version whose target
    is no longer in the latest one now fails with `INTERNAL_ERROR`. See Important 1
    (`r0034_target_records.py:165-175`, `targets.py:186-192`).
- ✅ Everything else in this half:
  - Each target is stored once, with its occupation, its link source and its coverage.
  - One `resolve_target` replaces the four resolvers (`find_pack_target` and `pick_occupation`
    are deleted, along with `titles.targets`', `sketch._chosen`/`_target`'s and
    `capability._chosen`/`_seed`'s own rules).
  - The slate, the sketch, the strength, Skills and the world read the record.
  - `concept_key` folds "&" and accents in a forward migration, which also rebuilds the
    index.
  - Real ESCO titles are tested: "food & beverage supervisor", "façade cleaner" and
    "dance répétiteur" on the full release, plus the sample's two.
  - The coverage line is shown in the sketch and in `TargetSaved`.
  - Skills seeds from the record.
  - The CHECKs already allow `ons` and `none_of_these`.
- ⚠️ Cannot verify from diff:
  - The full-release slate equality (`test_every_evaluation_case_s_slate_is_the_one_before_…`)
    and the acceptance runs. These are the implementer's runs, not re-run here.
  - The coverage line's words: not run, requires human (session W2).

### Strengths
- `decide` is pure, and it is the only place the rules live.
  - The migration test asserts that the backfill and `resolve_target` agree title for title
    (`test_migrations.py`, `stored == decided`).
  - A domain test pins the migration's pack constants to the committed pack.
  - Another pins the accent table to `unicodedata`.
- `TargetRecord.esco_occupation` puts "the pack's crosswalk seeds Skills only" in one place.
  - So DSC-11, 12 and 14 keep their "couldn't match" join, and Skills keeps its crosswalk
    seed.
- The CHECKs encode the record's invariants, not just its domains:
  - a link names its occupation;
  - a choice cites its source;
  - an exact label is the one label match;
  - a crosswalk link is a pack target.
- Failure is never an empty success here:
  - A target with no record is `INTERNAL_ERROR`, never "names nothing".
  - A record naming a pack target the pack lacks is `INTERNAL_ERROR`.
  - `commit_profile_version` refuses to save targets without the pack.
- Ruling 5 fixes a real defect. The sketch's "Use bookkeeper" for an ambiguous "bookkeeper"
  used to change nothing, so the sketch kept asking. The choice is now recorded.
- The web keys "already a target", `TargetSaved` and the world's destinations by the record.
  None of them compares titles any more.
- RLS, grants and the composite source FK match the existing per-workspace tables. No DELETE
  grant is needed, because records are never deleted and the workspace delete cascades.

### Issues

#### Critical
None.

#### Important
1. **A discovery pinned to an older profile version can stop opening after the upgrade.**
   - Where: `r0034_target_records.py:165-175` (`latest` and `titles` backfill only each
     workspace's newest profile version), with `exploration.py:728-729` and `:1166`, and
     `targets.py:186-192`.
   - What happens: the slate is recomputed on every read from the discovery's pinned
     document, and `stored_targets` raises `INTERNAL_ERROR` for any title without a record.
     Any workspace made before 0034 can hit this. Its latest discovery was pinned to version N.
     After that, a target was removed or replaced by a title with a different concept key: a
     direct edit, a revert, or the sketch's "Use X" on a close match. That old target has no
     record, so the slate fails to open and so does "Why this could suit you".
   - Effect on the person: the You chapter shows an error where their suggestions were. The
     only way forward is a new discovery, which costs a model call in live mode.
   - Why it is Important: it breaks the brief's "existing profiles migrate forward". The
     migration test covers only a one-version profile.
   - Fix, either way:
     - Backfill every target title of every profile version. Do each workspace and concept
       key once, with the spelling from the latest version that holds it, by the same rules.
     - Or backfill at least every version a run pins.
   - Then add a migration test: a discovery pinned to version 1, with a target replaced in
     version 2, still has a slate after 0034.
   - Delivery: amend 0034 if the controller confirms no lasting database has applied it.
     Otherwise ship it as 0035, with `ON CONFLICT DO NOTHING`.

#### Minor
1. **A record freezes inputs that used to be read live, and nothing notices when they
   change.**
   - Where: `targets.py:140-162`, `r0034_target_records.py:114`,
     `capability/commands.py:177-188`.
   - (a) Pack and reference versions: `pack_version` is stored but never read. A later pack
     or capability-reference version that adds a target, or moves a crosswalk, leaves existing
     records with the old coverage or the old crosswalk occupation, silently. Skills is then
     seeded from an outdated occupation. ADR 0015's line covers only "a pack that drops a
     target".
   - (b) No taxonomy held: `record_targets` doesn't call `held_release`. A target saved while
     no taxonomy is held is stored as matching nothing, and stays that way after the import.
     Setup now imports the taxonomy first, so this is unlikely in L0.
   - (c) A later role choice: an occupation chosen later for the current role no longer
     reaches a target saved earlier, though it does reach one saved after.
   - Also, `test_targets.py:132-139` compares the historical migration's constants with the
     current committed pack. The first pack bump will fail it, and that invites editing 0034.
   - Fix:
     - On read, compare `record.pack_version` with the committed pack and re-decide or refuse
       with a code.
     - Pin that test to pack 0.1.0's files.
     - Say in ADR 0015 what re-decides a record.
   - Latent today: L0 pins one pack and one release.
2. **Bracketed qualifiers no longer reach a pack target by title.**
   - Before: Skills matched pack titles by `title_key`, which folds bracketed notes. So
     "Registered nurse (adult)" reached P03, and so did "IT support technician (2nd line)".
   - Now: the concept key gives "registered nurse adult". It is not covered, and its
     coverage line says "can't check skills, options or routes".
   - In return, "Registered nurses" now matches.
   - Where it's recorded: only in the report's ruling 1. ADR 0012's amendment line doesn't
     say so.
   - Fix: name it in the ADR 0012 line. Whether a bracketed qualifier should fold for pack
     titles only (it is not a slate rule, so R11 doesn't bind it) is a question for the
     product owner. UK nursing roles are often written "(adult)" or "(mental health)".
3. **Room for slice B: only a choice may cite a source** (`r0034_target_records.py:124-126`).
   - The CHECK `(link = 'occupation_choice') = (source_ref_id IS NOT NULL)` means a record
     can cite a source only when it is a choice.
   - If slice B's "None of these is my job", or a pick from the ONS list, should cite the
     person's decision as a source, that needs a second migration.
   - Decide now, while 0034 is unreleased. Either relax it to "a choice cites its source",
     or record that `recorded_by` and `recorded_at` are the provenance for those links.
4. **One name, two keys.** The column `target_records.title_key` holds a concept key.
   `careerwright.evidence.jobs.title_key` is a different key, and `_matrix` uses it for
   Skills' evidence right next to `record.key` (`capability/commands.py:158`). Rename the
   column (`concept_key`) while 0034 is unreleased, or comment it.
5. **The next key change must re-key the records.** The docstring says "no other stored value
   holds a key made before this one" (`r0034_target_records.py:9-11`). After 0034,
   `target_records.title_key` holds keys, and any later change to the key must re-key it
   (merging rows that collide on the primary key). Say so in the function's COMMENT or in
   ADR 0015's line.
6. **The web treats "not loaded yet" or "failed" as "no targets".**
   - Where: `Directions.tsx:668`, `world/model.ts:48`.
   - While `GET .../targets` loads or fails, the world draws no destinations, and each
     suggestion offers "Make this a target" again. The server's no-op 200 corrects it on the
     next read.
   - Effect: low, because the profile still lists the targets. But a failed read looks like
     an empty world.
7. **ADR 0007's line says decision 13's rule is "unchanged".** Its concept key now folds "&"
   and accents for the role, the title ideas and searches-as-titles. The brief asked for this,
   and the evaluation slates are unchanged, but the line should say it.

### Answers to the dispatch's questions
- **"Bookkeeper" is now ambiguous in Skills until the person picks one. Correct and honest,
  or a regression?** Correct and honest, not a regression the person would feel.
  - One rule had to go. You, which R11 freezes, keeps several as several. So Skills' "prefer
    the preferred label" step was the one to drop, and "nothing is guessed" is the
    invariant.
  - The person is asked: the sketch shows the occupations, each with its own "Use …"
    button. Their choice now sticks, where before it was a no-op, and then reaches P05
    through the crosswalk (`test_capability.py`).
  - Skills has no web view yet, so no screen loses anything today.
  - The cost: a typed or chat-proposed "bookkeeper" needs one click before Skills or
    planning cover it. Until then the coverage line truthfully says Careerwright can't check
    it yet.
- **Room for slice B without a second migration:** yes for the kinds (`ons` with SOC and
  ISCO codes, `own_words`, `none_of_these`). The open question is citing a source (Minor 3).
- **Re-keying:** complete as of 0034. The index is rebuilt, and the records are written with
  the new key, in the same script.

### Questions for the product owner or session W2 (not findings)
- The pack-target line, "Careerwright can check skills, options and routes for this role", is
  the brief's own wording. Options and Routes aren't reachable in the web yet. Is "can check"
  true enough at session W2?
- Should bracketed qualifiers ("Registered nurse (adult)") count as the pack title? (Minor 2.)

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The design is sound: one decision, one record, CHECKs that hold its
invariants, and every consumer reading it. But the forward migration misses target titles
that only older profile versions hold, so a pre-0034 discovery can stop opening with
`INTERNAL_ERROR`. That is a small backfill fix with one migration test.
