# ADR 0006: The ESCO taxonomy, English cities and the InterviewTurn contract

- Status: Accepted (Task 5, Sprint 2: S2.1-S2.2). Decision 4's region assignment and its
  refusal of plain "Newcastle", decision 5's concept-key folding, decision 6's
  hard-constraint set and decision 8's basis for an answer with no value were provisional
  and were confirmed by the product owner on 2026-10-28 (H-11 below), the hard-constraint
  set with a salary floor added (implemented in Task 6, ADR 0007).
- Date: 2026-10-28
- Amended: 2026-10-31, the product owner's approval of the audit: decision 5's provisional
  concepts for the role space (ADR 0015); 2026-11-01, Task 6f; 2026-11-02, Task W2F (the
  last section): the tasks the person doesn't enjoy and `interview-turn-6`.
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
   `careerwright.catalogue.esco.ESCO_RELEASE`). `make setup` downloads it from the URL the ESCO
   download page links into the gitignored `var/datasets/` and keeps it only if size and
   hash match; the setup container mounts that directory read-only and `setup-database`
   imports the file after checking it again, once (later starts find it imported). The
   database holds one release; importing a different one is refused, so a version bump is
   a reviewed change. The import manifest records dataset, version, URL, hash, size, licence,
   attribution, native code version, transformation version (`careerwright-esco-import-1`), counts
   and the repeated rows collapsed (TAX1-04). "Already imported" means the same dataset, the
   same hash **and** the same transformation version; the same release built by another
   transformation is refused like a different release (its stored labels and search vectors
   would be stale), pointing at the reviewed-migration step (fix round 1).
   - The import is itself an adapted version of ESCO: 6 of the release's 19 CSV files
     (no skill groups, skill hierarchy, collections, dictionary, concept schemes or green
     share), labels trimmed and de-duplicated, repeated rows merged. The manifest, every
     release in the API and every occupation detail carry an `adaptation` statement that
     says so (ESCO's second reuse condition), beside the attribution.
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
     is an empty result. If such a query matches a label, the label matches are returned
     with `full_text_total: null`: full-text search did not run, which is not zero. Hidden
     labels match but are never displayed. Every occupation in a result carries
     `concept_kind: "esco"`; a provisional concept carries `"provisional"`, so an ID's kind
     is clear from the object alone (spec section 4).
   - Endpoints: `GET /v1/taxonomy` (manifest), `GET /v1/taxonomy/occupations?q=&match=&limit=`,
     `GET /v1/taxonomy/occupations/{concept_id}` (ISCO chain, alternative labels, skills,
     attribution).

4. **A finite English city list.** The 55 English cities of GOV.UK's "List of cities"
   (retrieved 2026-10-28, page SHA-256 recorded; Open Government Licence v3.0), each with a
   stable ID (`gb-eng-<name>`), country and subdivision (GB, GB-ENG), ONS region and
   timezone; served by `GET /v1/places`. A profile's cities must resolve to the list and are
   stored by the list's own name; unknown names are refused (`unknown_city`), never guessed.
   A few unambiguous aliases are recorded (Hull, Newcastle upon Tyne, Brighton,
   Stoke-on-Trent, Southend, St. Albans, City of London, City of Westminster); no alias names
   two cities. Plain "Newcastle" is not an alias: it also names Newcastle-under-Lyme, which
   is not on the list, so it is refused rather than guessed (fix round 1). **Provisional,
   needs product owner confirmation (R6):** this refusal, like the alias list itself.
   London and Westminster stay separate, as on the official list. A city is geography only:
   it implies no residence or right to work (BND1-04). **Provisional:** the ONS region of
   each city was assigned by the implementing agent; a reviewer should confirm it.

5. **Provisional concepts for verified titles outside ESCO** (DIV1-03).
   `POST /v1/workspaces/{id}/occupations/provisional` records a title the person confirmed as
   an internal concept private to the workspace, citing a direct-entry source. It has no ESCO
   URI or ISCO group by construction; a title that is any ESCO label as a concept is refused
   with the occupations that hold it. "As a concept" is `careerwright.concept_key`, one SQL
   function used by the API and by the database trigger, which derives it from the title
   itself: case, punctuation and hyphens folded, and a simple English plural folded per word
   ("ICT help-desk agent", "Data analyst." and "data analysts" are refused; fix round 1).
   **Provisional, needs product owner confirmation (R6):** the folding heuristic, which
   could refuse a title a person expects to be accepted. A title that only resembles a
   label ("senior data analyst") is accepted: offering the full-text matches first is
   discovery's work (DIV1-05, T6). Titles a model suggests are not accepted here: they stay
   search hypotheses until corroborated (DIV1-04, the discovery task).

6. **Profile schema version 2.** Three separate fields: `enjoyed_tasks` (interest),
   `confident_tasks` (what the person believes they can do) and `evidenced_tasks` (what they
   can show they have done), at most 8 each (REC1-04). Version 1 documents read as version 2
   with those fields not asked. Each answer's provenance is its source reference: kind
   (direct entry, fixture, or **conversation**), observation time, who recorded or
   confirmed it, and for a conversation source the turn that proposed it, the person's
   messages it cites and its basis, `stated` or `inferred` (PROF-01). The **hard
   constraints** are cities, target titles, weekly study hours, both spending limits and
   the salary floor: search and planning treat them as limits, so only the person's
   explicit confirmation establishes them (PROF-04). The product owner confirmed the set on
   2026-10-28 (H-11) and added the salary floor (`minimum_salary`: the lowest gross pay the
   person will accept, with its period), which Task 6 implemented in profile schema 3 (ADR
   0007 decision 2), with the optional work style.

7. **One write path.** `commit_profile_version` is the only way a profile changes: a direct
   edit (`PUT /profile`) and a confirmed chat proposal both go through it, with an expected
   version, under the workspace lock, as a new immutable version (PROF-07).

8. **The InterviewTurn contract** (`careerwright.profile.interview`). The model receives the
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
   round 1). Migration 0009 moves every workspace still on the old built-in $0.10 default,
   never changed by the person (`version` 1), to $0.15; a limit the person set is kept
   (fix round 2). Two cases can still report an outage as over budget, because the limit
   is the person's to set and the reservation must hold: a run limit the person set below
   $0.147, and a crash during a call followed by an outage (the interrupted attempt keeps
   its reservation, so three more do not fit). An attempt that makes no provider call
   records a known cost of 0.
   A response cut off at its token limit is `output_truncated` from its typed finish reason
   the moment it arrives (`TruncationGuard`, on every task's agent): never parsed, repaired
   or stored, so it costs one request, and its reported usage is still booked. A
   content-filter refusal is `model_refused` and is not retried.

10. **A new run kind on the same activity.** `interview_turn` runs through the one bounded
    activity and workflow (ADR 0002): no second model-call path. The activity takes a
    `RunTask` per kind (its call, worst case and whether it has an input), composed with the
    model builder in the new worker entry point `careerwright.worker` (`python -m careerwright.worker`),
    because the identity module must not import the profile module. Submission seals the
    turn's context into `run_inputs` (associated data: kind, workspace, run); the worker opens
    it inside the activity, still never reading profile or conversation tables (ADR 0004
    decision 5), and only while the requester may act. The run pins `profile_version`
    (ADR 0004 decision 7; a CHECK requires it for this kind). The step sequence is
    unchanged, so the DBOS `application_version` stays `careerwright-l0-1`. Reseal covers the new
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
    `careerwright-fixture-interviewer-1`, registered with mode `fixture` and zero price: a
    deterministic answer to the same prompt and schema, from fixed patterns (listed cities,
    hours, pound amounts, "I am a ...", "I enjoy ...", "rather not say"), checked by the same
    `check_turn`, stored with origin `fixture` and a reply that says it is the demo
    interviewer. It needs no key, makes no network call and its attempt records no spend. A
    CHECK makes it the only model a demo workspace's run can name and confines it to
    interview turns, which amends ADR 0004 decision 9: demo workspaces never call a
    *provider* model. A connection check in a demo workspace is still refused.

13. **The reply streams; nothing streamed commits** (amended in fix round 1; the first
    version deferred streaming). Spec section 4: stream natural conversation for
    responsiveness, commit only after complete validation.
    - *What streams.* Only the natural-language `reply`, never the proposals. The agent
      streams its request (`ReplyStream`, an event capability), reads `reply` out of the
      partial JSON on every text event (`pydantic_core.from_json`, trailing strings
      allowed) and hands it to the activity, saying when the reply's string has closed. A
      repair request streams a new reply. The fixture interviewer streams too, in fixed
      pieces, so demo turns and contract tests exercise the same path.
    - *Where it goes.* The activity seals the reply so far into `run_partials` (one row per
      run, the run as associated data) through `PartialWriter`: the first piece at once,
      then the newest text at most once per 0.25 s on any later stream event (so the end
      of a burst is not dropped), and the whole reply the moment it closes, whatever the
      interval: the store holds the complete reply while the proposals are still being
      generated (fix round 2). Each write is announced by a `run.partial_updated` event
      that carries the run ID and the write's sequence only: the event stream stays
      identifiers-only. The worker may write only its own run's row, and only while the
      requester may act; the API may only read it, for the workspace's owner, through
      `GET .../interview/turns/{id}/reply`. `make reseal` covers it.
    - *Superseded, never mistaken for the result.* The row is deleted in the transaction
      that stores the validated output. From then on the read path answers `superseded`
      with no text, also in the moment before the run is published complete (a missing
      partial is checked against the stored output last, so a poll never answers `none`
      for a run that has its output). On a failed attempt the row is marked `stopped` with
      the latest text received (a crash is marked when the run is published), in a
      savepoint that can never abort the attempt's settlement (for example when access is
      revoked mid-call and the worker may no longer write the row). The read path reports
      completeness and `updated_at` (spec section 18: partial results carry completeness
      and freshness): `none`, `streaming`, `stopped` (this attempt's reply stopped, but the
      run goes on and may stream again or still be superseded: not final), `incomplete`
      (final: the run ended without a validated output) and `superseded`. Partial text is
      never validated, never enters a later turn's context, and never reaches the profile,
      which changes only through a decision on a validated proposal (PROF-03). Leak scans
      cover it: the test fake's reply starts with the output sentinel, the scan finds it
      nowhere while it is sealed, and finds it in `run_partials` when stored unsealed.
    - *Best effort.* Streaming is for responsiveness only: a partial write that fails stops
      that attempt's streaming and is logged by error class; it never fails or retries the
      paid call.
    - *Cost.* A streamed request that fails leaves a response in the history: with no
      usage if it failed at once, or `interrupted` with the usage counted so far if the
      stream broke part-way. Neither counts, so such an attempt stays `unknown` with its
      whole reservation (decision 9; MODEL-08), never reconciled at a partial sum.
    - *Clients* (T6): a `run.partial_updated` event refreshes only that turn's reply query,
      never the workspace's other data.
    - Rendering the stream (the You chapter's conversation) is Task 6's part of MODEL-03.

14. **Live qualification through the existing command.** `make live-smoke INTERVIEW=1` runs
    one interview turn on the test model with a fixed synthetic message and confirms its
    proposals, in the isolated smoke stack, within the `live-smoke` scope's cumulative cap,
    which now counts provider requests. The workspace's run limit allows one attempt (two
    requests at most). Evidence (ledger row 13, 2026-10-28, `muse-spark-1.3-contributor`):
    one request, no repair needed, 1,128 input and 693 output tokens (323 reasoning),
    $0.000251 against a $0.0035 reservation; five proposals (current role, two cities,
    6 hours, a £1,200 total limit, one enjoyed task), each stated and citing the message,
    confirmed and saved as profile version 1; the leak scan of both databases, every
    container log and every API response found no part of the key.
    Streaming confirmation (ledger row 14, 2026-10-28, fix round 1, same model and message):
    the turn streamed its reply into the partial store (one write, announced by one
    `run.partial_updated` event), the validated output superseded it, usage arrived on the
    streamed response (1 request, 1,147 input and 632 output tokens, 255 reasoning;
    $0.000241, reconciled against a $0.0035 reservation), five proposals were confirmed into
    profile version 1, and the leak scan found nothing. The production model
    was not called for this schema: Spark 1.3's strict schema output on the Standard ID was
    qualified in Sprint 0 (ADR 0003, ledger calls 6-7), and the same release accepted this
    schema; one `PRODUCTION=1 INTERVIEW=1` run (worst case $0.049) would close that gap.

