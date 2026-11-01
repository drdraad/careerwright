# Task W2, slice W2B review: the deterministic sources (c84729e..f70f88d)

Reviewer: Claude (Opus 5.5), task reviewer. Read-only; no subagents; no live, web or model call.

Method: brief, slices (W2B and the binding rulings), dispatch, report, then the package diff
in five passes (ADRs; slate, titles and taxonomy; exploration; API and capability; tests and
evaluation). Plan section 4 and SW.5, ADR 0006/0007/0012/0014 and session 2's record read
for the named risks. Focused checks outside the diff, one per named risk:

- `make check` on f70f88d: exit 0 (ruff, mypy, pytest 1,532 passed / 308 deselected, fixture
  validator, generated client matches OpenAPI, Biome, `tsc`, Vitest 299 passed).
- The pinned ESCO v1.2.1 CSV (`var/datasets/`, unzipped to my scratchpad, read with an
  offline script): every preferred, alternative and hidden occupation label searched for the
  persona titles, and the type-ahead's every-word-prefix rule simulated on preferred and
  alternative labels.
- `evidence.py` `_reading` (does "used" ever supersede a levelled answer), `questions.py`
  (`UNSUPPORTED_CLAIM`), `receipts.run_idempotent` (are refusals stored), `RunOut` (does a
  receipt carry model output), `identity/` diff and `APPLICATION_VERSION`, the
  `chosen_occupation_uris` consumers, the vector built at import (`taxonomy_store.py:170-190`).
