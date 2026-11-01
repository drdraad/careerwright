### Spec Compliance

Scope: half A of `8a817f6..dec43e6`, everything under `backend/` (55 files, 6,147 insertions). I read the diff in 17 passes and treated the report as unverified. No suites were re-run. I ran three focused, read-only probes: pure-function Python against `nessa.profile.safety`, `interview.check_turn` and `fixture_interviewer`, and an offline analysis of ESCO v1.2.1 `occupations_en.csv` that re-implements `nessa.concept_key` in Python. The ESCO analysis is my approximation of the SQL function, not the database. No Docker, no live calls, no `.env`.

- ❌ Issues found:
  - The acute-distress screen fires on ordinary career phrasing ("I took my life savings out to retrain", "I don't want to live in London"). Its own docstring promises otherwise (`backend/src/nessa/profile/safety.py:10-11,32-39`).
  - DIV1-05 de-duplication folds distinct occupations. The union-find is transitive over any shared label, so it chains unrelated work together (`backend/src/nessa/profile/slate.py:229-245`).
  - S2.5 sketch: for 260 of 3,043 ESCO titles, an occupation the person explicitly chose stays "ambiguous", so they are asked to choose again with no end (`backend/src/nessa/profile/sketch.py:92-121`, `exploration.py:477,503`).
  - Addendum (b): the salary floor's period is never checked, yet the proposal is labelled `stated`. The demo fixture misreads periods (`backend/src/nessa/profile/interview.py:291-293`, `fixture_interviewer.py:54,129`).
  - Spec §4 DIV-1 says to "sample across occupational families and sectors before reranking". The pool is cut to 120 by relevance alone (`backend/src/nessa/profile/slate.py:281-282`).
- ⚠️ Cannot verify from diff (half B: apps/web, docs, the Sprint 2 review):
  - **You chapter UI:** sure/unsure entry and the "sure users bypass exploration" journey; tone choice; pause/resume UI; review tray (accept/edit/undo); editable "What we know"; one question displayed.
  - **Streaming and keys:** the MODEL-03 streamed-reply rendering; the MODEL-07 consent UI.
  - **Carried findings:** V-02, V-07, V-08 and S0-V01, V02, V05, V08.
  - **Support response UI:** it must send "Send my message anyway" with a new idempotency key, because the request fingerprint changes.
  - **`next` exception:** removal of the `next` 16.4.1 `minimumReleaseAgeExclude` (reported blocked by time).
  - **Docs:** `docs/reviews/sprint-2.md`, the ADR 0006/0007 updates, the H-12 checklist recorded as "not run — requires human", the runbook and CLAUDE.md.
  - **Register:** whether DIV1-10 can stay `verified` when sampling across families before reranking and oversampling are not done (see I-5).
  - **Browser checks:** Playwright, axe and screenshot evidence.
- Named-risk checks (one each):
  - **Authorization:** every new use case calls `visible_workspace` first:
    - `visible_discovery`, `discoveries` and `submit_discovery` (`exploration.py:157-198`);
    - `choose_target` (`exploration.py:459-463`); `requirement_sketch` (`sketch.py:175`);
    - `current_preferences` and `set_preferences` (`preferences.py:36,46`);
    - `submit_turn`, which screens only after `visible_workspace` (`conversation.py:197-201`).

    The occupation-choice `run_id` has a composite FK `(workspace_id, run_id)` (r0005:77). The new table has an RLS policy on the r0005 pattern (`r0010:50-55`) and is covered by the "every table has RLS" check (`tests/integration/test_isolation.py:188-192`). The 404 tests cover every new read and write (one weakly, M-1). I found no IDOR through run, choice or candidate IDs.
  - **Grounded discovery:** suggestions come only from ESCO hits. Model titles become candidates only through a label match; otherwise they are listed as unsupported (`exploration.py:405-418`). No score or percentage field exists (`discovery_schemas.py`). The slate is pure and deterministic. Preferences are never a filter, and the work style only adds queries.
  - **Model proposes, commands commit:** a target needs `POST /targets` through `commit_profile_version`. Discovery is a sealed-input run on the one activity. The integration test asserts an identifier-only journal, a reconciled attempt and a leak scan. The Contributor refusal does not depend on run kind (`identity/runs.py:146-147`, `identity/activity.py:281`, DB CHECK r0002:83), but no test exercises it for discovery (M-2).
  - **Salary floor:** the shape is right: `Money` minor units, a kept period, gross as a literal, a hard constraint, unknown is not 0, schema 1/2 documents upgrade on read, and `SALARY_FLOOR_NOT_APPLIED` appears only when a floor is provided. The defects are the period (I-4) and a £0 floor (M-7).
  - **Support policy:** it is deterministic, runs before any model call, nothing in it logs, and the model-output guard repairs then refuses. Its wording is marked provisional (H-12). The problems are false positives (I-1) and the "nothing has been saved" wording (M-8).
  - **Live eval (R5):** caps are checked under the ledger lock before the stack starts. It uses the test model only, refuses the production model, has its own `live-eval` scope, ledgers after the worker stops, and is absent from `make check` and `make acceptance`. I recomputed the ledger: rows 15–20 come to $0.00157486, with costs matching token × price row by row, and the running total is $0.021774 (M-11). The scope cap differs from the controller's 9 calls (M-10).
  - **Evaluation cases:** there are 39 synthetic cases with semantic expectations. Composition and checker issues are in I-6 and M-12.