15. **Export format 2.** The workspace export adds the interview turns (messages,
    proposals, decisions) and provisional concepts. Partial replies are not exported: they
    are never data, and a completed turn's reply is in its proposal.

## Consequences

- New error codes: `TAXONOMY_UNAVAILABLE`, `CONFIRMATION_REQUIRED`, `PROPOSAL_NOT_AVAILABLE`,
  `ALREADY_DECIDED`; new failure classes: `model_refused`, `output_truncated`; new event
  kind `run.partial_updated` and read path `GET .../interview/turns/{id}/reply` (decision
  13); migrations 0006 (a known zero cost for attempts with no call), 0007
  (`run_partials`), 0008 (the manifest's `adaptation`, `careerwright.concept_key` and the trigger
  that uses it) and 0009 (a partial records `stopped`, not `incomplete`; untouched $0.10
  run limits move to $0.15).
- A city outside the list, which Sprint 1 accepted as free text, is now refused on save.
  Stored version 1 documents still read; a person re-saving one with an unlisted city must
  pick a listed city.
- The You chapter (T6) builds the conversation, review tray and city picker on these
  endpoints; discovery (T6) uses the taxonomy search for its multi-query pool.
- Not done here: residence and work-rights fields (BND1-04 stays open for them), rendering
  the streamed reply (T6), an ESCO version-bump procedure beyond "new pin, reviewed
  migration".

