# Task 6d slice A, fix round 1: scoped re-review (both halves)

Commits 1cd1905, 9680f18, 1ab608f and 6c9e0a8 (38f9998..6c9e0a8). I read the contract, both
reviews, the fix list, the resume note and the report's "Fix round 1" section. Then I read the
whole 1,282-line diff in three passes. I read code outside the diff only to check a named
risk, one check per risk:
- **Does 0035 match 0034 and `resolve_target`?** I compared `FILL_IN` with 0034's `BACKFILL`
  line by line, and both with `decide` and `label_match_uris` (`taxonomy_store.py:378`).
- **Could the re-decision change a pinned slate?** The slate reads only a record's ESCO links
  and label matches (`titles.py:60-66`, `records.py:142` and `:174-176`).
- **Can the re-decision break a CHECK?** I checked each CHECK against `QUALIFIED`'s SET lines
  (`r0034_target_records.py:121-139`).
- **Can an older version hold a title the table refuses?** Titles have been 1 to 120
  characters since the first `document.py` (a31fd42), so `FILL_IN` can't fail the title CHECK.
- **Is there any other `INTERNAL_ERROR` for a missing record?** I read every raise in
  `profile/`, `capability/` and `api/`.
- **What does the person read when a record is missing?** I traced it through
  `exploration.py:757-879` to `vocabulary.ts:637`.
- **Is the bracket pattern the old one?** Yes. `evidence/jobs.py:52` is the same pattern.
- **Which nursing field is the pack's nurse target?** Its sources are adult nursing (BNurs
  Adult Nursing).

No suite was re-run, and no test was run.