### Strengths

- The model proposes searches, never suggestions. A suggestion can exist only if ESCO holds it, so REC1-06 and DIV1-04 hold by construction. Every suggestion carries its ESCO URI, the answers that found it, and words built from ESCO facts, never model prose (`exploration.py:284-341`).
- Slate controls are view parameters, never stored, and every exclusion is counted (`excluded`, `not_included` with reasons). A thin pool returns fewer suggestions, with the reason in words.
- Discovery follows the durable pattern of ADR 0002: input sealed and pinned to the profile version, a bounded repair, a spend reservation sized for two requests and tested arithmetically (`test_discovery_contract.py`), and a fixture proposer that reads the live prompt and passes the same check.
- The support screen sits after the authorization check and before any model or storage. The integration test proves no turn, run, event or leak, and that "send anyway" works.
- `live_eval.py` is careful:
  - it refuses before any call;
  - it ledgers even on Ctrl-C during the worker stop;
  - it scans for key leaks;
  - it now keeps per-case outputs so failures can be inspected.
- The honesty is good: REC1-09 is recorded as failed with its one-sample caveat, the one-question re-count is disclosed, and tests written after the code are disclosed.

### Issues

#### Critical

None.

#### Important

**I-1 — The acute-distress screen fires on common career-change phrasing** (`backend/src/nessa/profile/safety.py:35,37-38`)

- **What:** the patterns end at `\b`, so they match whatever follows. Probing `screen_message` on the final code returned True for all of these:
  - "I want to take my life in a new direction."
  - "I took my life savings out to retrain."
  - "I don't want to live in London."
  - "I hurt myself lifting boxes at the warehouse, so I need lighter work."
  - "There is no reason to go on with the accounting course."

  The interviewer itself asks about cities and budget, so these answers are likely.
- **Why it matters:** the person's message is withheld and they see a 999/A&E crisis response. The module's own docstring promises that "ordinary figures of speech" don't trigger it (`:10-11`). The non-trigger tests (`tests/domain/test_safety.py:49`) and SUP-06..08 contain none of these.
- **Fix:**
  - Constrain the object of the phrase: for example, `t(?:ake|aking|ook) my (?:own )?life(?!\s+(?:savings|in|into|back|forward|around))`, and `want to live` / `go on` only at the end of a clause (`(?=\s*(?:any ?more)?\s*(?:[.!?,]|$))`).
  - Add these sentences as SUP false-positive cases.
  - List them in the H-12 checklist alongside the known false negatives ("I can't go on", "I wanna die").

**I-2 — Near-identical folding chains unrelated occupations** (`backend/src/nessa/profile/slate.py:229-245`, used at `:268-280`)

- **What:** the union-find joins any two candidates that share any non-hidden label key, transitively. Two things the shared labels of ESCO v1.2.1 do in practice:
  - **One step:** "geologist" belongs to 6 concepts, and "operation manager", "general manager" and "facility manager" to 5 each.
  - **Chained:** in a 120-occupation pool of "repair/maintenance/outdoor" work, quarry engineer, mine manager, building caretaker and building cleaner form one group. The links are "mining engineer"/"quarry manager", then "facility manager", then "building caretaker".

  Within ISCO sub-major group 26, actor/actress, singer, composer, music producer and animation director fold together. Within 34, ski instructor, swimming teacher and sports coach fold together. Across the whole catalogue, one component has 319 members, including judge and puppet designer.
- **Why it matters:** folded members never reach the slate, and "Show why" calls them a "duplicate of" an unrelated occupation. That under-reports diversity and breaks DIV1-05 ("aliases and near-identical roles", not neighbours). The only test (`test_slate.py`, near-identical) covers a direct alias.
- **Fix:**
  - Fold only on an alias relation: one concept's preferred label is a label of the other, or the label sets are equal.
  - Never fold transitively: attach a candidate only to a group lead it aliases directly.
  - Add a regression test built from real chained ESCO rows (building cleaner and quarry engineer must stay distinct).

**I-3 — The sketch ignores the occupation the person chose** (`backend/src/nessa/profile/sketch.py:92-121`; `backend/src/nessa/profile/exploration.py:477,503`)

