# ADR 0007: The You chapter's conversation, grounded discovery and the support policy

- Status: Accepted (Task 6, Sprint 2: S2.3-S2.6). Decision 7 (the support policy, redesigned
  in fix rounds 4 and 5: its word lists and windows, its wording and its resources) and decision 5's slate
  weights are **provisional, need product owner and reviewed sign-off** (ruling R6; human
  gate H-12). Decision 2's salary floor is
  the product owner's change to the hard-constraint set (H-11, 2026-10-28).
- Date: 2026-10-28
- Requirements: REC1-01..10, DIV1-02, DIV1-04..12, STATE-05, STATE-06, STATE-08, PROF-04,
  PROF-07..09, MODEL-03, MODEL-07, TEST1-10; spec sections 3, 4 and 16; ADR 0006

## Context

Task 5 built the backend of the conversation (the InterviewTurn run kind, proposals,
confirmation, a streamed reply) and the ESCO taxonomy with full-text search. Sprint 2's
second half turns them into the You chapter (sure or unsure entry, a tone, pause, a review
tray, an editable "What we know"), a grounded and varied slate of career hypotheses, an
early requirement sketch, and a minimal policy for acute distress and inappropriate
inference, with at least 30 evaluation cases and a capped live run.

## Decisions

1. **Interview preferences are a record of their own** (`interview_preferences`, migration
   0010): how the person chose to start (`sure`: "I know my direction"; `unsure`: "Help me
   explore"), the tone (`practical`, `gentle`, `challenge`) and whether the interview is
   paused, one versioned row per workspace (`GET/PUT .../interview/preferences`, expected
   version, idempotency key). They are preferences, never profile facts or planning limits;
   null means not chosen (the interviewer then keeps to `practical`). Each turn seals them
   into its input, so the prompt (now `interview-turn-2`) tells the model how to proceed:
   a sure person confirms the target and its level and is not asked to explore; an unsure
   person is asked about tasks before any career is named. Pause is honoured by the web app:
   nothing is asked, and every way of sending (Send, Try again, Send it again) is disabled
   with the reason "Paused: resume to send." until Resume; the composer stays in place. The API does not refuse a message while paused: pause is the
   person's own setting, not a lock. "Help me explore instead" saves the entry as `unsure`.

2. **Profile schema 3** adds two fields; older documents read them as not asked.
   - `work_style`: how the person says they like to work, a list of their own phrases. It
     is the spec's optional "work style" layer: never forced, never a personality type, and
     never a limit. Discovery searches with it and weighs it below what the person does or
     enjoys (decision 5); it can only add candidates (REC1-03).
   - `minimum_salary`: the lowest gross pay the person will accept, with its period (`year`
     unless they say otherwise; `month`, `week` or `hour` as given; never annualised, spec
     section 5). It is a **hard constraint** (the product owner's change to ADR 0006 decision
     6): the interview may propose it, only explicit confirmation establishes it, and
     Unknown, Skipped and Prefer not to say are answers, never 0 (a new floor is more than
     £0; "no floor" is Unknown or Skipped; the rule applies to input only, so a version
     stored before it still opens, and undoing to one refuses with `no_longer_valid`). The
     period is part of the value: a proposal is
     `stated` only when the cited words give both the amount and that period ("an hour",
     "weekly", "annually"); a defaulted or different period is `inferred`. Until regional pay
     evidence exists (Sprint 3), nothing can apply it: the slate says so in
     `limits_not_applied` and removes nothing for pay, and unknown pay is never treated as
     below it.

3. **One useful question at a time** is the interviewer's job and part of the contract
   (`interview-turn-3`): the question lives only in `next_question`, which holds at most one
   question mark, and beside it the reply holds none (a validation problem, so the one
   repair applies). With no next question there is nothing to repeat, so a "?" in the reply
   costs no repair. The web app shows the reply and the question apart, so it is asked once.
   The evaluation checks each field on its own (`one_question`, which also counts a second
   ask joined to the first in one sentence) and `missing_excludes`, never exact prose; the
   repair rate is for the H-12 and release evaluations to track. Earlier turns stay one
   action away.

4. **Discovery is a run kind on the one activity** (`discovery`; ADR 0002, ADR 0006
   decision 10). The model proposes **searches, never suggestions** (`discovery-queries-1`):
   it reads only the confirmed answers that describe work (current role, targets, the three
   task fields, work style; never places, money, hours or a name) and returns up to 8 short
   ESCO queries, each in one of the spec's channels (tasks, environment, transferable,
   cross-industry, less familiar) and quoting the answers it rests on, plus up to 3
   "surprising but plausible" titles. `check_discovery` refuses a query that quotes
   something the person never said, or that searches by a health condition, personality
   type or protected characteristic the answers do not contain (one bounded repair, as for
   interview turns). Demo workspaces use a deterministic fixture proposer
   (`nessa-fixture-discovery-1`: each answer as a query, no invented titles); the database
   confines both fixture models to demo workspaces and to these two kinds. A discovery
   pins the profile version it read. Without an answer that describes work it is refused
   (`INSUFFICIENT_EVIDENCE`) before any run exists; without a taxonomy, likewise.