### Spec Compliance
- ❌ Issues found: one new Important (the missing-record fallback, below). Each of the four
  fixes is addressed:
  - **Facts I-1, a pack role's sketch said "Not researched": addressed.** The research status
    now depends on the match and the coverage. It is an exhaustive map over both
    (`vocabulary.ts:760-775`), shown through `ResearchStatus` (`SketchCard.tsx:57-62`, `:129`).
    - Tests that fail without the fix: `SketchCard.test.tsx:144-172` (all three titles) and
      `discoveryWords.test.ts:376-386` (the old map's entries aren't functions).
  - **Targets Important 1, the backfill: addressed.** 0035 (`r0035_every_version_s_targets.py:74-157`)
    records every target title of every version. 0034 is untouched.
    - `test_migrations.py:430-525` reproduces the reviewer's case: a discovery pinned to
      version 1, with targets replaced in version 2.
    - After head, both the slate and the note open. Every record equals `resolve_target`'s
      decision (`:500`).
    - The report's RED is HEAD's `INTERNAL_ERROR` at 0034.
  - **Targets Minor 2, the bracket rule: addressed.** It lives inside the one `resolve_target`
    (`targets.py:44-51`, `:91-94`, `:133-134`), and the whole title still comes first.
    - It uses the old `title_key` pattern. ESCO labels are still matched by the whole title,
      so the slate's rules are unchanged.
    - Tests: `tests/domain/test_targets.py:114` (including the whole-title-first case) and
      `:161` (the pattern and pack constants equal 0034's), plus
      `tests/integration/test_targets.py:173`, which checks the record, the sketch and Skills.
    - The ADR 0012 line is updated.
  - **Facts M-2, unknown counted as zero: addressed.** `slate_facts.py:277-279` and
    `exploration.py:821` make the count null. An idea that was searched keeps its count,
    0 included.
    - Test: `test_discovery.py:708`. It would fail with 0.
    - No consumer reads the count: `tools/evaluation.py:330` and `vocabulary.ts:745` read only
      the outcome.
- **Migration 0035:**
  - **Forward-only:** `downgrade` raises, and `down_revision = "0034"`.
  - **Safe after 0034:** it adds no DDL and only fills in or updates rows.
  - **Idempotent:** `ON CONFLICT DO NOTHING` (`:156`). `QUALIFIED` skips any record already
    decided by title (`:171`), so a second run changes nothing.
  - **Row-level security** is unchanged. The new rows are read back through the API's role in
    the migration test.
  - **CHECKs hold:**
    - `QUALIFIED` sets the coverage, target and basis together.
    - It turns the link from `none` to `pack_crosswalk` only together with the occupation.
    - It leaves a choice's source and an exact label's match alone.
  - **`FILL_IN` agrees with `decide`:** its whole-title-then-unqualified join
    (`coalesce(w, u)`) and its `crosswalk` are `decide`'s order.
- **Ruling 1 (0035 re-decides records the bracket rule now reaches): sound.**
  - Without it, a "Registered nurse (adult)" stored by 0034, or by the code since, stays "not
    covered" for ever, and `resolve_target` disagrees with its own record.
  - It changes only the coverage. It changes the link only from none to the crosswalk, which
    is what `decide` gives today.
  - Nothing a person chose is rewritten: a choice keeps its occupation and its source.
  - No pinned slate changes. The slate reads only ESCO links (choice, exact label) and label
    matches (`titles.py:60-66`), and `QUALIFIED` changes neither. `pack_crosswalk` is not an
    ESCO link.
  - What does change: Skills' pack target for the records it reaches. That is the intended
    restoration.
- **Ruling 2 (a title with no record reads as naming nothing): not sound as built.** It reads
  as "Careerwright couldn't match it", where no match was tried. See Important 1.
- **No missing record becomes `INTERNAL_ERROR`: met.**
  - `stored_targets` was the only such path.
  - The capability check at `capability/commands.py:177-187` is for a record naming a pack
    target the pack lacks: a stale record, not a missing one.
  - `commit_profile_version`'s check (`profile/commands.py:162-167`) catches a programming
    error. It is not about a missing record.
- **The sketch for the three pack roles:** no line about the target contradicts the coverage
  line. Each card reads:
  - "Registered nurse: Careerwright couldn't match it in ESCO" (or "Your own title: …" for a
    provisional "Bookkeeping assistant");
  - "Careerwright can check skills, options and routes for this role.";
  - "Closest in ESCO: Use …" for an unmatched one;
  - and no research line.

  The shared step 2 still says "Not researched yet: no providers, prices or dates". I read it
  as "able, but not done yet", not as a contradiction. See Minor 1 and the session W2 question.
- ⚠️ Cannot verify from the diff:
  - `make check` and `make acceptance` are the implementer's runs. Acceptance's backend half
    had 1 failure (`test_acquisition.py`, a one-minute backoff), which passed when re-run
    alone. The controller is re-running acceptance whole.
  - The RED runs of the integration tests.
  - The coverage and sketch words: not run, requires human (session W2).

### Strengths
- Each fix is at its cause:
  - the words depend on the coverage, not just the match;
  - the backfill covers every version;
  - the bracket rule sits inside the one resolver, not in a second matcher;
  - the count is nullable in the fact itself.
- The migration test reproduces the reviewer's case end to end through the API and the row
  security policy.
  - It checks `stored == decided` across both versions.
  - It covers both bracket forms in SQL: "[2nd line]" through `FILL_IN`, and "(adult)"
    through `QUALIFIED`'s re-decision of a record 0034 stored.
- The duplicated constants and pattern in 0035 are pinned to 0034's and to `targets.QUALIFIER`
  by a domain test.
- The test-input changes are disclosed and leave the old assertions intact. For example, the
  sketch test gained a third target so the "Not researched" words are still tested.

### Issues

#### Critical
None.

#### Important
1. **A target with no record says "Careerwright couldn't match it" where no match was tried
   (ruling 2).** Latent today.
   - **Where:** `targets.py:206` and `:212-226`; `exploration.py:757-758`, `:873` and `:877`;
     `vocabulary.ts:637-638`. The test that pins it: `test_migrations.py:494-497`.
   - **What happens:** the fallback record names no occupation, has no label match and is not
     covered. The slate then treats the title as unmatched:
     - it joins no work through that title, so it silently gives fewer suggestions;
     - when the slate is short, it tells the person: "Careerwright couldn't match '…' to an
       occupation in ESCO … Choose the ESCO occupation closest to it."
   - **The test asserts the untrue reading.** At 0034, `unmatched_titles == OLDER_TARGETS`
     includes "Saute cooks", which the same test shows is ESCO's "sauté cook" once it has a
     record.
   - **Why it is Important:**
     - The dispatch's own check is that "not resolved" never reads as "no match exists" where
       no search was run.
     - It breaks "failure is never an empty success" and "unknown is never none" (`CLAUDE.md`).
     - It removes the only guard on "every saved target has a record". The original
       `INTERNAL_ERROR` would fail loudly if a future write path skipped `record_targets`, or
       a future key change didn't re-key the records (the targets review's Minor 5). Now that
       mistake shows a false sentence and a thinner slate.
     - **Reachability today:** none that I found. Every write path records its targets
       (`profile/commands.py:168`, `cli.py:202`), and 0035 fills in the past.
   - **Fix, either way:**
     - **Option A:** decide a missing record on read with `resolve_target`, without storing
       it. That uses the same rules, gives a true answer and never errors. The readers
       would need the pack.
     - **Option B, the smallest change:** say nothing about such a title. Keep it out of the
       "couldn't match" reasons and the label-match count.

     Either way, change the 0034 test's assertion to match. Restoring the loud failure, now
     that 0035 closes every known gap, is the controller's call, because the fix list ruled
     out an error.