- **What:** `choose_target` stores only the preferred label as the target and puts the ESCO URI in the source locator. `_target` re-resolves the title through `concept_key_matches`, which includes alternative and hidden labels of every concept, and never reads the locator. 260 of 3,043 ESCO preferred labels also match another concept's label. "Administrative assistant" matches 3 concepts; "medical writer", "weaver" and "biomedical engineer" match 2 each.
- **Why it matters:** after the person picks one of these occupations (`replaces`), the sketch still says "Several ESCO occupations have this title. Choose the one you mean." Choosing again is a no-op (200), so it loops and never shows requirements. That defeats S2.5 for about 8.5% of occupations.
- **Fix:**
  - Resolve a target from its `occupation_choice` source's ESCO URI first (or store `concept_id` with the target), and fall back to label matching.
  - Add an integration test with a title that another concept also uses as an alternative label.

**I-4 — The salary floor's period is never verified, yet it is shown as `stated`; the demo fixture misreads periods** (`backend/src/nessa/profile/interview.py:291-293,259-265`; `backend/src/nessa/profile/fixture_interviewer.py:54,129`)

- **What:**
  - `_basis` checks only the amount. The comment says "the period is checked apart", but no such check exists.
  - Probe: the message "I will not work for less than £12 an hour." with proposal "12 per year", basis stated, gives no problems, basis `stated`, period YEAR.
  - A bare amount silently becomes yearly and is still `stated`.
  - The fixture turns "I get paid £500 a week" into "500 per year". It also turns "I could spend £1,500 a year on courses" into a minimum salary of £1,500 a year, because "a year" alone counts as a pay word.
- **Why it matters:** addendum (b) makes the period part of the value. `ProposedChangeOut.basis` tells the client that `stated` means "checked by the server", so the person is asked to confirm a mislabelled hard limit. Confirmation by name limits the damage but does not repair the provenance.
- **Fix:**
  - Mark a proposal `stated` only if the cited message also contains the period (year/annual, month, week, hour words). A defaulted period is `inferred`.
  - In the fixture, add week and require a pay word that is not next to a spend word.
  - Add one test for each case.

**I-5 — The working pool is cut by relevance only, never sampled across families** (`backend/src/nessa/profile/slate.py:281-282`)

- **What:** `leads[:limit]` keeps the 120 most relevant candidates. Spec §4 DIV-1 says: "Sample across occupational families and sectors before reranking; oversample under-retrieved catalogue areas". Family and sector bonuses act only in the greedy step, after the cut.
- **Why it matters:** P02 overflows the pool (DIV1-02 row: 120 kept, excess counted). The tail that gets cut is where other families and long-tail work sit, so diversity is decided before the reranker can see it.
- **Fix:**
  - Fill the 120 round-robin across ISCO minor groups, or per-family quotas, in relevance order.
  - Record oversampling as not done.
  - Half B should check that register row DIV1-10 does not claim "verified" for this part.

**I-6 — The two failing evaluation checks cannot tell checker artefacts from model behaviour, and the interview contract has a real gap** (`backend/tools/evaluation.py:145-147,154-157,193-201,278-282`; `backend/src/nessa/profile/interview.py:412`)

- **What, in the checker:**
  - `one_question` takes the union of questions across `reply` and `next_question` and de-duplicates only verbatim repeats. A paraphrase counts as two, and two asks in one sentence count as one.
  - `same_fields_as` compares one observation per arm on exact field sets, including optional, judgement-call fields. The INT-04/05 drift is `enjoyed_tasks` for "something more hands-on".
  - `_has` matches substrings: `" man"` matches "manager" (INT-05 `values_avoid`), and "type" or "test" match "types" or "contest" (INT-01, INT-02 `question_avoids`).
  - The one-question check was changed after the live failures and never re-run against those outputs, which were not retained.
- **What, in the behaviour:** the instructions say "write a short, warm reply ... and ask at most one question" but never say the question belongs only in `next_question`. The web shows the checked reply in the thread and `next_question` as the question heading (`apps/web/src/components/Conversation.tsx:47-56,323-328`), so a repeated question appears twice.
- **Why it matters:** REC1-09 and one-question evidence currently measure noise, while a likely user-visible duplication goes unaddressed.
- **Fix:**
  - Tell the model the reply must not contain the question, and check that `reply` has no "?" when `next_question` is set.
  - Run counterfactual arms over several samples and compare only fields stated unambiguously (`current_role`, `weekly_study_hours`), against a tolerance set in H-12.
  - Use word-boundary matching in `_has`.

#### Minor

