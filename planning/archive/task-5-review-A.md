# Task 5 review, half A (taxonomy): 10afdbf..56db48f

Reviewer scope: catalogue module, r0004 migration, ESCO pin/fetch/sample tooling, English
cities, provisional concepts, dataset tooling, Makefile/compose/setup, dependency and licence
notes, and their tests. I read the diff in seven passes (lines 1-520, 520-865, 865-1240,
1240-1440, 1440-1785, 1785-2185, 2185-2662). Outside the diff I made one focused check per
named risk (listed below). I ran no test suites and made no live calls. I ran two read-only
offline probes (`python3 -I`, scripts in my scratchpad) over the gitignored
`var/datasets/esco-v1.2.1-classification-en-csv.zip` and the committed sample.

### Spec Compliance
- ✅ Spec compliant for half A (S2.1). Two notes:
  - "Reviewed finite English-city list": the list is delivered. The review of its ONS regions
    is correctly recorded as provisional and needing a human (ADR 0006 decision 4). I checked
    all 55 region assignments against ONS E12 regions and found no factual errors (details
    below).
  - "Corroborated titles outside ESCO": implemented as user-verified titles, which matches
    spec §4 DIV-1 ("Verified user-supplied titles absent from ESCO remain provisional internal
    concepts"). Corroborating model-suggested titles (DIV1-04) is left to T6 and documented
    in `backend/src/nessa/profile/concepts.py:8-9`.
- Named-risk checks (what I checked):
  - **ESCO pinning.** `esco.py:59-71` pins v1.2.1 by URL, size and SHA-256. My probe hashed
    the local file and got `f9761b0b…deb3e`, 10,045,670 bytes, which matches the pin. The
    sample hashes to `747c5638…955d`, 76,049 bytes, which matches `tests/support/esco.py`.
    `read_verified` (`esco.py:179-190`) checks size and hash, then parses the same bytes it
    hashed (no TOCTOU). `cli.py:181-190` verifies before parsing.
    `tools/datasets.py:36-61` streams to a temp file, enforces the size cap while streaming,
    then renames. Tests cover a flipped bit, truncation, oversize, HTTP 404
    and "no partial file remains". Raw data is not committed: `/var/` is gitignored and
    `git ls-files` shows only the sample (76 KB) and its README. The sample is labelled
    `sample` in the pin, the database and the API, and is marked as a modified version.
    Attribution and licence are in `docs/dependencies.md:167`, and the API returns the
    attribution with the manifest, every search and every occupation.
  - **Full import.** My probe of the release found:
    - every concept is `released`;
    - no duplicate occupation-skill or skill-skill pairs (126,051 and 5,818 rows, matching
      the test);
    - no occupation with two broader rows, so `occupation_broader`'s primary key and
      `one_or_none()` at `taxonomy_store.py:243-256` are safe;
    - 3,043→3,039 occupations and 13,960→13,939 skills (4 and 21 repeats).

    Re-import is idempotent: `cli.py:186` pre-checks and `taxonomy.py:28-38` re-checks
    under `LOCK TABLE … EXCLUSIVE`. The import is transactional: one `engine.begin()`, with
    COPY on the same DBAPI connection. "Previous taxonomy intact" holds because a different
    release is refused before any write. Atomicity on mid-import failure is untested (Minor 5).
  - **Full-text retrieval.** The search uses the `english` config throughout. Every input is
    a bound parameter, and the f-strings only splice constants (`taxonomy_store.py:184-185`).
    `match=all` uses `websearch_to_tsquery`, which never raises on syntax. `match=any`
    rewrites `plainto_tsquery` output (which cannot contain spaced `&` inside a lexeme) and
    is never raw `to_tsquery` on user text. `q` is limited to 200 characters and `limit` to
    1-50, in both the route (`routes_taxonomy.py:48-49`) and the domain (`taxonomy.py:70`).
    `label_matches` has no limit, but the pinned data bounds it: my probe found a maximum of
    6 occupations sharing one normalised label (999 shared labels in total, which matches ADR
    0006). Ranking uses `ts_rank_cd` with A>B>C>D weights; the test shows "repair bicycles"
    ranks bicycle mechanic first. The error cases are distinct:
    - an unknown term is a complete 200 with `full_text_total: 0` and the release;
    - a query with no lexemes is a 422 with `no_search_terms`;
    - no taxonomy is a 503 with `TAXONOMY_UNAVAILABLE` (`envelope.py:33`).

    One observation: a negation-only `match=all` query (`-cook`) returns an unranked page of
    every other occupation. This is honest websearch semantics, not a defect.
  - **Scope and grants.** The ESCO tables are global reference data. They have RLS enabled
    with a `FOR SELECT TO nessa_api USING (true)` policy and only SELECT granted
    (`r0004:135-148`), and no grant to the worker. `provisional_concepts` uses the same
    workspace policy as `source_references` (`r0001:148-150`), with SELECT and INSERT only.
    A composite FK ties its source to the same workspace, and it cascades on workspace
    delete. Isolation is tested through the API (404 for another account). There is no
    database-level test (Minor 6).
  - **Provisional concepts.** "Corroboration" means the person's explicit confirmation,
    recorded as a `direct_entry` source. The record has no ESCO URI or ISCO fields, and
    `/v1/taxonomy/occupations/{id}` returns 404 for one. An ESCO label is refused both by the
    application (422 `in_taxonomy`) and by a trigger. Two gaps: the "not in ESCO" check is
    exact on case and spacing only (Minor 1), and the output object has no explicit
    provisional marker (Minor 11).
  - **55 cities.** The count and membership match GOV.UK's England list, including the 2022
    awards (Colchester, Doncaster, Milton Keynes, Southend-on-Sea). All 55 E12 regions are
    correct, including the easily confused ones: Milton Keynes SE, Peterborough EE, Carlisle
    NW, Hereford WM, Gloucester SW, Ripon YH, Ely EE, St Albans EE, Chester NW and Salisbury
    SW. The E12000001-9 code-to-name map is correct. The `sorted(_REGIONS)` unpacking at
    `places.py:59` maps the codes in the right order.
  - **`make setup` fetch.** The download happens only in `tools/setup.py` via
    `datasets.main([])`. It exits 1 with the manual step if the file cannot be had, and the
    runbook manual step is at `docs/runbook.md:104-111`. `make check` only uses a
    `MockTransport` (`tests/tools/test_datasets.py`). The migrate container mounts
    `./var/datasets:ro` and imports offline. A missing file fails `setup-database` loudly,
    and a missing file in acceptance fails the full-release test rather than skipping it.
  - **Tests.** They test behaviour, mostly against the real sample and real PostgreSQL. I
    traced plausible regressions through them:
    - removing the alias-exclusion, the hidden-label masking, the default match mode, the
      API-role grants, the trigger, the app-level ESCO check (500 instead of 422), the
      download size cap, the temp-file rename or the re-verification of a present file each
      makes a test fail;
    - the full-release test pins exact counts.

    The gaps are atomicity, transformation-version drift, DB-level provisional isolation and
    two shape tests (Minor 3, 5, 6, 7).
- ⚠️ Cannot verify from diff (half B owns these):
  - the InterviewTurn contract via the Meta model port, bounded validation repair, proposed
    patches with source message references, and explicit hard-constraint confirmation;
  - direct edits and chat sharing `commit_profile_version`, and never committing partial
    streamed JSON;
  - the deterministic fixture adapter, the failure tests (invalid schema, refusal,
    truncation, unavailable model, budget exhaustion, stale concurrent writes), and "old
    profile survives";
  - ADR 0004 decision 7 (expected profile version), MODEL-02 closure, the live-smoke ledger
    row and R5 cost, and client regeneration and drift;
  - city storage: the profile stores a city by its label, not `place_id`
    (`profile/document.py:236-242`). Half B should judge this against spec §3 "Resolve cities
    to stable geographic IDs".

  I did not re-run the implementer's `make acceptance` results (149 passed, full import about
  5.8 s, stack ESCO test). The register rows marked "verified" rest on them. Side
  observation: the CLAUDE.md retry-owner sentence is textually unchanged in the range
  (carry-forward item).