#### Minor
1. **The new sketch test hides the steps** (`SketchCard.test.tsx:158` and `:171`).
   - It passes `steps: []`. The real API always sends the three steps when there is a target
     (`sketch.py:166`), and step 2 says "Not researched yet: no providers, prices or dates"
     (`vocabulary.ts:788`).
   - So the real card for a pack role would fail the test's own `/Not researched/` check. The
     test proves the target's block only.
   - **Fix:** scope the check to each target's block, or render the steps and expect the step
     line by name.
2. **The bracket rule also folds a qualifier that names a different field.**
   (`targets.py:46` and `:91-94`)
   - "Registered nurse (mental health)" or "(children's)" reaches the pack's "Registered nurse".
     That target's sources are adult nursing, yet the person reads "Careerwright can check
     skills, options and routes for this role."
   - This is the behaviour from before slice A, and the fix list asked for it back. Skills,
     Options and Routes have no web view yet, so the person sees only the coverage line.
   - **Fix:** a question for the product owner (below).
3. **One record, two possible decisions.** (`targets.py:177`, `r0035:170`)
   - The key turns brackets into word breaks, but the bracket rule reads them. So "Registered
     nurse adult" and "Registered nurse (adult)" share one record yet would decide differently.
     Whichever is saved first stands.
   - The report discloses this. It is rare.
   - **Fix:** say it in ADR 0015's line.
4. **No test covers `QUALIFIED` keeping a choice or an exact-label link**
   (`r0035:166-168`). The migration test exercises only the `none` branch.
   - **Fix (final review):** add one bracketed title that holds a label match.

### Questions for the product owner or session W2 (not findings)
- Should a qualifier that names a nursing field ("(mental health)", "(children's)",
  "(learning disabilities)") reach the pack's adult "Registered nurse" target, or only a
  neutral one like "(adult)" or "[2nd line]"?
- On a pack role's sketch, does step 2's "Not researched yet: no providers, prices or dates"
  sit right beside "Careerwright can check skills, options and routes for this role"?

### Assessment
**Task quality:** Needs fixes

**Reasoning:** All four fixes are addressed at their cause, with tests that fail without them,
and 0035 is safe, idempotent and leaves people's choices and past slates alone. One new
Important: the fallback ruled for a missing record says "Careerwright couldn't match it" where
nothing was tried, and a test pins that. It is latent today but removes the guard on the one
invariant this slice relies on.