## Human review checklist (H-11, reviewed by the product owner on 2026-10-28)

Agents applied each item below as recorded. The product owner reviewed the checklist on
2026-10-28: items 1–3, 5 and 6 are confirmed as recorded; item 4 is confirmed with one
change (rulings R2, R6).

- [x] **ESCO licence reading** (rights review). Reuse under Commission Decision
  2011/833/EU on two conditions, read from the ESCO FAQ on 2026-10-28: the attribution
  sentence wherever ESCO content appears, and adapted versions marked as such. Confirm the
  reading, the attribution text, the `adaptation` statement and where the API shows them.
- [x] **City list and aliases.** The 55 cities, their stable IDs and the recorded aliases
  (decision 4), including the decision to refuse plain "Newcastle".
- [x] **ONS regions** assigned to each city by the implementing agent (decision 4).
- [x] **Hard-constraint set** (decision 6): cities, target titles, weekly study hours and
  both spending limits. **Changed by the product owner:** add a salary floor (the minimum
  salary the person will accept, spec §4) as a hard constraint. Implemented in Task 6
  (decision 6; ADR 0007 decision 2).
- [x] **Basis of an answer with no value** (decision 8): shown as `inferred`.
- [x] **Concept-key folding** (decision 5): whether the plural heuristic refuses any title
  a person would expect to be accepted.