### Strengths
- The release is fail-closed end to end. Fetch, mount and import each verify the pinned size
  and hash. The parser refuses unknown structure, unknown relation targets and conflicting
  repeated rows, and counts the benign repeats in the manifest instead of choosing silently.
- The identity model follows TAX-1: UUIDv5 concept IDs from the ESCO URI, the ISCO-08 chain
  as a pivot, specialists in one group kept distinct, and a database CHECK enforcing the
  ISCO prefix hierarchy.
- Retrieval keeps failure distinct from empty (GC6). Totals stop a page being read as the
  whole result, and shared labels return every holder. Hidden labels match but are never
  displayed.
- Least privilege: ESCO is read-only to the API and written only by the migration owner.
  Provisional concepts follow the existing workspace RLS pattern, with a same-workspace
  source FK and a DB trigger as a second guard.
- The sample is small, labelled, hash-pinned, deterministic and marked as modified. Its rows
  are value-identical to the release's (my probe), and the README explains how it was
  derived.
- No new dependencies. `httpx2` is pre-existing. SQL stays in the adapter registered in
  `test_boundaries.py`.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
1. **The "not in ESCO" guard catches only case and spacing differences**
   (`backend/src/nessa/profile/concepts.py:55`, `catalogue/esco.py:170-172`,
   `migrations/versions/r0004_taxonomy.py:170`).
   - What: `normalise_label` folds case and whitespace only. "ICT help-desk agent", "Data
     analyst." and "data analysts" all pass the check and become provisional concepts that
     stand in for ESCO occupations. The docstring at `concepts.py:6-8` claims a provisional
     concept "never duplicates or stands in for an ESCO record". `places._key` already folds
     hyphens, so the codebase has two different normalisations. Separately, the trigger
     compares the application-supplied `normalised_title` rather than deriving it from
     `NEW.title`, so the database guard is only as strong as the caller.
   - Why it matters: the disjointness of ESCO and provisional concepts is what T6 will rely on.
     Near-duplicates undermine DIV-1 alias deduplication.
   - Fix: fold punctuation and hyphens in the comparison. Do it on the fly in SQL to avoid
     re-importing, or with a transformation bump. Return the top `match=all` full-text
     candidates with an accepted or refused registration. In the trigger, derive the
     normalised form from `NEW.title`. Soften the docstring claim and record the remaining
     near-duplicate work against DIV1-05 (T6).