5. **The slate is deterministic code** (`nessa.profile.slate`), recomputed on each read
   (`GET .../discoveries/{id}/slate`) from the stored searches, the pinned answers and the
   held ESCO release, so it is reproducible without storing a second copy. The searches
   record the release they were chosen for; a slate read against another release says so
   in a note.
   - *Retrieval.* Each query runs twice against ESCO's English full-text index: occupations
     matching every word score their rank over the best such rank; those matching only some
     words score at most half that (any-word search ranks a common word in a title highly).
     Nessa adds the current role (searched) and the person's own target titles (exact label
     matches). A model title becomes a candidate only if ESCO holds it as a label (DIV1-04);
     otherwise it is listed as an unsupported hypothesis, never suggested.
   - *Pool.* Hits are pooled by concept (an alias is the same concept). An occupation in the
     same ISCO minor group as another, whose preferred label is one of the other's
     non-hidden labels (as a concept key) or that has the same labels, is near-identical to
     it and counts once, the most relevant representing them (DIV1-05). Folding is never
     transitive: a candidate joins a group only through its lead, because ESCO gives many
     distinct occupations a shared label ("geologist", "facility manager"), and chains of
     them once folded quarry engineers with building cleaners. Nor does it cross kinds of
     work: ESCO lists "biochemist" as a chemist, but that is related work, not the same
     role. By an offline count (Python approximation of `nessa.concept_key` over ESCO
     v1.2.1's preferred and alternative labels), 319 occupation pairs are one alias apart:
     155 across minor groups no longer fold, and 164 within one still do (for example
     physiotherapist and occupational therapist; H-12). The pool is bounded at 120 (the soft 60-120 target), filled
     round-robin across ISCO minor groups in relevance order so every retrieved family is
     sampled before relevance cuts any (spec section 4, DIV-1), and the excess is counted.
     Oversampling catalogue areas the search under-retrieves is not done.
   - *Unsearchable* queries (no searchable word), the model's or the current role, are
     listed as such, never run as a search that found nothing.
   - *Relevance* is the best channel-weighted score plus 0.2 per further query that found
     it. Work-style hits count 0.6, cross-industry, less-familiar and hypothesis hits 0.9,
     the rest 1. No pay, popularity, prestige or AI figure enters (DIV1-07); no percentage
     is produced (REC1-05).
   - *Direction* is relative to the person (DIV1-12): close to what they do now (its ISCO-08
     minor group is one of their current role's or targets', or they named it), building
     on skills they could carry over (a transferable or cross-industry query found it), or
     something different.
   - *Selection* is a constrained greedy reranker with no optimality claim (DIV1-06): each
     step takes the eligible candidate maximising relevance plus small bonuses for a new
     family (ISCO minor group, 0.3), a new sector (major group, 0.15) and an under-filled
     direction (0.4; quotas 2/2/2), less 0.3 per candidate already shown from its family, at
     most 2 per family. A relevance floor (best score 0.35) means a slot is never filled
     with a weak match: a thin pool returns fewer, with the reason in words.
   - *Controls* (REC1-08) are view parameters, never stored and never limits: `emphasis`
     (`practical`, `unfamiliar`, `broad`: a lower floor and one per family, `deeper`: up to
     4 per family, stated in a note) and exclusions of titles or kinds of work, counted in
     `excluded`. Excluding a title never excludes its family. Every pooled occupation not
     shown says why ("show why this wasn't included").
   - **Provisional (R6, H-12):** every weight, quota and floor above is product policy to
     be evaluated, not an estimate of fit. Known limit: ranks are normalised to each query's
     own best hit, so a query's best match clears the floor however weak the query is (an
     any-word match scores at most 0.5). An absolute rank floor needs calibrating on the
     full release; it is not set in L0 and is listed for H-12.