## Amendment, 2026-10-31 (the product owner's approval of the audit)

The product owner, 2026-10-31: "One thing that is really important to me is that we aren't
limited to a prefilled list of roles". They approved the audit's decision 2 (recognise any
UK job title, and always keep the person's own) and decision 3 (research roles that no list
holds). ADR 0015 records the role space; this ADR changes as follows.

- **Decision 5: provisional concepts carry their sources.** A provisional concept cites one
  of: the person's confirmation (as before); a title in the pinned ONS SOC 2020 coding index,
  with ONS's own unit group and ISCO-08 codes; or the title verified as a span on pages from
  independent permitted sources (ADR 0015 decision 2). A title a model proposes becomes a
  provisional concept only once one of those corroborates it; until then it stays a search
  hypothesis (DIV1-04), shown as not yet found. Why: the specification lets such a title
  count once "an authoritative occupational/professional source or independent employer
  evidence" backs it (DIV-1), and the ONS index is already pinned and imported. L0 widens
  that clause to independent permitted sources of any class, as the product owner approved
  (spec section 22, 2026-10-31).
- **The person's own words are always kept.** Nothing typed at the first question is
  refused (Task 6d). The duplicate check stays: a title that is an ESCO label as a concept
  becomes that occupation, never a second concept, and the person's words stay its label.
  How the first question offers that is to be settled by Task 6d.
