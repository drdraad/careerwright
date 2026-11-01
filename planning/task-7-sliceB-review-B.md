# Task 7 slice 7B: review B (AI evidence, AI Resilience records, reference store and API)

Reviewer B. Package `review-df44221..04f95cf-B-ai-evidence.diff` (18 files), read in three
passes: API and catalogue code, migration and tests, ADR 0010 and the register. I read
`exploration.py`, `discovery_schemas.py`, `routes_discovery.py`, `deps.py`, `cli.py`,
`envelope.py`, `r0004_taxonomy.py` and `test_isolation.py` in git only for named risks 3, 4
and 5. Read-only throughout. I did not read `.env` or NESSA_HOME, made no live call and
dispatched no subagent. HEAD is `04f95cf`.

One probe, run on the committed code with `uv run --locked` and no repository change:
`/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/97b1e108-19c9-45e9-9fd3-f372d0f9e9b6/scratchpad/probes/probe_air.py`.
Results:
1. A record with `origin: model_proposal` and a decision whose reviewer is "Muse Spark
   (model)" has no publication failures. Its state is `published`.
2. The fixture record with its range edited to 0-10 keeps the same decision and still
   passes every check.
3. In the fixture pack, an occupation with no record returns `unscored`, `no_record`,
   `synthetic=True` and `label=None`.
4. A seniority record listed first hides a publishable record for the same occupation,
   which then reads `unscored`.
5. The pinned ILO file scores ISCO 2519 (Gradient 3), the data quality specialist's group.
   The pinned crosswalk has no row for that occupation.

## Named risks, one focused check each

1. **AIR1-02 and AIR1-04.**
   - Checked: `ai_resilience.py` (record model, `publication_failures`, `check_record`,
     `assessment`), every use of `AssessmentOrigin` and `AssessmentRecord` under `src`
     (grep), and probe 1.
   - Holds: no code path writes a record. No route does, no run kind does, and the packs are
     committed JSON read at start. The product pack is empty, and a test fails if it is not.
   - Does not hold: `origin` is never read. A model proposal that carries a decision
     publishes (Important 2).
2. **The labelled fixture record.**
   - Checked: the pack validator (`ai_resilience.py:286`), `committed_packs` (`:471`),
     `for_workspace`, both call sites (`role_evidence.py`, `exploration.hard_filters`) and
     the integration test (`test_reference_data.py:196`).
   - Holds: synthetic and real records cannot share a pack, the product pack cannot be
     synthetic, the label must contain "synthetic", and the fixture pack applies only to
     workspaces with a `fixture_key`.
   - Labelling gaps: Minor 3 and Minor 8.
3. **The lower-bound filter and the unscored state.**
   - Checked: `filter_outcome` (`ai_resilience.py:443`), `_hard_filters`
     (`exploration.py:246`), `AiResilienceFilterOut` and `OccupationEvidenceOut.of`.
   - Holds: unscored roles are kept by default and never read as 0 or 10, only a published
     range's lower end is compared, and the counts are reported.
   - Does not hold: the publication checks let exposure-type evidence alone publish a range,
     and the fixture record does exactly that (Important 1).
4. **Migration r0027.**
   - Checked: the migration file, the revision chain (only `r0027` added,
     `down_revision = "0026"`), the ESCO pattern in `r0004`, and the all-tables RLS
     assertion (`test_isolation.py:190`).
   - All hold:
     - forward-only (`downgrade` raises);
     - CHECKs on `dataset`, `period`, `population`, `gradient` and `match_type`, plus the
       two crosswalk target constraints;
     - RLS enabled on all 8 tables;
     - `GRANT SELECT` to `nessa_api` only, with nothing for `nessa_worker`, which computes
       no slate (grep: `compute_slate` runs only in the API and `tools/evaluation.py`);
     - no write grant on any table. AI records are not in the database at all, so the API
       cannot write a published record.