2. **ESCO reuse condition 2 is applied inconsistently** (`docs/dependencies.md:167`,
   `backend/src/nessa/catalogue/esco.py:27-35`).
   - What: the product import is itself a reduced and transformed version of the release.
     It imports 6 of the 19 CSVs, leaving out the skill groups and skill hierarchy, the
     collections, the dictionary and the green share. It also de-duplicates labels and
     collapses repeated rows. Yet the manifest and attribution do not mark it as adapted.
     The sample is marked as modified for exactly the same reason ("reduced").
   - Why it matters: by the licence reading the implementer recorded, the shipped catalogue
     is unmarked.
   - Fix: add an adapted-version statement to the manifest and API, for example "Adapted:
     occupations, skills and their relations only; transformation nessa-esco-import-1". List
     the omitted files in the transformation comment. Put the ESCO-terms reading on the
     human rights-review checklist (R2) instead of recording it as settled.
3. **Re-import ignores the transformation version** (`backend/src/nessa/cli.py:186`,
   `backend/src/nessa/catalogue/taxonomy.py:33-34`).
   - What: the "already imported" check compares only `(dataset_id, sha256)`. If a later
     change alters normalisation or the vector build without changing the release, the
     import reports "already imported" and keeps the stale stored `normalised` and
     `search_vector` columns. Query-time `normalise_label` would then disagree with them, and
     alias lookups would miss silently.
   - Fix: include `transformation_version` in the comparison, and refuse on a mismatch with
     `TaxonomyMismatchError` and a pointer to the reviewed-migration step.