- **Optional seniority and industry** beside a role or target title (spec sections 4 and
  18; the product owner's ESCO research). Matching ignores them; display and search keep
  them. The profile schema change is Task 6d's.
- **Open from this ADR's consequences:** residence and work-rights fields (BND1-04) move to
  Task 12a, with remote working (BND1-05).

## Amendment, 2026-11-01 (the product owner's school-leaver decisions 2, 3 and 4; Task 6f)

The product owner, 2026-11-01: "Many users will be final year school students who have never
had a job before." No separate student mode: the same answers serve everyone, and nothing
asks for or infers age.

- **"I haven't had a job yet" is an answer about the current role** (field state
  `no_job_yet`, the role's only), never a job title, Skipped or Unknown. It lights the
  person's light, and neither the demo nor the live interviewer asks the job question again.
  The first question saves it through the one write path (`POST .../origin/role/no-job-yet`,
  an expected version and an Idempotency-Key); What we know and a confirmed proposal save it
  through the same command as any answer. It names no occupation, so nothing is joined to it.
- **Two optional answers** (spec section 3's work status and qualifications): `work_status`,
  one of working, in education or training, looking for work, caring, other; and
  `qualifications`, each in the person's words and marked achieved or expected (at most 8).
  Both take Skip, Unknown and Prefer not to say, are never limits, and go through the one
  write path and the interview contract (the model proposes, the person confirms). The model
  writes a qualification as "achieved: …" or "expected: …". A qualification's status and a
  work status are always shown as Careerwright's reading, never as "You said", even where
  the words appear in the cited messages (fix round 1). An expected
  qualification is shown as expected everywhere and never read as achieved; Skills (Task 10)
  and Options (Task 12b) read both as entry facts later. Saved answers schema version 4;
  migration 0040 rewrites every stored document with both not yet asked (each answer it held
  keeps its state, value and source), and an older document still reads that way.
- **The one exception to append-only saved answers:** migration 0040 adds the two
  not-yet-asked answers to stored documents in place. A schema migration may add
  not-yet-asked answers in place; nothing else about a saved version changes, and no other
  write updates one.
- **The interview works without a job** (`interview-turn-5`): the instructions say "Someone
  may not have had a job yet: ask about school or college, volunteering, caring, clubs and
  hobbies; never treat no job as a gap", name the new answers (each asked at most once, a
  skip accepted, never the person's age) and say "their next step" for "the change". The
  explore opening is "What would you like your working life to be like?" (a proposal: the
  product owner settles the words at session W2), and the demo interviewer asks an unsure
  person next "What do you enjoy doing, at school, at work or in your own time?". No live
  call was made for this version: Task 6e runs the capped live check (R5).

## Amendment, 2026-11-02 (the product owner's yes after session W2; Task W2F, Muse's turns)

- **"Tasks you don't enjoy"** (`disliked_tasks`; spec section 4's "disliked tasks"): a
  fourth task answer, optional, at most 8, kept apart from the three of decision 6 and never
  a hard constraint. The model proposes it and the person confirms it through the one write
  path, like any answer (decisions 7 and 11). It informs the conversation only: discovery's
  answer set (`EVIDENCE_FIELDS`, which the slate, its written explanation and the strength
  also read) leaves it out, so it is never a search, a filter or a ranking input, and
  dislikes alone start no discovery. Saved answers schema version 5; migration 0046 adds it
  not yet asked in place (the exception above). The demo interviewer reads "I don't enjoy
  ...", "I don't like ..." and "I hate ...". Like any answer but a chosen target, changing
  it marks a slate as made on earlier answers, though no suggestion reads it.
- **`interview-turn-6`** (session W2's findings 4 to 7): the instructions add the new
  answer ("Keep these four apart"); one activity takes the same words in each task answer it
  belongs to; a list proposal leaves out anything the person takes back; a money limit
  hinted without a figure ("no pay cut", "nothing too expensive") is asked for in pounds as
  the next question, before any other, and no money value is proposed or invented without
  the person's figure; and with no start chosen (entry null), the interviewer never asks how
  they want to start but uses what they wrote. The safety and no-inference rules are
  unchanged. Evaluation cases INT-18 (a dislike and a take-back) and INT-19 (Sam's hinted pay
  cut, no start chosen) carry the rules; no live call was made here: the controller runs the
  capped live check (R5).
