# ADR 0007: The You chapter's conversation, grounded discovery and the support policy

- Status: Accepted (Task 6, Sprint 2: S2.3-S2.6; decision 12 and the amendment to decision 6:
  Task 6b, S2.7). Decision 7 (the support policy, redesigned in fix rounds 4 and 5: its word
  lists and windows, its wording and its resources), decision 5's slate weights, folding and
  floor, decision 3's repair-rate tracking and the 43 evaluation cases of decision 9 were
  **accepted for L0 as built by the product owner at session 1** on 2026-10-28
  (`docs/reviews/session-1.md`; H-12, checklist below), and decision 9's powered
  counterfactual comparison was approved to run at release (its pass rule is still open).
  There the product owner also asked for three phrases to be added to the support screen
  (decision 7). Decision 12 and evaluation case EXP-01 were not in session 1's package; the
  product owner accepted them on 2026-10-28 in the chat after it, as five questions put them
  (the session 1 record's "Addendum"). Decision 12's full readiness, pay and hiring word
  lists, its claim and quotation bounds, its full function-word list and the "first view"
  definition were not asked: they stay
  **provisional, need product owner and reviewed sign-off** (ruling R6; H-12). Decision 2's
  salary floor is the product owner's change to the hard-constraint set (H-11, 2026-10-28).
  Decisions 13 and 14 (Task W2 slice W2B, 2026-10-30: the slate joined by shared essential
  skills, and the unexpected connection; fix round 1, 2026-10-31: every other search reaches
  work only through its essential skills; fix round 2, 2026-10-31: a whole phrase in one
  skill, no search on work style alone, no tie cut by the alphabet, a shared title waits for
  the person's choice; fix round 3, 2026-10-31: a search too general to find work alone,
  only a one-word work style left unsearched, no cut inside a tie, the specific answer's work
  first, every answer that found nothing named) amend decision 5 and are **provisional, need
  product owner confirmation at session W2** (R6; its sheet is Task W2D's): the minimum of
  three shared skills, the share-of-both ranking, the best 30, the connection rule, the
  essential-skills search with every word of a phrase in one skill, a one-word work style
  finding no work (to confirm or reverse), the too-general thresholds (more than 50
  occupations, or more than 5 different skills none named exactly by the search's words),
  the order by the reaching search's specificity and then the share of skills, the
  type-ahead's "closest titles" order and its status words, and the prompt's ESCO skill
  wording (`discovery-queries-3`, untested live).
- Date: 2026-10-28
- Requirements: REC1-01..11, DIV1-02, DIV1-04..12, STATE-05, STATE-06, STATE-08, PROF-04,
  PROF-07..09, MODEL-03, MODEL-07, TEST1-10; spec sections 3, 4 and 16; ADR 0006; ADR 0008
  decision 4

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
     enjoys (decision 5); it can only add candidates (REC1-03). Since Task W2B fix round 3 a
     search resting only on one-word answers ("structured") is not run, and a longer answer
     ("working outdoors") is searched like any other (decision 13, provisional for session
     W2), so it can add work and still removes none.
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
     below it. *Amended by Task 7 slice B (2026-10-29):* the floor is now applied as a hard
     filter, on the slate through reviewed official pay and on the job list through
     advertised pay, and `limits_not_applied` is replaced by `salary_floor`, which counts
     what it left out, what met it and why the rest were kept (ADR 0010 decision 8).

3. **One useful question at a time** is the interviewer's job and part of the contract
   (`interview-turn-3`): the question lives only in `next_question`, which holds at most one
   question mark, and beside it the reply holds none (a validation problem, so the one
   repair applies). With no next question there is nothing to repeat, so a "?" in the reply
   costs no repair. The web app shows the reply and the question apart, so it is asked once.
   The evaluation checks each field on its own (`one_question`, which also counts a second
   ask joined to the first in one sentence) and `missing_excludes`, never exact prose; the
   repair rate is for the release evaluation to track, with no target yet (accepted by the
   product owner at session 1, H-12). Earlier turns stay one action away.

4. **Discovery is a run kind on the one activity** (`discovery`; ADR 0002, ADR 0006
   decision 10). The model proposes **searches, never suggestions** (`discovery-queries-1`;
   `discovery-queries-2` since Task W2B fix round 2, decision 13: short phrases in ESCO's
   skill wording, never work style alone; `discovery-queries-3` since fix round 3: never a
   phrase too general to find work alone, and only a one-word work style never alone):
   it reads only the confirmed answers that describe work (current role, targets, the three
   task fields, work style; never places, money, hours or a name) and returns up to 8 short
   ESCO queries, each in one of the spec's channels (tasks, environment, transferable,
   cross-industry, less familiar) and quoting the answers it rests on, plus up to 3
   "surprising but plausible" titles. `check_discovery` refuses a query that quotes
   something the person never said, or that searches by a health condition, personality
   type or protected characteristic the answers do not contain (one bounded repair, as for
   interview turns). Demo workspaces use a deterministic fixture proposer
   (`careerwright-fixture-discovery-1`: each answer as a query, no invented titles); the database
   confines both fixture models to demo workspaces and to these two kinds. A discovery
   pins the profile version it read. Without an answer that describes work it is refused
   (`INSUFFICIENT_EVIDENCE`) before any run exists; without a taxonomy, likewise.

5. **The slate is deterministic code** (`careerwright.profile.slate`), recomputed on each read
   (`GET .../discoveries/{id}/slate`) from the stored searches, the pinned answers and the
   held ESCO release, so it is reproducible without storing a second copy. The searches
   record the release they were chosen for; a slate read against another release says so
   in a note.
   - *Retrieval.* Each query runs twice against ESCO's English full-text index: occupations
     matching every word score their rank over the best such rank; those matching only some
     words score at most half that (any-word search ranks a common word in a title highly).
     Careerwright adds the current role (searched) and the person's own target titles (exact label
     matches). A model title becomes a candidate only if ESCO holds it as a label (DIV1-04);
     otherwise it is listed as an unsupported hypothesis, never suggested. Decision 13
     (Task W2B) replaces this retrieval: titles join other work by shared essential skills,
     every other search reaches work only through one essential skill whose label holds all
     its words, and the any-word search and its half weight are gone.
   - *Pool.* Hits are pooled by concept (an alias is the same concept). An occupation in the
     same ISCO minor group as another, whose preferred label is one of the other's
     non-hidden labels (as a concept key) or that has the same labels, is near-identical to
     it and counts once, the most relevant representing them (DIV1-05). Folding is never
     transitive: a candidate joins a group only through its lead, because ESCO gives many
     distinct occupations a shared label ("geologist", "facility manager"), and chains of
     them once folded quarry engineers with building cleaners. Nor does it cross kinds of
     work: ESCO lists "biochemist" as a chemist, but that is related work, not the same
     role. By an offline count (Python approximation of `careerwright.concept_key` over ESCO
     v1.2.1's preferred and alternative labels), 319 occupation pairs are one alias apart:
     155 across minor groups no longer fold, and 164 within one still do (for example
     physiotherapist and occupational therapist): the product owner confirmed at session 1
     that these are the same role for a slate (H-12). The pool is bounded at 120 (the soft 60-120 target), filled
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
   - **Accepted for L0 as built (product owner, session 1, 2026-10-28; H-12):** every
     weight, quota and floor above. Each is product policy to be evaluated, not an estimate
     of fit. Known limit: ranks are normalised to each query's
     own best hit, so a query's best match clears the floor however weak the query is (an
     any-word match scores at most 0.5). An absolute rank floor needs calibrating on the
     full release; it is not set in L0, and session 1 accepted the floor as built.

6. **A suggestion's words come from facts; a written note may stand beside them (ADR 0008
   decision 4; Task 6b, decision 12).** "Why this could suit you"
   quotes the answers that found it and the search that matched ESCO's record; "What might
   not suit you" names ESCO's essential skills (not yet compared with experience), a
   regulated-profession mark and, when familiarity is known, a different kind of work;
   "Try it before committing" offers an informational interview and one of its tasks on a
   small scale (with people who do the work for a plural ESCO title, "warehouse operators
   for clothing", since Task W2B fix round 4). Entry gates and evidence gaps say plainly what is not researched yet; a
   later absence of listings is a demand signal, not proof the work does not exist
   (DIV1-09). Every suggestion carries its ESCO URI as its source, the release's
   attribution and adaptation are shown with the slate, and it becomes a target only when
   the person chooses it (`POST .../targets`, REC1-07): the one write path, with an
   `occupation_choice` source naming the ESCO URI and the discovery. The same command
   resolves an ambiguous target title to the occupation the person means (`replaces`).
   Since ADR 0008 decision 4 (D3), a model-written "Why this could suit you" may stand
   beside these words, never in their place: decision 12 (Task 6b) records how. These words
   remain the deterministic provenance, shown in every case and cited by exports.

7. **The minimal support policy** (`careerwright.profile.safety`, `support-policy-7`): one
   deterministic, recall-first screen over normalised words (controller rulings, Task 6 fix
   rounds 4 and 5; three phrases added after session 1). It is kept apart from career
   suitability: it scores, labels and remembers nothing. The four UK services were checked
   on their own pages on 2026-10-28 (999 or A&E; NHS 111, mental health option; Samaritans
   116 123; Shout 85258). One hand-written table is the test
   (`tests/domain/test_safety.py::CORPUS`): every shape the reviewers reported in re-reviews
   2 to 4 must trigger the flow, and their career examples with no listed word must not;
   the session 1 rows (source `session1`, the controller's) say which of their messages
   must and must not; each row is also checked inside other text and in capitals. It shows
   that those shapes are caught, not that every possible wording is.
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
     (U+2018, U+2019, U+201B, U+02BB, U+02BC, grave, acute) to `'`; the hyphens U+2010 and
     U+2011 to `-`; the dashes U+2012 to U+2015 and U+2212 to a space; soft hyphens and
     zero-width characters removed; lower case; words split on anything else, a hyphenated
     compound split at its hyphens so each part is a word ("anti-suicide", "die-so"), except
     that "self" stays joined to the part after it ("self-harm", "self-esteem"); windows
     count words after contractions are spelt out ("I'd" is two); contractions spelt out:
     any "n't" to "not"
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
     the forms listed in the code) with die, dies, died or dead within 4 words after; the
     same intent or wish with end (-s, -ed, -ing) followed by "it" within 4 words after
     (session 1: "want to end it"); exist, exists or existed with want or wish (any of
     their forms) and a negation (not, never, no longer) within 4 words before (session 1:
     "want to not exist", "wish I didn't exist", "don't want to exist"; not "existing",
     mostly an adjective in career text; only want and wish here, by the fix round 1
     ruling, so "isn't going to exist" about a job does not trigger it); think, thinks,
     thinking, thought or thoughts with "dying" within 4 words
     after; want (-s, -ed, -ing) with a negation within 3 words before and live, alive or
     "be here" within 3 after; reason(s) with no, not or never within 3 words before and
     live, living, alive, "go on" or "carry on" within 4 after; "go on" (go, goes, going,
     went, gone) or "carry on" (carry, carries, carried, carrying; session 1) with a
     negation within 3 words before and can or could within 4 before; "better off" with
     dead, or without + me / you / him / her / us / them, within 4 words after. Session 1's
     three phrases are constructions, not bare words, because bare "carry on" and "end it"
     are ordinary career wording (controller ruling).
   - *The support flow.* The message is screened before anything else. When it triggers the
     screen, the panel accompanies an accepted send and every refusal the command (or the
     replay of its receipt) raises; it does not accompany an unexpected server failure (a
     database or queue error, answered 500) or a request refused before the message is
     read (see the known limits). An accepted send is a 202 as usual (no hold, no extra step) with `support_note`: a calm,
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
   - *Never stored.* The panel and the instruction are recomputed from the message wherever
     they are needed (the API response, a replay or a refusal included, and every model
     request and check, a repair included), so no flag is stored in a profile, proposal,
     discovery, slate, export, receipt, run, journal or log (tested by scanning both
     databases, the worker log, the API log and the export). The question is dropped once,
     in `check_turn`, and the stored proposal holds `next_question: null`; no field records
     why, and a null question is ordinary. The model's answer to the instruction is stored
     like any reply. Receipts stored before fix round 4
     but after `send_after_support` was added (Task 6 rounds 0 to 3) have another
     fingerprint, so replaying one is refused as a key reuse whose reason names an earlier
     request format, never a 500; some may still hold the old note, in pre-release local
     data only. Receipts from before Task 6 had today's request shape and replay normally.
   - *Known limits (H-12):* a finite English list of words and constructions, so wording
     outside it gets nothing ("my friend wants to end things", "what's the point", method
     words), and a construction whose words are further apart than its window gets
     nothing: extending either is the reviewer's decision. Known gaps of this kind: the
     wish shape "wish that I'd ... die" can fall past the window of 4 words once "I'd" is
     spelt out; the "not exist" construction counts only want and wish, so another listed
     intent word before a negation and "exist" gets nothing (recall given up so that
     predictions about work, such as "that job is not going to exist in ten years", show no
     panel; pinned as must-not-flow rows); and an apostrophe-like character outside the
     mapped list (such as U+2032) or a reflexive spelt apart other than after my / your /
     him / her / our / them / one ("our selves" is not matched; "ourself" and plural
     "selves" after an owner are not listed) is not read. A dash written without
     spaces is read as a space, so "self—esteem" after "my" reads as "my self esteem" and
     triggers. False positives show the panel, since the screen makes no intent judgement:
     listed words in career, workplace or figurative phrasing trigger it ("took my life
     savings", "ending my life sciences career", "end my working life", "better off without
     me" about a team, "hurt myself lifting", "cut yourself some slack", "I cut costs
     myself", "don't want to live in London", "don't want to be here in five years", "going
     to die of boredom", "can't go on holiday", "the meeting would die"). Session 1's
     constructions add their own ("I can't carry on working nights", "I want to end it"
     about a zero-hours contract, "I wish commutes didn't exist"; pinned in `CORPUS` as
     `session1 limit`). Some people may find these panels unwelcome.
     Only the next question is dropped: the model's reply text is
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
   - **Accepted for L0 as built (product owner, session 1, 2026-10-28; H-12):** the
     wording, the word lists, the windows and the resources, and the inference word lists.
     The product owner also asked there for "end it", "carry on" and "not exist". They were
     added after the session as the constructions above (`support-policy-6`; `-7` after fix
     round 1 narrowed "not exist" to want and wish), in a form the
     controller ruled; the product owner has not seen them as built. Clinical screening is
     out of scope; this is not one.

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
   (`CAREERWRIGHT_LIVE_EVAL_SCOPE`). Every attempt is ledgered after the worker stops, the key is
   leak-scanned, results with failures by type are appended to
   `docs/evidence/live-eval.md` under a header naming the budget scope (runs from fix round
   2 on), and each case's output is kept in the private evidence
   directory (`CAREERWRIGHT_HOME/evidence/live-eval.jsonl`, never committed) so a failure can be
   diagnosed. It is never part of `make check` or `make acceptance`. The counterfactual pair
   (INT-04/05) is not in the default run: one sample per arm cannot separate a demographic
   effect from run-to-run variation, so it compares only the fields the message states
   unambiguously, and a powered comparison (several samples per arm) belongs to the
   release task. At session 1 (2026-10-28; H-12) the product owner approved it as the
   package put it: "run the powered comparison at release, estimated at most $0.07 on the
   test model" (Task 16). Derived from the Task 6 report, not asked at the session: about 10
   samples per arm, so at most 40 requests; its own scope with a cap above 9 requests; and
   the fields the pair compares as built (`current_role`, `weekly_study_hours`). Still
   open, and to be decided before Task 16 runs it: the pass rule across several samples per
   arm (how much the arms may differ before it counts as a change). It has not run, and no
   live call was made for it.
   The offline evaluation runs the deterministic subjects (support screen,
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

12. **The written "Why this could suit you" (Task 6b, S2.7; ADR 0008 decision 4; REC1-11).**
    A run kind on the one activity (`slate_explanation`, prompt `slate-explanation-1`,
    migration 0011; ADR 0002, ADR 0006 decision 10), so one bounded call with at most one
    repair, like a discovery.
    - *What a slate is* (ruling). A discovery's first view: balanced emphasis, no
      exclusions, computed when the explanation is asked for. A changed view (emphasis,
      exclusions) is never a new slate and never makes a call: a suggestion it shows that
      the note covers keeps its note, and any other says it has none. A new discovery
      ("Suggest again") is a new slate. `slate_explanations` holds at most one current link
      per discovery (a partial unique index, migration 0012); asking again, from any view or
      with any idempotency key, answers 200 with the same run, whatever its state.
    - *One call per slate, and a failed note* (fix round 1, controller ruling). Whether a
      failed note used up the slate's call is read from its recorded attempts, not its
      failure class: a run none of whose attempts took a reservation or sent a request was
      refused inside the activity (budget, key, access, model) and made no call
      (`can_retry`). Only then does the person's explicit Try again (`retry_failed: true`,
      never sent automatically) start a new run, which replaces the failed link in the same
      locked transaction; the failed run stays in `runs` with its attempts, and concurrent
      tries start one run. A failed run that sent a request (a provider failure,
      `invalid_model_output`, `output_truncated`, or an attempt left unfinished or with an
      unknown charge) stays the slate's one note: Try again is refused
      (`SLATE_ALREADY_EXPLAINED`), and the web app offers Suggest again, saying that it makes
      a new set of suggestions with a note of its own.
    - *When.* The web app asks once, when a slate first shows for the current answers and a
      key is stored (or the workspace is a demo). The API refuses before any run exists when
      the expected version is stale or the discovery's pinned answers are not the current
      ones (`STALE_INPUT_VERSION`: the note would quote answers since changed), when the
      discovery has no validated searches (`PROPOSAL_NOT_AVAILABLE`), when no pinned answer
      is one the note can quote (`INSUFFICIENT_EVIDENCE`, `no_quotable_answer`) or the
      slate is empty (`INSUFFICIENT_EVIDENCE`, `no_suggestions`), when the answers are too
      long for the prompt in bytes (`LIMIT_EXCEEDED`, `answers_too_long`), and for the usual
      reasons any run is refused (no key, over budget, demo runtime).
    - *Input* (SEC-05). The answers the discovery pinned that describe work (decision 4),
      each whole, and ESCO's record of each suggestion: its title, its description cut at a
      word, and its first essential skills (ESCO's order is alphabetical). The record steps
      down (600 characters and 6 skills, then 400/4, 250/3, 150/2, 100/1) until the prompt
      fits 8,500 bytes; the cut record is what the model reads and what quotations are
      checked against. The bound is in bytes, so answers in characters of several bytes
      that leave no step fitting are refused before any run or reservation (above). No
      name, place, money, hours, ID or link is sent. Two requests at
      their bounds reserve $0.0034 on the test model and $0.0495 on the production model,
      so three step attempts fit the default $0.15 run limit.
    - *Output and check* (`check_explanation`). Every suggestion once, with 1-2 distinct
      claims; a claim is 20-240 characters with no quotation marks of its own (the model is
      asked for one sentence; only the length is checked), resting on 1-3 distinct
      quotations, at least one of the person's answers and at least one of that
      occupation's record. Each quotation must be an exact span of its source at word
      boundaries (case, spacing, compatibility forms and apostrophe or dash forms aside; an
      apostrophe inside a word or after an "s" belongs to its word, so "s tools" is no
      phrase of "mechanic's tools" and "students" none of "students' learning", while any
      other is a quotation mark, so "people person" is a phrase of "a 'people person'";
      double quotation marks and closing punctuation are taken off its ends until none
      remain, single quotes only as a matching pair), and that span, folded as it was
      matched, must hold a content word: four letters or more, not one of the function
      words of a standard English stopword list with its contraction stems ("about",
      "being", "could", "should", "with" in fullwidth letters, "and" quote nothing). It is
      stored in the source's own characters, with the answer's field or the record's part.
      Refused: a misquotation, an invented answer, a fact the record lacks (another
      suggestion's record included), readiness, affordability or hiring words, phrasings
      ("in high demand", "an in-demand trade", "high-demand", "well-paying", "strong
      candidate", "already have the experience", "plenty of jobs", "crying out for",
      "sought after", "employers want", "short of staff"; "pay" or "paying" before
      "attention" is a skill, not pay) or a currency sign that the occupation's own record
      does not use (the person's answers
      never unlock one: "ready for a change" is no ground for "ready"), and a health
      condition, type, protected characteristic or percentage that neither the answers nor
      that record name (decision 7's guard; the record's words describe the work, not the
      person). Claims and quotations past their bounds are counted, not checked, a model's
      text is echoed at most 60 characters, and the repair message is capped at 800 bytes
      (then "and N more problems"), so the repair fits its reserved 1,000 tokens with the
      agent's fence. One repair, then `invalid_model_output`; a cut-off response is
      `output_truncated` at once; nothing is stored as checked.
    - *Models* (MODEL-02, as for every run). The Standard production model for
      non-synthetic workspaces, the test model for synthetic ones; demo workspaces use the
      deterministic fixture explainer (`careerwright-fixture-explainer-1`, each claim labelled
      "Demo explainer (synthetic)"), which the database confines to demo workspaces and, with
      the other fixture models, to interview turns, discoveries and explanations. It reads
      each quotation back as the check reads it (`accepted_quotation`) before writing it,
      quoting a description's word as its whole token where the word alone is no span
      ("children's"), and quotes only answers the check accepts as quotations of
      themselves. Until the session 1 transcription, the API's pre-check read answers
      differently (any content word), so an answer set made only of single-quoted phrases
      ending in "s" ("'odd jobs'", straight or curly) passed it, and the demo note then
      failed its check (a live run would have spent a paid repair). The pre-check now uses
      the same function, so an answer is "one the note can quote" in exactly the
      explainer's sense. Every ESCO v1.2.1 title is a quotation of itself (an offline count
      over all 3,043), so its last fallback, the title, is always accepted too. For every
      slate the API lets it explain, then, each quotation it writes is one the check
      accepts, by construction (a property test, fix round 3, widened to single-quoted
      words by the session 1 transcription).
    - *Never a change.* The slate is computed without reading the note, and choosing a
      target records the `occupation_choice` source (ESCO URI and discovery) as before,
      never the note. The command answers with the run only (`ExplanationRunOut`): a
      command's answer is kept as its receipt, and model output stays sealed, so the text is
      read with the discovery (`DiscoveryOut.explanation`). Export format 4 carries it beside
      the provenance, which is what exports cite.
    - *UI.* "Why this could suit you" shows the note (each claim, then each quotation after
      "You said" or the part of ESCO's record), says who wrote it and that only the quoted
      words were checked against the answers and ESCO's record, the sentences being the
      writer's own, and then "How Careerwright found it" (decision 6's words), shown in every case.
      Pending, unavailable and not-covered states say so; a polite status line announces the
      change. An unavailable note shows, once above the cards, words from `vocabulary.ts` and
      the one action that can work: Try again for a run that reached no model or a refusal
      that may pass next time (budget, key, the service); Suggest again (it says it makes a
      new set of suggestions) once the slate has had its call, or when the discovery has no
      searches or the answers changed since; and, for a refusal that asking again would
      only repeat (no answer to quote, answers too long, no suggestions), its own reason and
      "Edit answers directly", after which the chapter offers Suggest again. Never a Try
      again that cannot succeed.
    - *The support screen* (decision 7) is neither read nor written: the note sees only the
      pinned answers and ESCO, and an answer holding a listed word is quoted like any other.
    - *Known limits.* The claim's prose is model prose: only its quoted words are checked,
      so a sentence may still say, in other words, more than its quotations support (no
      claim-to-quotation word check is made: it would turn paraphrase into paid repairs);
      the word screens catch the listed readiness, money, hiring and sensitive terms only.
      A short answer with no content word ("art") cannot be quoted on its own. Known false
      positives for the H-12 review: "employers want" or "employers need" is refused even
      where the occupation's work is employers' needs (a careers adviser "explains what
      employers need"), unless that record itself uses the phrase; a closing quotation mark
      after a word ending in "s" ("'odd jobs'") reads as a plural possessive. An answer set
      made only of such phrases is therefore refused before any run (`no_quotable_answer`),
      although a quotation that drops the opening mark and keeps the closing one ("odd
      jobs'") would verify; a model would rarely write one. The web app titles that refusal
      "Your answers can't be quoted on their own", which holds for both causes (fix round
      1). The live evidence is single samples on the test model.
    - **Accepted by the product owner (2026-10-28, the session 1 record's "Addendum";
      H-12):** blocking readiness, pay and hiring claims unless the job's own record uses
      the word, as answer 3 put it: the rule, with its examples ("qualified", "well-paid",
      "in demand", "employers need") and the "employers need" false alarm; the content-word
      rule as asked (a one-word answer such as "art" is not quotable alone), a claim quoting
      both the person and the record, asking for the note without a click, and Try again
      only for a run that reached no model. **Still provisional (R6, H-12), not asked:** the
      full readiness, pay and hiring word lists and phrasings, the claim and quotation
      bounds, the full function-word list and the "first view" definition of a slate.

13. **Titles join work by shared essential skills, never by their words** (Task W2 slice W2B;
    plan section 4, Sprint W SW.5; ADR 0014). At session 2 the product owner judged the slate
    for "data analyst" "arbitrary matching on keywords": the current role was searched as
    text, so any occupation with "data" or "analyst" in its labels, skills or description
    qualified (call centre analyst, data entry clerk, data protection officer, material stress
    analyst), and the demo's query proposer searched target titles too ("Bookkeeping
    assistant" found shop assistant and assistant lecturer). This amends decision 5's
    retrieval:
    - *A title of the person's own* (their current or last role, a target, or a search that
      is one of them as a concept: `careerwright.concept_key`, so "Data analysts" is their
      "data analyst") is resolved to ESCO occupations, never searched:
      `careerwright.profile.titles` takes the occupation the person chose for it (an
      `occupation_choice` source, by ESCO URI; the role keeps the title the person picked,
      ESCO's or another ESCO lists for that occupation), else every occupation holding it as a
      label (`careerwright.concept_key`; several is ambiguous and all are kept, none picked).
      A title ESCO does not hold joins nothing: the slate lists it (`unmatched_titles`) and,
      when it is short, says "Careerwright couldn't match “...” to an occupation in ESCO ...
      Choose the ESCO occupation closest to it" (fix round 5: it said "isn't a title ESCO
      lists", a claim about ESCO, though the match folds case, punctuation and plurals). A
      title several occupations hold joins nothing either (fix round 2): joined
      over their skills together, the count it stated could be true of neither ("bus
      operator": the taxi driver's "14 of the same essential skills for both", when it shares
      13 with the bus driver and 9 with the trolley bus driver; ESCO has 1,051 such titles).
      The slate lists it (`ambiguous_titles`) and, when it is short, says "Careerwright
      matched “bus operator” to 2 occupations in ESCO ... until you choose which one you
      mean", as the first slate already asks (DSC-16; fix round 5: it said ESCO lists it "as
      the title of 2 occupations"). Its occupations are still the person's own close
      candidates. The first question's type-ahead offers those closest titles: when no ESCO
      title holds every word typed (two to eight words; 97% of ESCO's titles have at most
      eight), the occupations whose titles hold the most of them, marked `partial` for
      "Careerwright couldn't match that title in ESCO. Is it one of these?" (Task W2C: it
      said "ESCO doesn't list that title", untrue for a title typed with "and" that ESCO writes
      with "&", or without its accent); the person chooses, and nothing is
      joined by the words. Order (fix round 2): titles holding more of the words whole come
      first ("nurse" before "nursery"), then rarer words ("bookkeeping" before "assistant",
      so P05 sees the bookkeeper first), and a status word ("registered", "senior",
      "junior", "trainee", "qualified", "chartered", "certified", "licensed") is not counted,
      so P04's "Registered nurse" offers the nurse assistant, specialist nurse, veterinary
      nurse, advanced nurse practitioner and nurse responsible for general care first
      (before: a registered sales assistant and a dental hygienist, and six "nursery"
      titles).
      The current role's old fallback (its top full-text hit taken as the person's kind of
      work) is gone: nothing is guessed from a title's words.
    - *The skill join* (`skill_join_hits`): an occupation joins a title only when ESCO lists
      at least three of the same essential skills for both (`MIN_SHARED_SKILLS`). Why three:
      ESCO v1.2.1 lists 3 to 99 essential skills per occupation (22 on average), so three is
      the most every occupation could meet. With one shared skill the median occupation
      joins 337 others and with two 105, which a single skill unrelated work also lists can
      do (54 skills are each essential to more than 100 occupations); with three it joins 45,
      still enough to fill the join's best 30, and 50 of 3,039 occupations join none; with
      four, 142 join none. Hits score their share of both roles' essential skills (Jaccard) over the
      join's best, as a search's ranks are over its best, so decision 5's relative floor and
      relevance apply unchanged; the best 30 are kept (`JOIN_HITS`), and since fix round 3
      every occupation tied with the 30th too (equal share and equal shared count: the
      warehouse manager's places 23 to 47 tie, and the cut kept 8 of them by concept ID). The
      slate says what a join keeps ("Careerwright found 47 other occupations in ESCO that
      share 3 or more essential skills with “data analyst”, and keeps the 30 with the largest
      share of essential skills in common."; fix round 4: it said "the 30 that share the
      most", untrue by count, since P03's join keeps a live chat operator sharing 5 and leaves
      out a ticket issuing clerk sharing 7; fix round 5: it says what Careerwright found, and
      so does the first slate's "Careerwright found no other occupation in ESCO that shares 3
      or more essential skills with ..."), and the ones it leaves out are counted (`beyond_pool_limit`). Careerwright adds the
      role's join itself (channel `shared_skills`, query `j1`, a transferable channel); a
      model or fixture search naming the title is answered by the same join under its own
      channel. Direction follows decision 5: close in the role's or a target's kind of work,
      transferable elsewhere. The role's own occupation stays a close candidate of a
      discovery, as before. Its words: "Your current role: “data analyst”. ESCO lists 12 of
      the same essential skills for both, so Careerwright joined them by those skills."
    - *Every other search reaches work only through one essential skill holding all its
      words* (fix rounds 1 and 2): what the person enjoys, can do or has done (the task,
      environment, transferable, cross-industry and less-familiar channels) search the
      preferred labels of ESCO's skills alone (`skills.search_vector`, migration 0032) and
      reach an occupation only through a skill it lists as essential. No occupation title,
      hidden label, ISCO group label or description is searched (fix round 1's finding:
      hidden labels and the ISCO group's title still matched title words, and descriptions
      matched "structured" to "structures"). Fix round 2: the product owner had rejected
      "arbitrary matching on keywords", and the slates still read that way, so three rules
      make each suggestion defensible to a person, even at the cost of fewer suggestions
      (each provisional, for session W2):
      1. *Whole phrase, one skill.* A search reaches a skill only when that one skill's label
         holds every content word of it (English stems, stop words dropped; no search
         operator, not even "or", turns it into an any-word search). A hyphen in the search
         is read as a space (Task W2C): PostgreSQL's English parser kept "first-aid" whole
         beside "first" and "aid" (`'first-aid' & 'first' & 'aid'`), so no skill named with
         "first aid" held it and "first-aid" found no work; a hyphenated skill name keeps its
         parts too, so nothing it reached is lost. Thresholds and ranking are unchanged. One
         precision: a hyphenated skill name typed with its hyphen ("use e-learning
         platforms") no longer counts as named by exactly the search's words, because its
         vector keeps the whole hyphenated word the search now drops; that flag only exempts
         a search from being too general, and the W2C review's rough offline scan of the
         release's hyphenated essential skill names found no search it turns too general
         (Task W2C fix round 1).
         The
         any-word pass and
         decision 5's partial-match weight are gone: one shared word ("people", "give",
         "write") found an animal behaviourist and a secretary for "looking after people",
         an aesthetician and an air force officer for "giving injections", and an
         aquaculture mooring manager for "writing stories".
      2. *A one-word answer about how someone likes to work does not find work.* Fix round
         2 stopped every search resting on work style alone; before, P01's "structured"
         found soil structure, wood elements in structures and advertising structures. That
         also stopped where someone likes to work, which ESCO does list as part of the work
         ("working outdoors": "work in outdoor conditions"), and its note said the answer
         was not about the work. Since fix round 3 only a search or title idea resting on
         one-word work-style answers alone ("structured", "collaborative", "practical") is
         not run; a longer answer is searched under rules 1 and 4 like any other (environment
         channel, weight 0.6). The slate says so in words that never call an answer not
         about the work: "How you like to work (“structured”, “collaborative”) isn't searched
         on its own, because a single word matches too loosely. Careerwright searches a
         longer answer, such as “working outdoors”." No setting or flag: session W2 confirms
         or reverses it. A search resting on a task and a work style together still runs.
      3. *Ties are never cut by the alphabet.* Every occupation reached through the same
         skill ties on its rank. A search keeps every occupation it reaches up to the pool's
         bound (120; before, its first 30 by title) and, since fix round 3, every occupation
         tied with the last (`FETCH FIRST ... WITH TIES`; "writing reports" kept 2 of the 9
         tied at the 120th place by title, and now keeps all 9). Equal scores go first, since
         fix round 3, to work a more specific search
         found (the search that reached it itself reached fewer occupations: the bicycle
         mechanic, the only occupation "repairing bicycles" reaches, before the 12 that
         "working outdoors" reaches; `Candidate.reach`), then to the occupation whose
         essential skills the person's answers reach the larger share of (the skill is a
         bigger part of that work; `Candidate.share`), the title only last, in the search,
         the pool and the slate. "Planning shifts" reached 58 occupations through "plan
         shifts of employees"; the first 30 by title were kept, so the warehouse worker,
         which "stacking goods" also reaches, never met it.
      4. *A search too general to find work on its own finds none* (fix round 3). Rule 1
         was not enough: a short, common phrase still reaches dozens or hundreds of
         occupations through skills that add a domain to it, and the variety bonus spread
         the six across unrelated work ("writing reports": an emergency ambulance driver
         through "write reports on emergency cases", a chiropractor, a city councillor, an
         aquaculture mooring manager). A search that reaches more than 50 occupations
         (`TOO_GENERAL_OCCUPATIONS`), or more than 5 different essential skills
         (`TOO_GENERAL_SKILLS`) none of which is named by exactly its words (stems and stop
         words aside: "selling products" is exactly "sell products"), only adds weight to
         work another search or join found: decision 5's 0.2 for a further query, never its
         own score (so it never lifts a weak match over the floor), on every such
         occupation it reaches, past its own cut too (it is searched again among them:
         "writing reports" kept its best 127, which leave out the nursery school head
         teacher that "caring for children" also reaches; DSC-19). The slate says so, in
         what the search did: "“Writing reports” reached 217 occupations in ESCO through the
         main names of their essential skills, too many to choose from on its own. Say more
         about it, such as what it's about or who it's for." and "“Training staff” matched
         the main names of 10 different essential skills in ESCO, none of them just those
         words, ..." (fix round 4: both count essential skills only; fix round 5: they said
         "is part of the essential skills of 217 occupations" and "is part of 10 different
         essential skills in ESCO, none of them just that", claims about ESCO that a skill's
         other names can make untrue, since a search reads main names only). Where a model
         wrote the search, it is the search that was too general,
         so the person is never asked to say more about their answer: "The search “write
         reports” (from “writing inspection reports for bridges”) reached 217 occupations in
         ESCO through the main names of their essential skills, too many to choose from on
         its own. Careerwright would need a narrower search to find work from “writing
         inspection reports for bridges”." Since fix round 5 that last sentence is said only
         of an answer no other search found work from: where "write inspection reports", from
         the same answer, found work, it is left out. The web marks such a
         search under "Found by these searches" ("too general to find work on its own, so it
         only added weight to what another search found") and leaves it out of "found by N
         searches of ESCO" (fix round 4), as it does a search that reached nothing (fix round
         5). The same reasoning as the join's
         three shared skills: one shared skill joins the median occupation to 337 others.
         Both thresholds are provisional, for the product owner at session W2. On the
         release they stop "solving problems" (77), "writing reports" (217), "working in a
         team" (242), "analysing data" (92), "training staff" (10 skills), the one-word
         "driving" (71), "cleaning" (191) and "drawing" (317), "planning shifts" (58),
         "managing budgets" (212) and "maintaining equipment" (242); they keep "handling
         complaints" (47, 2 skills), "stocking shelves" (44), "caring for children" (16),
         "caring for animals" (13, 5 skills), "working outdoors" (12), "selling products"
         (12, 8 skills, one exact) and "leading a team" (19, 4 skills). Since 50 is below the
         pool's bound, a search that can find work keeps everything it reaches.
      Each suggestion names the skill, and only one that reached it itself: a near-identical
      role folded into it (decision 5) adds to its relevance but never lends it a skill
      (fix round 2: the sound designer said ESCO lists "attend music recording sessions" for
      it, which ESCO lists for the sound editor; DSC-17). "What you enjoy: “working
      outdoors”. Careerwright searched for “working outdoors”, and ESCO lists “work in
      outdoor conditions” as an essential skill for this work." The discovery prompt
      (`discovery-queries-3`) asks the model for short phrases in ESCO's skill wording
      ("stack goods", "repair bicycles", "care for children"; fix round 3 dropped "plan
      shifts", now too general), since a paraphrase ESCO does not use ("look after
      children") finds nothing, and for what a common phrase is about ("write inspection
      reports", not "write reports"); it is untested live (R5). Evaluation:
      `searched_through_skills` needs every content word of the search in the named skill,
      one of the suggestion's own essential skills; `work_style_not_searched`,
      `general_searches_add_only`, `titles_ambiguous` and `small_pool_has_reason` check
      rules 2 and 4, a shared title and the soft pool. The public taxonomy search is
      unchanged. Known limit, for session W2: a one-word task answer reaching few enough
      occupations still matches on its stem (rule 4 stops "driving", 71 occupations).
    - *Honest emptiness* (fix rounds 2 to 5): an answer whose every search found nothing
      is named, on full and short slates: "No main name of a skill ESCO lists as essential
      holds all the words of “repairing physical objects”, so it found no work." Where the
      searches were not the answer's own words (a model's), the note names them: "“Fixing
      things” found no work: no main name of a skill ESCO lists as essential holds all the
      words of its search “repair machinery”." A search of only common words reads nothing
      ("“All of it” has only common words, which Careerwright doesn't search for, so it found
      no work."), and a model's search naming the person's own title is answered by its join
      ("Careerwright found no other occupation in ESCO that shares 3 or more essential
      skills with its search “warehouse manager”, your own title"). Fix round 5, the
      controller's ruling: a note says what the search did, never what ESCO contains. Three
      rounds found such a claim untrue: "isn't how ESCO names any skill" where ESCO names the
      skill but lists it as essential for no occupation ("taking pictures": "take pictures",
      optional for two; 2,561 of the 13,939 skills in the release's skills file are essential
      for none; fix round 4), then "isn't part of any skill ESCO lists as essential" where
      the words are another name of an essential skill, since a search reads main names
      only ("operating farm machinery" is ESCO's other name for "operate agricultural
      machinery", essential for 8 occupations; `tests/integration/test_evaluation.py`). An
      answer several searches rest on is named only when none of them found anything. The
      person's own titles keep their own reasons, and a one-word work style its own note,
      a model's search resting on it beside a task included (fix round 4; before, such a
      search that found nothing named "practical" as having found no work). With nothing to
      suggest, the slate says "None of your answers found work to suggest yet." (before:
      "None of your answers matched an occupation in ESCO yet.", which a too general answer
      made untrue). Check: `missed_answers_named` (DSC-01, DSC-03, DSC-07, DSC-18), which
      leaves one-word work styles to their own note and, since fix round 5, faults one named
      as having found no work.
    - *The soft pool* (fix round 2): the 60-120 working pool holds only where evidence
      permits (DIV1-02). A full slate chosen from fewer than 60 says so: "Careerwright chose
      these from 12 occupations that match your answers closely. It aims for at least 60,
      but doesn't add weaker matches to get there." A short slate already says why it is
      short. Since fix round 3 `beyond_pool_limit` counts, once each, what a join reached past
      its best 30 and what the pool's bound left out (before: only the bound's, so "data
      analyst" said nothing of the 17 its join left out), and the web says "17 more were
      found but not kept". Full-release tests exercise the bound (four searches reaching
      178), the ties at both cuts and the too-general answers.
    - *Checked on the full release* (offline evaluation, fixture proposer; DSC-01 to
      DSC-19, `tests/integration/test_evaluation.py`): "data analyst" gives data scientist
      (22 shared), chief data officer (7), big data archive librarian (7), data quality
      specialist (12), data entry clerk (5) and knowledge engineer (7), and the same when a
      model searches "Data analysts" (DSC-15). P03's "IT support technician" is ESCO's ICT
      help desk agent and joins after-sales service technician, call centre agent, ICT help
      desk manager, customer service representative and specialised seller. P04
      ("Registered nurse"), P05 ("Bookkeeping assistant") and P01's "Data quality analyst"
      are not ESCO titles: nothing joins them, and the slate says so. P01's tasks
      ("finding inconsistencies", "explaining evidence") are in no single skill's label and
      its work style is not searched, so its slate is empty with both reasons; choosing the
      closest ESCO title, the data quality specialist, gives DSC-02's skill-joined slate
      (fix round 1: dental practitioner, ICT information and knowledge manager, advertising
      installer, agronomic crop production team leader, artistic coach, carpenter). P02's
      "repairing physical objects" is in no skill's label, "practical" is one word and "small
      team" (searched since fix round 3) finds nothing, so all six come through "work in
      outdoor conditions", from 12 occupations: leaflet distributor, deep-sea fishery
      worker, pesticides sprayer, fisheries observer, fruit and vegetable picker, offshore
      renewable energy plant operator; the slate names "repairing physical objects" and
      "small team" as having found no work. "Looking after people" finds nothing, and says
      so; since fix round 3 DSC-07 and DSC-08 use "caring for animals" (13 occupations), so
      their pair checks something. "Caring for patients" finds the advanced nurse
      practitioner, specialist nurse and nurse responsible for general care, and the slate
      names "giving injections" as having found nothing (DSC-18); "designing websites" the
      web designer, webmaster and web developer; "teaching children, writing stories"
      nothing. "Caring for children, writing reports" (DSC-19): six from the 16 that
      "caring for children" reaches, "writing reports" named as too general. DSC-03's role
      became "warehouse supervisor" (an ESCO alternative label) in fix round 1: "Warehouse
      shift supervisor" is not one, so it joins nothing.

14. **The unexpected connection** (plan section 4, the Roles chapter's moment). A
    deterministic rule over a slate (`unexpected_connection`): of the suggestions the
    person's role joined by shared essential skills, outside the role's own kind of work
    (ISCO-08 minor group) and never a title the person named, the one sharing the most
    essential skills with the role; ties go to the larger share of both roles' skills, then
    to the slate's order. No such suggestion, no connection (a revelation with no source is
    not shown). Only a role that names exactly one ESCO occupation has a connection (fix
    round 1): a title several occupations hold ("bus operator") is no single occupation to
    state a fact about, and since fix round 2 it joins nothing until the person chooses
    which they mean (decision 13; DSC-16). Only the suggestion's own join counts, never a
    near-identical role's folded into it. Why this rule: "unexpected" is the plan's "a destination the person never
    named ... joined to their own role": another kind of work, never one they named; and the
    most shared skills makes the revelation the most substantial fact the slate holds, which
    its sentence states. It is a fact about two roles, never about the person: "A data
    analyst and a chief data officer share 7 essential skills." (a plural ESCO title takes no
    article since fix round 3: "A warehouse manager and warehouse operators for clothing
    share 6 essential skills."), with the seven skills one
    step away and "These are the skills ESCO lists for both roles. They aren't compared with
    your own experience yet." It is served with a discovery's slate (`SlateOut.connection`)
    and the origin's first slate (`GET .../origin`), which is the role's skill join alone
    (the role is the origin, never a destination), recomputed on each read with no model
    call: on the full release the first answer's response took 19 ms to save and 24 ms to
    read (`tests/integration/test_first_answer.py`); fix round 1 timed the heaviest roles
    too, the clinical psychologist (99 essential skills) and the spa manager (joined to the
    most occupations, 305), each under 60 ms to save and read, and single letters typed
    ("a", "s", "c", "d") under 60 ms.

## Consequences

- Task W2 slice W2B (decisions 13 and 14): `SlateOut` gains `unmatched_titles` and
  `connection`, slate channel `shared_skills`; `GET /v1/taxonomy/titles` (the first
  question's type-ahead over preferred and alternative labels), `GET .../origin` and
  `POST .../origin/role` (the first answer, an `occupation_choice` source on the current
  role); migration 0031's label-words index. Fix round 1: migration 0032
  (`skills.search_vector`, generated from each skill's preferred label, so the held release
  is filled by the migration and later imports as they write); `TitleMatchesOut.partial`;
  `ChooseRole.label` (the title the person picked); evaluation cases DSC-15 and DSC-16 and
  the checks `searched_through_skills` and `no_connection`. Fix round 2: `SlateOut` gains
  `ambiguous_titles`, and its `notes` also say when answers were not used to find work or
  the pool is below its soft target; prompt `discovery-queries-2`; evaluation case DSC-17
  and the checks `work_style_not_searched`, `titles_ambiguous` and
  `small_pool_has_reason`; DSC-12's `size_at_least` became `fewer_has_reason`, and DSC-16's
  `joined_by_skills` became `titles_ambiguous`. No migration. Fix round 3: `PoolQueryOut`
  gains `reach` and `too_general`; `beyond_pool_limit` also counts what a join reached
  past its best 30 (the web: "N more were found but not kept"); `notes` name the answers
  that found no work, the searches too general to find work alone and what a join keeps;
  the empty slate's reason is "None of your answers found work to suggest yet."; prompt
  `discovery-queries-3`; evaluation cases DSC-18 and DSC-19 and the checks
  `missed_answers_named` and `general_searches_add_only`; `work_style_not_searched` checks
  one-word answers only, and DSC-07 dropped it (its work style is now searched) for
  `missed_answers_named`; DSC-07 and DSC-08 search "caring for animals". No migration. Fix
  round 4 (words, labels and tests; no API or matching change): the missed, too-general and
  join notes say what was checked and kept; a model's too-general search points at the
  search; a one-word work style a model searched beside a task keeps its own note, and
  `missed_answers_named` leaves it to that note; the web marks a too-general search and
  doesn't count it as finding work; a plural title's "Try it" talks to people who do it.
  Fix round 5 (words, the web count and tests; no API or matching change): every slate note
  and reason says what Careerwright's search, match or join did, never what ESCO contains
  (the missed, too-general and join notes, the first slate's empty join, a title it couldn't
  match or matched to several occupations, and a person's own title in "Why this could suit
  you": "Careerwright matched it to this occupation in ESCO"); a model's too-general search
  asks for a narrower one only from an answer no other search found work from; the web
  counts only searches that reached work and says "couldn't match to an occupation in ESCO"
  of a title Careerwright thought of; `missed_answers_named` faults a one-word work style
  named as having found no work.
- Migration 0010; new run kind `discovery`; new event kind `interview.preferences_updated`;
  new source kind `occupation_choice`; new endpoints for preferences, discoveries, slates,
  targets, the sketch and the profile revert; `submit_turn` answers 202 with the support
  panel when the message triggers the support screen, and a refusal of such a message
  carries the panel too (`TurnRefusedOut`; fix rounds 4 and 5: no 200 response and no
  `send_after_support` any more); a turn decision may carry edits.
- Task 6b (decision 12): migration 0011; new run kind `slate_explanation` and fixture model
  `careerwright-fixture-explainer-1`; `POST .../discoveries/{id}/explanation`; `DiscoveryOut`
  gains `explanation`; export format 4. Fix round 1: migration 0012 (a replaced link, one
  current link per discovery), `retry_failed` and `can_retry`, error code
  `SLATE_ALREADY_EXPLAINED` (409).
- Not done: applying the salary floor (done in Task 7 slice B: a hard filter on the slate
  and the job listing, with counts, ADR 0010 decision 8); a salary floor per target; a human review of decision 12's full readiness, pay and hiring word lists, claim
  and quotation bounds, function-word list and "first view" definition (H-12; not asked at
  session 1 or in its addendum).

## Human review checklist (H-12, session 1: held by the product owner on 2026-10-28)

Agents applied each item below as recorded. At session 1 the product owner answered an
agent-prepared package (`docs/reviews/session-1.md`, Part B; their answers are the record,
rulings R2 and R10) and accepted the ticked items for L0 as built, each as the package line
cited beside it puts it. The package was drafted before Task 6b added the written
explanation (decision 12) and evaluation case EXP-01. Both were asked in the chat after the
package, on 2026-10-28 (the session 1 record's "Addendum"); what those questions did not
cover stays open: not run — requires human.

- [x] **Support policy** (decision 7): the one recall-first screen in place of an intent
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
  refused before the message was read; an unexpected server failure, which carries no
  panel; the window-of-4 wish shape and the rare apostrophe characters and spelt-apart
  reflexives the screen does not read; and the four resources and their wording (checked
  against the services' pages on 2026-10-28). **Accepted for L0 as built** by the product
  owner on 2026-10-28 (session 1, Part B line 1). They also answered yes to adding "end it",
  "carry on" and "not exist", which were added after the session (decision 7).
- [x] **Inference rules** (decision 7): the health, type and protected-characteristic word
  lists, the kindred-word groups (discovery searches only), and refusing a condition in a
  career field. **Accepted for L0 as built** by the product owner on 2026-10-28 (session 1,
  Part B line 2: the current word lists).
- [x] **Slate policy** (decision 5): channel weights, the partial-match weight, the floor
  (and whether an absolute rank floor is needed), the bonuses, quotas, the family limit,
  alias-only folding within a minor group (164 ESCO pairs still fold, for example
  physiotherapist and occupational therapist: are they the same role?) and the family
  round-robin pool. **Accepted for L0 as built** by the product owner on 2026-10-28
  (session 1, Part B line 3): the weights, quotas, family limit and relevance floor as
  built, so no absolute rank floor in L0; the 164 within-group pairs are the same role for
  a slate and keep folding.
- [x] **Interview repair rate** (decision 3): how often the one-question rule costs a paid
  repair, from the release evaluation. **Accepted** by the product owner on 2026-10-28
  (session 1, Part B line 4): tracking only, at release, no target yet.
- [x] **Written explanation** (decision 12): **Accepted** by the product owner on
  2026-10-28, asked in the chat after the package (`docs/reviews/session-1.md`, "Addendum",
  answers 1-5), as those questions put it: asking for the note automatically when
  suggestions first appear, one paid call per set, the test model for synthetic data and
  the production model otherwise (answer 1); every sentence quoting both the person and the
  job's official record, and a one-word answer such as "art" not quotable on its own
  (answer 2); readiness, pay and hiring claims blocked unless the job's own record uses the
  word, with the known false alarm "employers need" (answer 3); Try again only if no paid
  call was made, Suggest again otherwise (answer 4); the note above "How Careerwright found it",
  saying only the quoted words were checked, and evaluation case EXP-01 as written
  (answer 5).
- [ ] **Not covered by the addendum's answers** (decisions 12 and 7): the full readiness,
  pay and hiring word lists and phrasings (answer 3 accepted the rule with its examples),
  the claim and quotation bounds (counts and lengths), the full function-word list, the
  "first view" definition of a slate, and the support screen's three phrasings as built
  ("end it", "carry on", "not exist", added after session 1). Not asked: not run — requires
  human.
- [x] **Evaluation cases** (decision 9): the 43 cases from before Task 6b and their
  semantic expectations. Of them, 20 (SUP-01..13, GRD-01..07) test deterministic code with
  canned inputs; the model's behaviour rests on the live cases alone, single samples so
  far. **Accepted for L0** by the product owner on 2026-10-28 (session 1, Part B line 5).
  EXP-01 was accepted as written in the addendum (Written explanation, answer 5).
- [x] **Counterfactual comparison run** (decision 9): **Approved** by the product owner on
  2026-10-28 (session 1, Part B line 6): "run the powered comparison at release, estimated
  at most $0.07 on the test model" (Task 16).
- [ ] **Counterfactual tolerance** (decision 9): the pass rule across several samples per
  arm, and which fields must not change with an irrelevant cue. Not asked at session 1; to
  be decided before Task 16 runs the comparison. Derived from the Task 6 report, not asked
  at the session: about 10 samples per arm, at most 40 requests, its own scope above the
  9-request cap, and INT-04/05's fields as built (`current_role`, `weekly_study_hours`).
  Not run — requires human.