- **M-1** (`backend/tests/integration/test_discovery.py:321`): the 404 test for `POST /targets` uses a missing `concept_id`, so it returns 404 whether or not the workspace check runs. Use a real `concept_id` from the slate. The code itself is correct.
- **M-2** (`backend/tests/support/fake_models.py` discovery branch, unused): the discovery run kind has no failure-path test (invalid output twice → `invalid_model_output`; slate of a failed discovery → `PROPOSAL_NOT_AVAILABLE`, `exploration.py:344-360`). There is also no non-synthetic, Standard-only test for the discovery kind, which was a named risk. The mechanism does not depend on run kind (`identity/runs.py:146-147`, `activity.py:281`, r0002:83).
- **M-3** (`backend/tests/integration/test_evaluation.py:64`): the assertion `60 <= pool_size <= 120 or beyond_pool_limit == 0` passes for any small pool. Assert P02's pool size directly.
- **M-4** (`backend/src/nessa/profile/exploration.py:241-246`, `slate.py:41`): ranks are normalised to each query's own top hit, so every query's best match scores 1.0 (an any-word match scores 0.5) and clears the 0.35 floor however weak it is. The floor cannot reject a uniformly weak query. This sits in the provisional weights (H-12); consider an absolute `ts_rank` floor.
- **M-5** (`backend/src/nessa/profile/sketch.py:129`): `except NessaError` treats every search error as "no close matches". Narrow it to `reason == "no_search_terms"`, as `_search_hits` does (`exploration.py:229-239`).
- **M-6** (`backend/src/nessa/profile/exploration.py:395`): an unsearchable current role shows as a query with 0 hits instead of under `unsearchable_queries`, unlike model queries.
- **M-7** (`backend/src/nessa/profile/document.py:123`): `SalaryFloor.amount` accepts 0, so "I don't mind about pay" can become a confirmed £0 floor. Require a positive amount; "no floor" is Unknown or Skipped.
- **M-8** (`backend/src/nessa/profile/safety.py:45-46`): the text says "nothing has been saved", but `run_idempotent` stores a receipt with the response and a SHA-256 of the request, message included (`identity/receipts.py:32-37`). Reword it to "your message wasn't saved", or skip the receipt for this case.
- **M-9** (`backend/src/nessa/profile/exploration.py:375`; `api/routes_discovery.py:136`): the slate is recomputed against whatever release is held now, while the docstring says "pinned taxonomy". Record the release ID with the discovery and flag a mismatch.
- **M-10** (`backend/tools/live_eval.py:105`): the `live-eval` scope allows 24 requests where the controller's per-scope cap was 9. The cost cap ($0.05) is tighter and 7 requests were used. The controller should ratify ruling 5 or lower the default.
- **M-11** (ledger, `docs/evidence/live-usage.jsonl` rows 15–20): rows 15–20 total $0.00157486, which rounds to $0.001575; the report and commit say $0.001574 (truncated). The total of $0.021774 is correct.
- **M-12** (`backend/tools/evaluation_cases.json`):
  - 16 of the 39 cases (SUP-01..09, GRD-01..07) test deterministic code with canned inputs.
  - INT-06..14 have never run anywhere.
  - The ≥30 count is met, but the evidence about model behaviour is six single samples.

  This is disclosed; note it for H-12.
- **M-13** (`backend/src/nessa/profile/safety.py:150-168`): demographic words cause false refusals in discovery. Probe: the query "maternity support work for women" for a person who wrote only "mothers" was refused for "women", which costs the repair and can fail the run. This belongs in the H-12 list review.
- **M-14** (`backend/src/nessa/profile/exploration.py:327`): "works as a {title}" produces "a administrative assistant".
- **M-15** (`backend/src/nessa/profile/preferences.py:6`): the docstring says "nothing is asked until the person resumes", but the API accepts turns while paused (by decision, ADR 0007 decision 1). Make the docstring match.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** Authorization, grounding (model searches, ESCO-only suggestions, no percentage) and the durable and live-eval cost controls are sound and well tested. However, several deterministic rules give wrong results on real inputs: the distress screen, transitive de-duplication, sketch resolution after a choice, the salary period, and the pool cut. In addition, the two failing evaluation checks cannot yet separate checker noise from model behaviour.

**Evaluation failures, checker or behaviour:**

- **One-question (INT-01..03):** mostly a checker defect. At live-run time the check summed every "?" in the reply and next_question, and all three cases scored exactly 2, which fits one question repeated in both fields. The outputs were not kept, so this cannot be proven.
- **The real defect behind it:** the prompt and contract never say where the question goes, and the UI shows both fields, so a repeated question is visible to the user.
- **Counterfactual (INT-04/05):** a measurement defect. One sample per arm and an exact field-set match that includes a judgement-call field give no evidence of demographic sensitivity either way.
- **REC1-09:** "failed (one sample per arm)" with its caveat does not overclaim. "Inconclusive" would be more accurate.