- Not run: `make acceptance` (the controller's), the integration suites, the timings.

### Spec Compliance

❌ Issues found:
- SW.5 "Destinations and connections are joined by shared essential skills, never by shared
  words in a title ... fix the slate where it matches on words": done for the person's own
  titles and for the first slate; not done for the task, transferable and work-style
  searches, which still reach occupations through title words (hidden labels, ISCO group
  labels, unrecognised variants of the person's title) and through description keywords
  (I1 `taxonomy_store.py:182-184,211`, `exploration.py:520,694`; I2 `exploration.py:468`).
- Overlooked strength: the run reads every answer the person ever gave, not the answers the
  turn added, which ADR 0014 decision 3, the migration and `RunKind` all say it reads; a
  declined strength therefore returns on later turns (I3, `strengths.py:208`).
- "The demo shows a scripted example, labelled": the demo's example is a shared-word
  heuristic, the kind of matching the product owner rejected (I4, `strength.py:397-409`).

Met (checked in code): the type-ahead (preferred and alternative labels, never hidden;
deterministic; no model, key or workspace; honest `matches: []`; a release missing is an
error, not empty); the first answer through `run_idempotent` and the one profile write path
with an `occupation_choice` source; "usual in your role" display-only and "used" self-reported
(I traced every reader: only `get_origin` reads usual skills; "used" reads `unsupported`,
level unknown, and as another rubric's answer only fills a row with no answer of its own,
never superseding a level); the role's join and the first slate; the connection rule with its
reason (ADR 0007 decision 14); the strength as one `RunTask` composed in `worker.py`, its own
run of the unchanged model-run workflow (`identity/` untouched apart from the enum, registry
and fixture map; `careerwright-l0-1` unchanged); quotation span-verified with the slate
explanation's verifier; skill checked against the destination's essential skills; one per
turn (`UNIQUE turn_id`, workspace lock); support turn refused before any run (refusals are not
receipts; nothing stored); demo uses the fixture model at zero cost; confirm and decline with
expected version and `Idempotency-Key`; receipts hold ids, versions and run state only, never
the proposal; forward-only migration with RLS policies matching earlier tables; the new
adapter listed in `test_boundaries.py`; client regenerated; tests offline (fake provider and
fixtures); no live call.

⚠️ Cannot verify from diff: `make acceptance` on f70f88d (one run failed on the known shutdown
hang, per the report); the 19 ms / 24 ms timings; the before/after slates (the scratch test
was deleted); DSC-10..14 on the full release; live strength behaviour (R5); every human item.

### Answers to the named risks

- **Words vs skills.** Letter: mostly met for titles, broken at the edges (I1). Spirit: not met
  for P01 and P02 (I2). Destinations are still reachable by word matching through the task,
  transferable and work-style channels; connections are not (they need a role join). Smallest
  deterministic fix: one essential-skills-only search vector for those channels (below).
- **P04 and P05 empty.** Honest: "Registered nurse", "Bookkeeping assistant" (and P01's "Data
  quality analyst") are not a preferred, alternative or hidden label of any occupation in
  v1.2.1, and resolution compares all three kinds with `concept_key`. Not a missed lookup. But
  the type-ahead also returns nothing for those exact titles, so the "sharper question" has
  nothing to offer (I5).
- **Strength run kind.** Follows the pinned pattern (see above). Defects: input scope (I3),
  demo script (I4), untested kind-specific failure path (M4).
- **Confirm and decline.** Correct paths and receipts. Confirmed is `used`, `self_report`, no
  level, read `unsupported`: self-reported, never evidenced. Re-proposal after a decline does
  nag, deterministically in the demo; smallest fix in I3, storing nothing.
- **"Usual in your role".** Display-only, confirmed. "Used" is self-reported and counts for
  nothing; no slate, rank, readiness or gap reads it.
- **Truth and failure.** Unknown never zero; errors are `CareerwrightError` codes with static
  messages; reads in `actor_transaction` (taxonomy in `system_transaction`, as before); no
  empty-success path found except one unreachable-in-practice case (M3).
- **One second.** Measured on the API path the person hits (type-ahead, `POST origin/role`,
  `GET origin`), in-process (no Next.js forwarder, no browser), on real PostgreSQL 16 and the
  full release, asserted under 1 s in an integration test that `make acceptance` runs. It
  catches gross regressions only and covers one role (M1).
- **Provisional rules.** Recorded as provisional (ADR 0007 header, ADR 0014 decision 3, ADR
  0012). Reasons given for the connection rule and the strength gate; the minimum of 3 has
  only release statistics, and ADR 0007 does not tie them to session W2 (M6).

### Strengths

- The title join is clean: titles resolve to ESCO occupations (chosen URI, else exact label,
  ambiguity kept and never picked), joins are pure functions (`skill_join_hits`,
  `unexpected_connection`) with domain tests, and "not an ESCO title" is said, not hidden.
- The "data analyst" after-slate is now grounded (data scientist 22 shared, data quality
  specialist 12, chief data officer 7, ...) and the connection sentence is built from counts.
- The strength reuses the explanation's verifier and the one activity; the model sees refs,
  not IDs; finding none is an answer; the receipt test asserts no proposal.
- "Used" was placed carefully in ADR 0012's reading rules, with a DB CHECK mirroring the code.
- Honest report: concerns 1, 2 and 4 are real and were disclosed, as was the acceptance flake.

### Issues

#### Critical

None.

#### Important

**I1. Title words still reach the slate through the "non-title" search.**
`backend/src/careerwright/catalogue/taxonomy_store.py:182-184,211`,
`backend/src/careerwright/profile/exploration.py:520,694,699`.
What: `titles=False` zeroes the preferred (A) and alternative (B) labels only. The vector puts
hidden labels in part C with the essential skills, and the ISCO unit group's label in part D
with the description; both still weigh. (a) A hidden label is an occupation title. (b) The ISCO
label is the group's title: P02's "repairing physical objects" (any-word) matches every
occupation in 3111 "Chemical and physical science technicians" and 3119; a live query holding
"analysts", "clerks" or "assistants" matches whole groups ("Systems analysts", "Accounting
and bookkeeping clerks", "Medical assistants"). (c) A live query that is a variant of the
person's own title ("Data analysts", "data analyst roles") is not recognised as their title
(`_title_key` folds case and spaces only; `concept_key` also folds plurals and punctuation) and
is word-searched over (a) and (b). The DSC cases use the fixture proposer, which repeats titles
verbatim, so none of this is exercised. ADR 0007 decision 13 records (a) only.
Why it matters: the plan's "never by shared words in a title", in letter, on the live path.
Fix: build a second vector at import with the essential skills' labels only, backfill it for
the held release in a forward migration, and use it whenever `titles=False`; match model
queries to the person's titles with `concept_key`. Add a DSC case whose proposer query is a
plural of the role.

**I2. Task and work-style searches still match keywords in ESCO descriptions (SW.5's "fix the
slate where it matches on words" is half done).**
`backend/src/careerwright/profile/exploration.py:468` (`_search_hits` → part D).
What: P01's after-slate is ICT information and knowledge manager, house builder, online
community manager, bridge inspector, branch manager and chief operating officer; house builder
comes from the work style "structured" matching "structures" in its description (the report's
own finding). P02's six all come from task and work-style words ("working outdoors",
"practical", "small team"), now including consultant social worker. DSC-12 checks only the
unmatched title and a size of 3; nothing guards the task channel.
Why it matters: this is what the product owner called "arbitrary matching on keywords" and
said they would be "very disappointed" to see. P01 is the persona the routes acceptance runs on.
Fix (deterministic, same change as I1): run task, transferable and work-style searches on the
essential-skills-only vector, so each such suggestion is reached through an essential skill
whose label holds the person's words, and let its why-line name that skill; add an evaluation
check that a task-channel suggestion's matched words sit in one of its essential skills.
Whether work-style words should retrieve at all is the product owner's (spec section 4 makes
them a source of hypotheses): put P01's before and after on session W2's sheet. This changes
DIV-1 task retrieval, so the controller should rule on scope before W2C builds on the slate.

**I3. A declined strength returns on every later turn; the run reads all answers, not the
turn's.**
`backend/src/careerwright/capability/strengths.py:208,216`; the docs it contradicts:
`identity/records.py:98`, `migrations/versions/r0031_first_moments.py:9-10`,
`docs/adr/0014-the-living-world.md:65`, the `capability/strength.py` docstring.
What: `_added_answers` only gates the request. The input is then every quotable answer in the
profile and every essential skill not answered used or done. A decline changes none of that,
and a later turn only appends its new answer, so the demo fixture (first answer, in order,
sharing a word) proposes the identical strength on every later turn that adds an answer, and a
live model very likely does too.
Why it matters: it nags, and "one proposal per turn that has new answers" becomes a proposal
about old answers.
Fix: send only the answer items the turn's decision added (present in the turn's profile
version, absent from the version before, as `_added_answers` already compares); refuse
`no_quotable_answer` when none of them is quotable. Stores nothing and uses nothing for
suitability. Test: decline, then a later turn adding another answer does not propose the
declined quotation.

**I4. The demo's "scripted" strength is a shared-word match.**
`backend/src/careerwright/capability/strength.py:397-409`;
`backend/tests/domain/test_strength.py:175`.
What: the fixture pairs the first answer with any skill label sharing one content word. The
test's own example pairs "tidying messy data" with "deliver visual presentation of data"
(only "data" in common): a wrong pairing.
Why it matters: without a key this is the only strength the product owner can see, and the
one session W2's captures will show. It is keyword matching, which they rejected; labelled
synthetic, but plan section 4 asks for "a scripted example".
Fix: script it: a small fixed table (answer phrase → ESCO skill URI) for the demo journey's
known answers, still passed through `check_strength`, and none otherwise. At the least, require
all content words of the skill label to appear in the answer.

**I5. The type-ahead finds nothing for three of the five personas' own titles, and the API
offers nothing for the "sharper question".**
`backend/src/careerwright/catalogue/taxonomy_store.py:307`,
`backend/src/careerwright/catalogue/taxonomy.py:133`.
What (simulated on the pinned CSV): "Registered nurse", "Bookkeeping assistant" and "Data
quality analyst" match 0 occupations; "registered n" already empties the list. "nurse" (21
occupations), "bookkeeping" (bookkeeper) and "data quality" (data quality specialist) find the
closest ESCO titles. The slate's fewer-reason tells P01, P04 and P05 to "Choose the ESCO
occupation closest to it", but typing their title gives them no candidates.
Why it matters: the first ten seconds fail for these personas unless something else asks the
sharper question; W2C needs to know who does.
Fix (rule before W2C): when every-word matching finds nothing, return the occupations whose
labels match the most typed words, flagged `partial: true`, so the UI asks "ESCO doesn't list
that title. Is it one of these?". The person chooses; nothing is joined by words. Or W2C
re-queries with fewer words. Either way, test it on P01, P04 and P05.

#### Minor

**M1. The one-second evidence is narrow.** `backend/tests/integration/test_first_answer.py:81,105-106`.
One role (36 skills), one run, in-process, about 20× headroom (43 ms against 1 s), and only "d"
among single letters (the slowest, 87 ms). Fix: also time the occupation with the most
essential skills or skill neighbours, and a few single letters ("a", "s", "c"); record the
numbers where W2D cites them.

**M2. The connection on an ambiguous role states a fact about no single occupation.**
`backend/src/careerwright/profile/exploration.py:816-838`.
In a discovery, a role several occupations hold is joined over the union of their skills, and
the sentence says "A bus operator and X share N essential skills". The first slate already
refuses ambiguity. Fix: no connection unless the role names exactly one occupation.

**M3. A complete run with no readable output reads as "none found".**
`backend/src/careerwright/capability/strengths.py:99-102`,
`backend/src/careerwright/api/routes_origin.py:103`. `found: false` is an answer; a missing
output is a failure. Fix: raise `INTERNAL_ERROR` in `_view`, as it does for a missing run.

**M4. Test gaps.** `backend/tests/integration/test_origin.py`. Missing: the strength kind's own
failure path (invalid twice → `invalid_model_output`; Task 6 review A-M2 asked the same of
discovery), a confirm with a stale capability version, a decision on a failed run
(`PROPOSAL_NOT_AVAILABLE`), `STALE_INPUT_VERSION` when answers changed after the turn, and the
`recite` path (choosing the occupation for words already typed).

**M5. Choosing a role replaces the person's words with ESCO's title.**
`backend/src/careerwright/profile/exploration.py:1058`. Picking "IT support technician" makes
the role read "ICT help desk agent". Resolution already reads the source's URI, so the picked
label could be kept. Plain-words question for W2C and session W2.

**M6. Provisional rules not tied to session W2.** `docs/adr/0007-conversation-discovery-and-support.md:18-21,522`.
Decisions 13 and 14 say "need product owner confirmation" but not when; the minimum of 3 has
release statistics but no reason; the known limits omit the ISCO group label (I1b). W2D should
put each provisional rule (3 shared, Jaccard, best 30, the connection rule, the strength gate,
the quotable fields, `used`) on session W2's sheet.

**M7. Notes for W2C.** `held_back` is a 422 `INSUFFICIENT_EVIDENCE`: the client must not ask on
a support turn and must never show that code's words beside the support panel. A strength's
horizon destinations are the first slate's only (`strengths.py` `_destinations`): if the
horizon shows a discovery slate, a proposal could name a destination not on screen.

**M8. Three "chosen occupation" lookups with different normalisation.** `profile/titles.py`
(`preferred_label.casefold()`) vs `capability/commands.py:169` (`title_key`) vs
`profile/sketch.py:93`. Pre-existing duplication (report concern 5), now diverging. Final-review
list.

**M9. "Added answers" counts a removal.** `backend/src/careerwright/capability/strengths.py:120`.
Any change to a quotable field while provided passes the gate. Resolved by I3's fix.

### Verdicts on the implementer's rulings

1. Titles resolve, never search: **agree**. Verified honest for P01, P04 and P05. See I5.
2. Task searches drop title words: **agree in direction, incomplete** (I1, I2).
3. 3 shared skills, Jaccard, best 30: **accept as provisional**; state why 3 (M6).
4. The role is never a first-slate destination: **agree**.
5. `current_role` with an `occupation_choice` source; the role's choice in
   `chosen_occupation_uris`: **agree**. Its consumers key by title, so it is harmless (checked
   `capability.commands._chosen` and `sketch._chosen`). See M5.
6. `recite` on the one write path: **agree**; narrow. Untested (M4).
7. `used` as a sixth answer: **agree**. Checked: it never supersedes a row's own level, it reads
   `unsupported`, and the DB CHECK matches.
8. The strength trigger: **agree with the gate, disagree with the input** (I3).
9. Quotable fields (enjoyed, confident, evidenced): **agree**.
10. Destinations (targets naming one occupation, then the first slate): **agree**; align with
    W2C's horizon (M7).
11. Declining records only the decision: **agree** it stores nothing about the skill; not
    enough alone (I3).
12. The demo's shared-word example: **disagree** (I4).

On the report's concerns: 1 is I2; 2 is I5; 3 is M6; 4 is I3; 5 is M8; 6 (the shutdown hang) I
did not verify: the controller's `make acceptance` decides.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The core is sound and well tested: the title skill join, the first slate, the
connection, `used` and the strength's run pattern, receipts and gates. But the slate still
matches on words outside the person's own titles (I1, I2). The strength re-proposes declined
answers (I3). The demo's revelation is a keyword match (I4). Three personas cannot find a
closest title by typing their own (I5). All are fixable within the slice, and I2 and I5 need a
controller ruling before W2C builds on them.