5. **The reference API.**
   - Checked: `routes_reference.py`, the error messages in `reference.py`, the validation
     handler (`envelope.py:103`, location and type only) and the generated client.
   - Error messages are static and never echo input. A cross-person read returns 404
     (tested).
   - I did not re-run the client drift check. `make check` on `04f95cf`, which the
     implementer reports, includes it. Spot check: `types.gen.ts` has
     `OccupationEvidenceOut`, `AiResilienceOut` (state, `unscored_reason`, `synthetic`,
     `synthetic_label`, pack fields), the operation's URL and `REFERENCE_DATA_UNAVAILABLE`.
6. **ADR 0010 and the register.**
   - Checked: the rows the slice changed (TAX1-02..07, AIR1-02/03/04/05/07/10/11/12, JOB-05,
     DIV1-07, H-10) against the code.
   - H-10 is "not run — requires human". No human gate is claimed as passed.
   - AIR1-04 and ADR 0010 decision 7 overstate the code (Important 2). AIR1-02 and AIR1-03
     rest on checks that miss exposure-only evidence (Important 1). The ADR status line
     numbers the provisional decisions wrongly (Minor 10).

### Spec Compliance
- ❌ Issues found:
  - The publication checks accept a range supported only by exposure-type evidence, so
    "Where the evidence supports exposure only, show that fact and keep resilience unscored"
    (spec AIR-1 step 4; register AIR1-03) is not enforced. The one published record (the
    fixture) is such a range. `ai_resilience.py:200`, `:226`;
    `packs/ai_resilience_fixture.json:16-31`.
  - AIR1-04 ("a model proposal can only be a proposed record") is claimed in ADR 0010
    decision 7 and in the register, but the record model does not enforce it.
    `ai_resilience.py:145`, `:226`; `docs/adr/0010-reference-data-and-ai-evidence.md:99`;
    `docs/requirements-register.md:157`.
