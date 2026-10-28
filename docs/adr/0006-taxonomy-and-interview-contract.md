# ADR 0006: The ESCO taxonomy, English cities and the InterviewTurn contract

- Status: Accepted (Task 5, Sprint 2: S2.1-S2.2). Decision 4's region assignment,
  decision 6's hard-constraint set and decision 8's basis for an answer with no value are
  **provisional, need product owner confirmation** (ruling R6).
- Date: 2026-10-28
- Requirements: TAX1-01, TAX1-04, DIV1-01, DIV1-03, REC1-04, BND1-04, PROF-01..07,
  MODEL-01..04, STATE-08, TEST1-10; spec sections 3-5, 16 and 18; ADR 0002, ADR 0004
  decisions 5, 7 and 9

## Context

Sprint 2 turns the You chapter into a conversation. Two backend foundations come first:
an occupation taxonomy to ground titles in (spec section 5, TAX-1: the full pinned ESCO
release with PostgreSQL full-text search and alias lookup; no embeddings, Career Causeways
or taxonomy API), and a structured interview turn whose output the model proposes and the
person confirms (spec section 4, "Schema governance and conversational integrity"). ADR 0004
decision 7 requires the first run kind that reads the profile to pin the version it read.

## Decisions

1. **One pinned ESCO release, fetched and verified, never committed.** ESCO v1.2.1,
   classification, English, CSV (10,045,670 bytes, SHA-256 `f9761b0b…deb3e`;
   `nessa.catalogue.esco.ESCO_RELEASE`). `make setup` downloads it from the URL the ESCO
   download page links into the gitignored `var/datasets/` and keeps it only if size and
   hash match; the setup container mounts that directory read-only and `setup-database`
   imports the file after checking it again, once (later starts find it imported). The
   database holds one release; importing a different one is refused, so a version bump is
   a reviewed change. The import manifest records dataset, version, URL, hash, size, licence,
   attribution, native code version, transformation version (`nessa-esco-import-1`), counts
   and the repeated rows collapsed (TAX1-04).
   - The release lists 4 occupations and 21 skills twice, identical except `modifiedDate`.
     Such a repeat is imported once (the later date kept) and counted; a repeat that differs
     in anything else is refused as conflicting data.
   - Tests import a committed, labelled, hash-pinned subset (`fixtures/esco-sample/`, 30
     occupations), marked `sample` in the database and the API. The full release is imported
     in `make acceptance` (`test_the_full_pinned_release_imports_and_is_searchable`, and the
     stack's own setup container) and by `make dev`/`make demo`.

2. **Identity: internal concept IDs, ISCO-08 as the pivot.** Each ESCO occupation gets an
   internal concept ID, UUIDv5 of its ESCO URI (stable across re-imports, never confused with
   a random provisional ID), and keeps its URI, ESCO code and ISCO-08 unit group. Specialists
   in one ISCO group stay distinct concepts (TAX1-01). Skills, essential/optional
   occupation-skill links, skill-skill links and the occupation hierarchy are imported in
   full. ESCO is public reference data: row-level security with a policy that every row is
   readable, read-only grants for the API role, written only by setup.

3. **Retrieval: English full-text search plus alias lookup.** One `tsvector` per occupation:
   preferred label (A), alternative labels (B), hidden labels and essential skills (C),
   description and ISCO group (D), with a GIN index.
   - A search returns exact label matches first (normalised: case-folded, single-spaced),
     all of them when several occupations share the label (999 normalised labels in v1.2.1
     belong to more than one occupation; the caller resolves the ambiguity), then ranked
     full-text matches, excluding the label
     matches, with the total, so a page is never mistaken for the whole.
   - `match=all` needs every word (web-search syntax); `match=any` ranks by how many words
     match, for broad task and interest queries (DIV-1: several queries, reranked later).
   - A query with no searchable words is refused (`VALIDATION_FAILED`, `no_search_terms`),
     and a database without the taxonomy refuses searches (`TAXONOMY_UNAVAILABLE`): neither
     is an empty result. Hidden labels match but are never displayed.
   - Endpoints: `GET /v1/taxonomy` (manifest), `GET /v1/taxonomy/occupations?q=&match=&limit=`,
     `GET /v1/taxonomy/occupations/{concept_id}` (ISCO chain, alternative labels, skills,
     attribution).

4. **A finite English city list.** The 55 English cities of GOV.UK's "List of cities"
   (retrieved 2026-10-28, page SHA-256 recorded; Open Government Licence v3.0), each with a
   stable ID (`gb-eng-<name>`), country and subdivision (GB, GB-ENG), ONS region and
   timezone; served by `GET /v1/places`. A profile's cities must resolve to the list and are
   stored by the list's own name; unknown names are refused (`unknown_city`), never guessed.
   A few unambiguous aliases are recorded (Hull, Newcastle, Brighton, Stoke-on-Trent,
   Southend, St. Albans, City of London, City of Westminster); no alias names two cities.
   London and Westminster stay separate, as on the official list. A city is geography only:
   it implies no residence or right to work (BND1-04). **Provisional:** the ONS region of
   each city was assigned by the implementing agent; a reviewer should confirm it.

5. **Provisional concepts for verified titles outside ESCO** (DIV1-03).
   `POST /v1/workspaces/{id}/occupations/provisional` records a title the person confirmed as
   an internal concept private to the workspace, citing a direct-entry source. It has no ESCO
   URI or ISCO group by construction; a title that is any ESCO label is refused with the
   occupations that hold it, and a database trigger refuses one too. Titles a model suggests
   are not accepted here: they stay search hypotheses until corroborated (DIV1-04, the
   discovery task).

6. **Profile schema version 2.** Three separate fields: `enjoyed_tasks` (interest),
   `confident_tasks` (what the person believes they can do) and `evidenced_tasks` (what they
   can show they have done), at most 8 each (REC1-04). Version 1 documents read as version 2
   with those fields not asked. Each answer's provenance is its source reference: kind
   (direct entry, fixture, or **conversation**), observation time, who recorded or
   confirmed it, and for a conversation source the turn that proposed it, the person's
   messages it cites and its basis, `stated` or `inferred` (PROF-01). The **hard
   constraints** are cities, target titles, weekly study hours and both spending limits:
   search and planning treat them as limits, so only the person's explicit confirmation
   establishes them (PROF-04). **Provisional:** which fields are hard constraints.

7. **One write path.** `commit_profile_version` is the only way a profile changes: a direct
   edit (`PUT /profile`) and a confirmed chat proposal both go through it, with an expected
   version, under the workspace lock, as a new immutable version (PROF-07).

8. **The InterviewTurn contract** (`nessa.profile.interview`). The model receives the
   minimum profile subset (every field's state and value, the preferred name's value
   withheld, no IDs or sources), up to the last six messages and its earlier replies, within
   a prompt budget, and must answer a strict JSON schema: reply, proposed updates (field,
   state, text or items, basis, cited message refs, reason), next question, missing critical
   fields, readiness for review. `check_turn` validates the output deterministically: only
   profile fields can be named (keys, secrets and commitments are not profile fields;
   PROF-06), each update cites one to five of the given message refs, values parse by field
   kind (money as pounds into integer pence, hours, list bounds, cities on the list), one
   update per field. A valid output is stored, sealed, as an `InterviewProposal` with
   server-assigned change IDs, message IDs in place of refs and the hard-constraint mark.
   Structural bounds are checked in code, not schema keywords, so the schema stays within
   strict mode. A list proposal is the complete list after the change (the instructions and
   the API say so); accepting it replaces the field's list.

   **Basis is verified, not taken on trust** (fix round 1). The server keeps the model's
   `stated` only when every new value the update proposes appears in the messages it cites
   (case, spacing and digit grouping aside, whole words; list items the profile already
   holds need no quote); otherwise the change is `inferred`. The correction is not a
   validation problem, so it never costs a repair request. **Provisional, needs product
   owner confirmation (R6):** an answer with no value to quote (`unknown`, `skipped`,
   `prefer_not_to_say`) is shown as `inferred`, so the person checks it, even when they said
   it in so many words.

9. **Bounded validation repair, and who retries what.** An invalid output gets one repair
   request listing the problems; a second failure ends the run `invalid_model_output`
   (PROF-05). The repair is the agent's output-retry budget (`retries={'output': 1}`,
   `request_limit=2`), the only retry owner for invalid output; the DBOS step still retries
   only transient provider failures and the activity's store budget only store failures. An
   attempt can therefore send two requests: its spend reservation covers both at their
   bounds (input 14,500 tokens, output 1,500), $0.049 on the Standard model and $0.0035 on
   the test model, and the attempt records the requests it sent (`requests_sent`). An
   attempt that sent more requests than it got responses (a repair that failed without
   usage) is `unknown` and keeps its whole reservation, never part-reconciled (MODEL-08).
   The default run limit is $0.15 so that all three of the DBOS step's attempts fit on the
   Standard model: a Meta outage ends `provider_unavailable`, never `budget_exceeded` (fix
   round 1). An attempt that makes no provider call records a known cost of 0.
   A response cut off at its token limit is `output_truncated` from its typed finish reason
   the moment it arrives (`TruncationGuard`, on every task's agent): never parsed, repaired
   or stored, so it costs one request, and its reported usage is still booked. A
   content-filter refusal is `model_refused` and is not retried.

10. **A new run kind on the same activity.** `interview_turn` runs through the one bounded
    activity and workflow (ADR 0002): no second model-call path. The activity takes a
    `RunTask` per kind (its call, worst case and whether it has an input), composed with the
    model builder in the new worker entry point `nessa.worker` (`python -m nessa.worker`),
    because the identity module must not import the profile module. Submission seals the
    turn's context into `run_inputs` (associated data: kind, workspace, run); the worker opens
    it inside the activity, still never reading profile or conversation tables (ADR 0004
    decision 5), and only while the requester may act. The run pins `profile_version`
    (ADR 0004 decision 7; a CHECK requires it for this kind). The step sequence is
    unchanged, so the DBOS `application_version` stays `nessa-l0-1`. Reseal covers the new
    sealed table.

11. **Deciding on a turn.** `POST .../interview/turns/{turn_id}/decision` with an expected
    version, the change IDs accepted and each hard-constraint field confirmed by name.
    - It applies only a complete, validated proposal (else `PROPOSAL_NOT_AVAILABLE`), only
      when the profile is still the version the message was sent with (else
      `STALE_INPUT_VERSION`, naming both versions), and only if every accepted hard
      constraint is confirmed (else `CONFIRMATION_REQUIRED`, naming the fields). Every
      refusal leaves the profile exactly as it was.
    - Accepted changes become one new version, each citing its own conversation source;
      the rest are recorded as rejected; a turn is decided at most once (`ALREADY_DECIDED`).
    - The decision's response, which is stored as the command's receipt, carries the decision
      and the profile but not the model's reply: model output stays sealed.
    - Edits and undo are direct edits (decision 7). Submitting a turn also names the version
      the person saw; a stale one is refused before any run exists.

12. **The deterministic fixture interviewer** (plan sections 2-3). Demo workspaces' turns use
    `nessa-fixture-interviewer-1`, registered with mode `fixture` and zero price: a
    deterministic answer to the same prompt and schema, from fixed patterns (listed cities,
    hours, pound amounts, "I am a ...", "I enjoy ...", "rather not say"), checked by the same
    `check_turn`, stored with origin `fixture` and a reply that says it is the demo
    interviewer. It needs no key, makes no network call and its attempt records no spend. A
    CHECK makes it the only model a demo workspace's run can name and confines it to
    interview turns, which amends ADR 0004 decision 9: demo workspaces never call a
    *provider* model. A connection check in a demo workspace is still refused.

13. **No token streaming in this slice.** The activity's requests are not streamed: nothing
    could show a partial reply anyway, because the event stream carries identifiers only and
    a partial reply is private content. A run output exists only after complete validation,
    and the profile changes only through a decision on it, so partial or streamed JSON can
    never commit (PROF-03). Responsiveness during a turn (stages, a progress state) is the
    You chapter's work (T6); streaming the reply would need a sealed partial store and its
    own ADR.

14. **Live qualification through the existing command.** `make live-smoke INTERVIEW=1` runs
    one interview turn on the test model with a fixed synthetic message and confirms its
    proposals, in the isolated smoke stack, within the `live-smoke` scope's cumulative cap,
    which now counts provider requests. The workspace's run limit allows one attempt (two
    requests at most). Evidence (ledger row 13, 2026-10-28, `muse-spark-1.3-contributor`):
    one request, no repair needed, 1,128 input and 693 output tokens (323 reasoning),
    $0.000251 against a $0.0035 reservation; five proposals (current role, two cities,
    6 hours, a £1,200 total limit, one enjoyed task), each stated and citing the message,
    confirmed and saved as profile version 1; the leak scan of both databases, every
    container log and every API response found no part of the key. The production model
    was not called for this schema: Spark 1.3's strict schema output on the Standard ID was
    qualified in Sprint 0 (ADR 0003, ledger calls 6-7), and the same release accepted this
    schema; one `PRODUCTION=1 INTERVIEW=1` run (worst case $0.049) would close that gap.

15. **Export format 2.** The workspace export adds the interview turns (messages,
    proposals, decisions) and provisional concepts.

## Consequences

- New error codes: `TAXONOMY_UNAVAILABLE`, `CONFIRMATION_REQUIRED`, `PROPOSAL_NOT_AVAILABLE`,
  `ALREADY_DECIDED`; new failure classes: `model_refused`, `output_truncated`.
- A city outside the list, which Sprint 1 accepted as free text, is now refused on save.
  Stored version 1 documents still read; a person re-saving one with an unlisted city must
  pick a listed city.
- The You chapter (T6) builds the conversation, review tray and city picker on these
  endpoints; discovery (T6) uses the taxonomy search for its multi-query pool.
- Not done here: residence and work-rights fields (BND1-04 stays open for them), streaming,
  an ESCO version-bump procedure beyond "new pin, reviewed migration".