4. **`full_text_total: 0` when full-text search did not run**
   (`backend/src/nessa/catalogue/taxonomy.py:79-80`).
   - What: in the label-only path (no lexemes but a label matched), full-text search never
     runs, yet the response reports zero full-text matches.
   - Why it matters: it conflates "not searched" with "searched, none" (GC6 in spirit). The
     impact is low.
   - Fix: return `null` for the total or a `full_text_searched: false` flag, or at least
     state this case in the `OccupationSearchOut` description.
5. **Import atomicity and the post-lock "already imported" branch are untested**
   (`backend/tests/integration/test_taxonomy.py:182-194`).
   - What: both re-import tests go through `import_taxonomy`'s pre-check (`cli.py:186`), so
     `import_release`'s own "already imported" branch (the race path, `taxonomy.py:33-34`)
     never runs. No test shows that a failure part-way through COPY leaves no rows.
   - Fix: call `import_release` twice directly. Add a test that makes the import fail
     part-way, for example a catalogue whose relation names an absent skill, built past the
     parser, and asserts that every taxonomy table is empty afterwards.
6. **No database-level isolation test for `provisional_concepts`**
   (`backend/tests/integration/test_isolation.py:17-23`).
   - What: `WORKSPACE_TABLES` does not include `provisional_concepts`. Only the API 404 test
     exists (`test_provisional_concepts.py:66-73`). The policy matches the proven pattern, so
     this is a coverage gap, not a bug.
   - Fix: add a provisional concept to the fixture workspace, or add an `as_role("pg_api", …,
     actor=BEN)` count test.
7. **Two shape and tautology tests, plus cosmetics.**
   - `tests/domain/test_esco_release.py:39-49` restates the pin's literal values. The real
     check of the pin is the acceptance full-release test.
   - `tests/domain/test_places.py:48-58` proves BND1-04 by introspecting dataclass fields.
     GC12 asks for tests of contracts, not implementation shape. Prove it through the
     `GET /v1/places` item keys and the profile document instead.
   - Cosmetic: `test_esco_release.py:124` has a no-op `dataclasses.replace(SAMPLE_RELEASE)`,
     and `test_taxonomy.py:230` has a leftover `print`.
8. **"Byte-for-byte" overstated** (`backend/tools/esco_sample.py:7`,
   `fixtures/esco-sample/README.md:18`).
   - What: the sample's rows are re-serialised by `csv.DictWriter`, and line endings change
     from CRLF to LF (my probe). The values are identical but the bytes are not.
   - Fix: say "value-for-value".
9. **`places.place()` and `_BY_ID` are test-only code** (`backend/src/nessa/catalogue/places.py:135,143-144`).
   - What: nothing in `src` calls them, because the profile stores the label.
   - Fix: remove them, or use `place_id` where cities are stored (half B's call).
10. **The "Newcastle" alias** (`backend/src/nessa/catalogue/places.py:91`).
    - What: Newcastle-under-Lyme (Staffordshire) is also commonly called "Newcastle". The
      module promises "never guessed" (`places.py:11`).
    - Fix: no code change. Add it to the human city-review checklist with the other aliases.
11. **Provisional concepts carry no explicit marker in the output**
    (`backend/src/nessa/api/catalogue_schemas.py:238-255`).
    - What: you can only tell a provisional concept apart by the endpoint, the export array
      or the UUID version.
    - Why it matters: spec §4's `CareerSuggestion` holds "canonical concept or provisional
      concept ID". A consumer of the object alone cannot tell which it holds.
    - Fix: add `kind: "provisional"` (or `taxonomy: null`) to the output.
12. **Process (disclosed by the implementer).** A heredoc string replacement was applied to
    `tools/esco_sample.py` and `tools/datasets.py`, against the workspace rule to use the
    Edit tool only. I read both final files in full and saw no residual defect. Recorded
    only.

### Assessment
**Task quality:** Approved
**Reasoning:** The taxonomy half meets S2.1. The pin is enforced and fail-closed, the import
is transactional and idempotent, retrieval is parameterised and bounded, failure is kept
distinct from empty results, and grants follow least privilege. I verified the region
assignments and the data claims against the pinned release. What remains is Minor: a
case-and-space-only "not in ESCO" guard, uneven application of the ESCO adapted-version
condition, transformation-version drift, and some test-coverage and wording gaps.