- ⚠️ Cannot verify from diff:
  - **UI labelling.** Whether the fixture record and the unscored state are conspicuous in
    the UI. No UI shows an assessment yet; that is Task 8.
  - **Client drift and acceptance.** The drift check and `make acceptance` (including
    `test_isolation`'s RLS assertion over the 8 new tables) were not re-run here.
  - **Demo-stack response.** In the demo stack, the data quality specialist's evidence
    answer would show `ai_evidence.state: exposure_only` beside a published range. I
    derived this from the code plus probe 5. I did not start the stack.
  - **Human gates.** The licence readings (R6) and H-10 are human gates.

### Strengths
- **Synthetic data cannot reach a real workspace.** It is enforced in three places: the
  pack validator (one synthetic flag per pack), `committed_packs` (the product pack is never
  synthetic, the fixture pack always is) and pack selection by `fixture_key`. A test fails if
  the product pack gains a record.
- **Clear state precedence.** Withdrawn, then invalidated, then proposed, then published.
  Corrections apply by source or record ID when the API starts, and a bad pack stops the API
  from starting. Nothing is silently skipped.
- **The filter never turns unknown into a score.** `filter_outcome` is small and
  deterministic: unscored is never 0 or 10, unscored roles are kept by default, and switching
  them off is counted. The slate's counts and pack version are on every answer.
- **Missing is never zero.** For observed use, a code the release lacks shows
  `in_release: false` with null counts. The ILO and observed-use measure texts are accurate.
- **The migration matches the reviewed ESCO pattern exactly:** read-only public data, no
  grant to the worker.
- **The evidence endpoint is properly scoped.** It reads inside `actor_transaction` with
  `visible_workspace`, uses static errors, returns 503 when reference data is not imported
  rather than an empty answer, and has a 404 cross-person test.

### Issues

#### Critical
None.

#### Important

1. **Exposure-only evidence can publish a resilience range, and the fixture does.**
   - **Where:** `backend/src/nessa/catalogue/ai_resilience.py:200` (`_independent_families`),
     `:226` (`publication_failures`), `packs/ai_resilience_fixture.json:16-31`,
     `backend/src/nessa/api/reference_schemas.py:314`.
   - **What:**
     - The only evidence checks are "any observed item" (`NO_SUPPORTING_EVIDENCE`) and "two
       families from two independence groups". The fixture's two families are
       `task_exposure` (ILO, `mixed`) and `observed_use` (Anthropic, `pressure`): exactly
       the two imported indices. Nothing bears protection, yet it publishes 5-8, which
       reaches "comparatively resilient".
     - With the pinned files imported (`setup-database` imports them in `make demo` too),
       ISCO 2519 has ILO exposure (probe 5). So the fixture workspace's evidence answer for
       the data quality specialist says `ai_evidence.state: "exposure_only"` and
       `ai_resilience.state: "published_range"` together.
     - The record also cites "observed use of matched O*NET tasks", but the crosswalk has
       no match for that occupation.
   - **Why it matters:**
     - Spec AIR-1 step 4 says that where the evidence supports exposure only, resilience
       stays unscored, and that publication needs "supporting evidence for the assigned
       band".
     - Register AIR1-03 is marked verified because no real record exists, not because the
       checks enforce the rule. The machinery would publish a real record built from the two
       pinned indices alone.
     - This is the named risk ("exposure-only evidence shows with resilience unscored"),
       reproduced in the fixture workspace.
   - **Fix:**
     - Add a deterministic publication failure, for example `exposure_only_evidence`, when
       every observed item's family is `task_exposure` or `observed_use`. Add its
       parametrised case to `test_a_record_missing_any_publication_condition_never_publishes`.
     - Give the fixture a third synthetic, labelled family (for example
       `human_accountability`, bearing `protection`) so it still qualifies the machinery
       under the rule.
     - Stop emitting `exposure_only` beside a published range. Either derive `ai_evidence.state`
       from the assessment, or rename it to describe the imported evidence.
     - Correct the AIR1-02 and AIR1-03 evidence text.

2. **AIR1-04's guard is stated in ADR 0010 and the register but is not in the code.**
   - **Where:** `backend/src/nessa/catalogue/ai_resilience.py:145` (`AssessmentOrigin`, never
     read), `:226`; `backend/tests/domain/test_ai_resilience.py:158-166`;
     `docs/adr/0010-reference-data-and-ai-evidence.md:99`;
     `docs/requirements-register.md:157`.
   - **What:**
     - ADR 0010 decision 7 says "a model's proposal can only be `model_proposal` with no
       decision". The register says "no field lets a record mark itself published".
     - `publication_failures` ignores `origin`. `decision` is exactly the field that makes a
       record publishable, and anyone can fill it: `role` is a literal any author can type.
       Probe 1 shows a `model_proposal` with a decision by "Muse Spark (model)" publishing.
     - The covering test builds its proposal with `decision=None`, so it repeats the
       `NO_REVIEWER_DECISION` case and cannot fail for AIR1-04. Its other assertions
       (`"published"`, `"state"` not in `model_fields`) test implementation shape (GC12).
   - **Why it matters:**
     - L0 is safe today: no code path creates records, and the product pack is tripwired
       empty.
     - But the deliverable is the record model that a later model-backed proposal path will
       rely on, and the register marks AIR1-04 verified on a guarantee the model does not
       give.
   - **Fix (either):**
     - Make `origin` load-bearing: a `model_proposal` never publishes, and a reviewer who
       accepts one enters a `reviewer_entry` record. Add a test that a `model_proposal`
       carrying a full decision stays `proposed`.
     - Or reword decision 7 and AIR1-04 to state the real L0 guard (no code path writes a
       record, packs change only by reviewed commit, the product pack is tripwired empty),
       and drop the shape assertions.

#### Minor

1. **The reviewer's decision does not bind the range it approved.**
   `ai_resilience.py:128-137` (`ReviewerDecision` has `outcome` but no bounds). Editing
   `lower`/`upper` after the decision (0-10 in probe 2) keeps the record published. The spec
   has the reviewer "record an allowed range". Fix: put the decided bounds in the decision
   and fail publication when they differ from the record's. R12: hardening.
2. **A reviewed null with thin evidence reports the wrong reason.** `ai_resilience.py:406-408`.
   A null decision still runs every evidence check. A reviewer's null for insufficient
   evidence, the usual case, therefore shows `unscored_reason: not_publishable`, not
   `reviewed_null`, and the reviewer's decision disappears from the answer. Fix: skip the
   evidence-sufficiency checks for `outcome == "null"`, and test a null decision with one
   family.
3. **In the fixture workspace, an occupation with no record says `synthetic: true` with no
   label.** `ai_resilience.py:400`, `reference_schemas.py:235`/`:251` (probe 3). The field
   describes the pack, not an assessment, so a UI badge keyed on `synthetic` would mark every
   unscored role, with no text. Fix: set `synthetic` from the record (False when there is
   none), or document that the field describes the pack.
4. **`for_occupation` takes the first record for an occupation.** `ai_resilience.py:337`.
   A seniority record (always proposed in M0) listed first hides a publishable one (probe 4).
   The pack's key allows both. Fix: reject a second record per `esco_uri` in M0, or select
   the seniority-`None` record. Hypothetical in L0.
5. **`mapping_reviewed` and the evidence items are self-declared.**
   `ai_resilience.py:164`, fixture `:15`. Nothing ties them to a mapping version (crosswalk
   release, ISCO group or UK SOC review) or to held data. The fixture declares its mapping
   reviewed while the same answer shows `uk_soc.review_state: unreviewed` and no O*NET match.
   Fix: record which mapping (dataset IDs and codes) was reviewed, so a crosswalk correction
   can invalidate the record through `affects_sources`. R12.
6. **The record model lacks fields the spec lists.** Spec section 18 lists "evidence quality"
   for `AIResilienceAssessment`; there is no such field. AIR-1 asks to preserve scenarios and
   "the reason for widening the range"; `widening_reason` is optional and never required, and
   the two-band fixture (5-8) has none. Fix: add evidence quality, and require a widening
   reason when a range spans more than one band, or record why not. R12.
7. **No test runs a scored record through the slate.** `exploration.py:290`. The integration
   test covers only unscored roles. `test_slate.py` injects `left_out` directly. So deleting
   the `BELOW_MINIMUM` → `below_ai_resilience_minimum` branch, or miscounting `scored`, passes
   every test. Fix: one integration case with an injected pack holding a published synthetic
   range, for example `dataclasses.replace(api_deps, assessment_packs=...)`, at a minimum
   below and above its lower end.
8. **The slate's AI filter output carries no synthetic marker.** `discovery_schemas.py:394-396`.
   In the fixture workspace, its summary calls the synthetic record a "reviewed range", and a
   `below_ai_resilience_minimum` reason driven by it is unlabelled. Only the `fixture-` prefix
   of `pack_version` shows the pack is synthetic. Fix: add `synthetic` to
   `AiResilienceFilterOut`, and say "synthetic fixture range" in the summary when it applies.
9. **The evidence endpoint's failure paths are untested.** `reference.py:172`, `:264`.
   `REFERENCE_DATA_UNAVAILABLE` (503) and an unknown concept (`NOT_FOUND`) are never
   exercised. Fix: two integration cases (GC6).
10. **ADR 0010 misnumbers its provisional decisions.**
    `docs/adr/0010-reference-data-and-ai-evidence.md:4` and `:161` say "Decisions 4
    (full-time tables), 7 (the 90th percentile) and 8 (advertised pay read as gross)". But
    decision 7 is the AI Resilience record model; the 90th percentile and the gross reading
    are both in decision 8. As written, the product owner is asked to confirm the record
    model as provisional. Fix: "decisions 4 and 8 (the 90th percentile; advertised pay read
    as gross)" in both places.

### Assessment
**Task quality:** Needs fixes

**Reasoning:** The record model, the filter, the store, the migration and the endpoint are
sound, and no real record or human gate is claimed. But the publication checks let
exposure-only evidence publish a range, which the one fixture record demonstrates. And the
AIR1-04 guarantee claimed in ADR 0010 and the register is not enforced or tested by the code.

Counts: Critical 0, Important 2, Minor 10.