6. **A suggestion's words come from facts, not model prose.** "Why this could suit you"
   quotes the answers that found it and the search that matched ESCO's record; "What might
   not suit you" names ESCO's essential skills (not yet compared with experience), a
   regulated-profession mark and, when familiarity is known, a different kind of work;
   "Try it before committing" offers an informational interview and one of its tasks on a
   small scale. Entry gates and evidence gaps say plainly what is not researched yet; a
   later absence of listings is a demand signal, not proof the work does not exist
   (DIV1-09). Every suggestion carries its ESCO URI as its source, the release's
   attribution and adaptation are shown with the slate, and it becomes a target only when
   the person chooses it (`POST .../targets`, REC1-07): the one write path, with an
   `occupation_choice` source naming the ESCO URI and the discovery. The same command
   resolves an ambiguous target title to the occupation the person means (`replaces`).
   Model-written explanations are not used in L0: grounding by construction was preferred
   to a second paid call whose prose would need its own checks.

7. **The minimal support policy** (`nessa.profile.safety`, `support-policy-5`): one
   deterministic, recall-first screen over normalised words (controller rulings, Task 6 fix
   rounds 4 and 5). It is kept apart from career suitability: it scores, labels and
   remembers nothing. The four UK services were checked on their own pages on 2026-10-28
   (999 or A&E; NHS 111, mental health option; Samaritans 116 123; Shout 85258). One
   hand-written table is the test (`tests/domain/test_safety.py::CORPUS`): every shape the
   reviewers reported in re-reviews 2 to 4 must trigger the flow, and their career examples
   with no listed word must not; each row is also checked inside other text and in capitals.
   It shows that those shapes are caught, not that every possible wording is.
   - *Why one screen.* Fix rounds 1 to 3 tried to tell intent apart with hand-written
     patterns: a blocking tier for first-person present intent, a note for every other
     mention. Each round traded false positives for false negatives: re-review 3 found
     first-person shapes that reached neither tier (C-1), the blocking tier firing on career
     text with no risk stem at all ("lifeguard", "without meetings") or on object frames
     ("life sciences", "life savings") (N-I1), and uncontracted negations reaching neither
     (N-I2). Precise intent classification by pattern is not achievable here, so the
     classifier was removed (round 4). Round 4 still matched phrase grammar, family by
     family, and re-review 4 found forms one family accepted and another lacked (I-1), so
     round 5 matches normalised words by proximity instead.
   - *Normalisation* (`words_of`). Compatibility forms (NFKC); every apostrophe variant
     (curly, modifier letter, grave, acute) to `'` and every hyphen and dash variant to `-`;
     soft hyphens and zero-width characters removed; lower case; words split on anything
     else, a hyphenated word staying one word; contractions spelt out: any "n't" to "not"
     (can't, won't, ain't included), the same forms without an apostrophe (dont, cant,
     hadnt, ...), cannot, 'm, 're, 've, 'll and 'd ("would"), and wanna, gonna, gotta,
     tryna to "want to", "going to", "got to", "trying to".
   - *Listed words*, any form: a word starting suicid-, overdos-, self-harm or selfharm,
     and "self" followed by a word starting harm.
   - *Constructions*, each a core word with its markers in a small window of words (the
     windows are policy, H-12): kill / hurt / harm / cut (-s, -ed, -ing) with a reflexive
     (myself, yourself, himself, herself, ourselves, yourselves, themselves, themself,
     oneself, or "my self" spelt apart) within 3 words after; end (-s, -ed, -ing) it all; end
     or take (-s, -ed, -ing, -en, took) with "life" or "lives" within 3 words after and a
     possessive between (my, your, his, her, our, their, own, or any word ending 's); an
     intent or wish (want, going, ready, tempted, urge, plan, try, intend, decide, wish, in
     the forms listed in the code) with die, dies, died or dead within 4 words after; think,
     thinks, thinking, thought or thoughts with "dying" within 4 words after; want (-s, -ed,
     -ing) with a negation (not, never, no longer) within 3 words before and live, alive or
     "be here" within 3 after; reason(s) with no, not or never within 3 words before and
     live, living, alive or "go on" within 4 after; "go on" (go, goes, going, went, gone)
     with a negation within 3 words before and can or could within 4 before; "better off"
     with dead, or without + me / you / him / her / us / them, within 4 words after.
   - *The support flow.* The message is screened before anything else, so every outcome of
     `POST .../interview/turns` carries the panel when the message triggers the screen. An
     accepted send is a 202 as usual (no hold, no extra step) with `support_note`: a calm,
     non-diagnostic panel with the four services and the date they were checked, saying the
     message was sent. A refused send (stale profile version, too long for the prompt,
     over budget, no key, an idempotency key reused, a workspace the caller cannot see, or
     any other refusal the command raises) carries the same panel beside its error
     envelope (`TurnRefusedOut`), saying the message was not sent. The web app shows it
     beside the conversation until dismissed and announces it through the chapter's polite
     live region ("Your message was sent / not sent. Support information is shown above the
     reply field."); focus is not moved (dismissing returns it to the reply field), and the
     question steps aside while it is shown. For that turn only, the interviewer's
     instructions gain a fixed sentence (`SUPPORT_TURN_INSTRUCTION`, prompt
     `interview-turn-4`): acknowledge briefly and kindly, offer one smaller next step such
     as pausing, ask no career question, and give no phone numbers or service names (the
     panel holds the checked ones; spec section 4: never fabricate emergency details). The
     server enforces the question part: on that turn `check_turn` drops any next question
     the model still writes, and spends no repair on it. The model never sees a label naming
     the screen or what matched: the context it reads is the same either way. The demo
     interviewer follows the same instruction.
   - *Never stored.* The panel, the instruction and the dropped question are recomputed
     from the message wherever they are needed (the API response, a replay or a refusal
     included, and every model request and check, a repair included), so the flag reaches
     no profile, proposal, discovery, slate, export, receipt, run, journal or log (tested by
     scanning both databases, the worker log, the API log and the export). The model's
     answer to the instruction is stored like any reply. Receipts stored before fix round 4
     but after `send_after_support` was added (Task 6 rounds 0 to 3) have another
     fingerprint, so replaying one is refused as a key reuse whose reason names an earlier
     request format, never a 500; some may still hold the old note, in pre-release local
     data only. Receipts from before Task 6 had today's request shape and replay normally.
   - *Known limits (H-12):* a finite English list of words and constructions, so wording
     outside it gets nothing ("my friend wants to end things", "what's the point", "I just
     want to end it", "can't carry on", method words), and a construction whose words are
     further apart than its window gets nothing: extending either is the reviewer's
     decision. False positives show the panel, since the screen makes no intent judgement:
     listed words in career, workplace or figurative phrasing trigger it ("took my life
     savings", "ending my life sciences career", "end my working life", "better off without
     me" about a team, "hurt myself lifting", "cut yourself some slack", "I cut costs
     myself", "don't want to live in London", "don't want to be here in five years", "going
     to die of boredom", "can't go on holiday", "the meeting would die"), and some people
     may find that unwelcome. Only the next question is dropped: the model's reply text is
     not checked for a career question. A message is screened only when it reaches the API:
     while sending is unavailable in the web app (paused, no key stored, a reply still on its
     way), nothing is sent, so nothing is screened, and a request the API refuses before
     reading the message (signed out, no idempotency key, a body outside the contract such as
     an empty or over-long message, which the web app does not send) gets no panel.
   - *Inappropriate inference.* Model output may not name a health condition, a diagnosis,
     a personality type (or MBTI code), a protected characteristic or a percentage that the
     person's own messages never used; a condition the person names may be acknowledged,
     to ask which adjustment would help, but is never recorded in a career field. A word the
     person used, singular or plural, may be used. In a discovery search only, a kindred
     word may be too ("mothers", so "maternity work for women"): naming who the work serves
     is not a guess about the person, while in an interview reply it would be. Both are
     validation problems, so the one bounded repair applies.
   - **Provisional, needs reviewed sign-off (R6; H-12):** the wording, the phrase lists and
     the resources. Clinical screening is out of scope; this is not one.

8. **The early requirement sketch** (`GET .../sketch`, STATE-05) resolves each target
   title: first by the occupation the person chose for it (`occupation_choice`, by its
   ESCO URI in the held release), else against ESCO's labels: one occupation gives its
   essential skills (the first six and the count); several give a choice (nothing
   guessed); none gives the nearest occupations and "not researched". About 260 ESCO
   preferred labels are also another occupation's label, so re-matching a chosen title
   would ask the person to choose again forever. Three generic steps (compare, find options, check time and cost)
   are always `unresolved`. It is labelled "Early sketch, not a checked route", names no
   provider, price or date, and lists which minimum inputs are not asked yet.

9. **The live evaluation is its own capped command** (`make live-eval`,
   `tools/live_eval.py`) on the existing usage ledger: the cases marked live (four:
   INT-01..03 and DSC-01; at most 6 per invocation), one synthetic workspace each with a
   run limit of exactly one attempt, the test model only, a per-scope cumulative cap of the
   controller's 9 requests (R5; no production request, $0.05 worst case), so a scope holds
   one default run and a further authorised run gets its own scope
   (`NESSA_LIVE_EVAL_SCOPE`). Every attempt is ledgered after the worker stops, the key is
   leak-scanned, results with failures by type are appended to
   `docs/evidence/live-eval.md` under a header naming the budget scope (runs from fix round
   2 on), and each case's output is kept in the private evidence
   directory (`NESSA_HOME/evidence/live-eval.jsonl`, never committed) so a failure can be
   diagnosed. It is never part of `make check` or `make acceptance`. The counterfactual pair
   (INT-04/05) is not in the default run: one sample per arm cannot separate a demographic
   effect from run-to-run variation, so it compares only the fields the message states
   unambiguously, and a powered comparison (several samples per arm) belongs to the
   release task. The offline evaluation runs the deterministic subjects (support screen,
   output guard, discovery with the fixture proposer over the full release); it certifies
   the pipeline, not the model.

10. **Export format 3** adds the discoveries (with their validated searches; slates are
    recomputed) and the interview preferences.

11. **A decision carries the person's edits; undo is a revert** (Task 6 review). The review
    tray's edited answers go in the turn's one decision (`edits`: a proposed field each,
    not also accepted), checked like a direct edit and saved as direct entries in the same
    version as the accepted proposals, so a failure saves nothing and loses nothing. An edit
    that leaves the proposal as it was is sent as an acceptance and keeps its source.
    `POST .../profile/revert` (`expected_version`, `to_version`) restores an earlier
    version's answers, each citing the source it had (a fixture stays a fixture; a
    confirmed reading keeps its basis and turn), as a new version; undo uses it, never a
    direct edit.

## Consequences

- Migration 0010; new run kind `discovery`; new event kind `interview.preferences_updated`;
  new source kind `occupation_choice`; new endpoints for preferences, discoveries, slates,
  targets, the sketch and the profile revert; `submit_turn` answers 202 with the support
  panel when the message triggers the support screen, and a refusal of such a message
  carries the panel too (`TurnRefusedOut`; fix rounds 4 and 5: no 200 response and no
  `send_after_support` any more); a turn decision may carry edits.
- Not done: model-written suggestion explanations; applying the salary floor (Sprint 3,
  with pay evidence); a salary floor per target; a human review of the evaluation cases
  and of the support policy (H-12).

## Human review checklist (H-12, not run — requires human)

- [ ] **Support policy** (decision 7): the one recall-first screen in place of an intent
  judgement; the normalisation, the listed words, the constructions and their windows
  (`safety.py`; the reported shapes in `test_safety.py::CORPUS`), and whether to add wording
  they miss ("end it", "carry on", "not exist", method words) or widen a window; the
  panel's two wordings (sent, not sent), its placement beside the conversation and beside
  a refusal, its polite announcement and the question stepping aside; the smaller-step
  instruction's wording, the server dropping the next question on that turn, and that the
  reply text is not checked for a career question; the decision to send every message and
  never store the panel or the instruction; the known limits in decision 7: a finite
  English list of words and constructions, false positives that show the panel (career,
  workplace and figurative phrases with a listed word), no intent judgement, and messages
  not screened because they were never sent (paused, no key, a reply on its way) or were
  refused before the message was read; and the four resources and their wording (checked
  against the services' pages on 2026-10-28).
- [ ] **Inference rules** (decision 7): the health, type and protected-characteristic word
  lists, the kindred-word groups (discovery searches only), and refusing a condition in a
  career field.
- [ ] **Slate policy** (decision 5): channel weights, the partial-match weight, the floor
  (and whether an absolute rank floor is needed), the bonuses, quotas, the family limit,
  alias-only folding within a minor group (164 ESCO pairs still fold, for example
  physiotherapist and occupational therapist: are they the same role?) and the family
  round-robin pool.
- [ ] **Interview repair rate** (decision 3): how often the one-question rule costs a paid
  repair, from the release evaluation.
- [ ] **Evaluation cases** (decision 9): the 43 cases and their semantic expectations. Of
  them, 20 (SUP-01..13, GRD-01..07) test deterministic code with canned inputs; the model's
  behaviour rests on the live cases alone, single samples so far.
- [ ] **Counterfactual tolerance** (decision 9): which fields must not change with an
  irrelevant cue, and how many samples per arm the release task's comparison needs.
