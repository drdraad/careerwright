# ADR 0007: The You chapter's conversation, grounded discovery and the support policy

- Status: Accepted (Task 6, Sprint 2: S2.3-S2.6). Decision 7 (the support policy, its phrase
  lists and its resources) and decision 5's slate weights are **provisional, need product
  owner and reviewed sign-off** (ruling R6; human gate H-12). Decision 2's salary floor is
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
   person is asked about tasks before any career is named. Pause is honoured by the web app
   (nothing is asked; the composer gives way to Resume); the API does not refuse a message
   while paused, because the person can only send one by resuming.

2. **Profile schema 3** adds two fields; older documents read them as not asked.
   - `work_style`: how the person says they like to work, a list of their own phrases. It
     is the spec's optional "work style" layer: never forced, never a personality type, and
     never a limit. Discovery searches with it and weighs it below what the person does or
     enjoys (decision 5); it can only add candidates (REC1-03).
   - `minimum_salary`: the lowest gross pay the person will accept, with its period (`year`
     unless they say otherwise; `month`, `week` or `hour` as given; never annualised, spec
     section 5). It is a **hard constraint** (the product owner's change to ADR 0006 decision
     6): the interview may propose it, only explicit confirmation establishes it, and
     Unknown, Skipped and Prefer not to say are answers, never 0. Until regional pay
     evidence exists (Sprint 3), nothing can apply it: the slate says so in
     `limits_not_applied` and removes nothing for pay, and unknown pay is never treated as
     below it.

3. **One useful question at a time** is the interviewer's job (its instructions: one
   question, never ask again for what the profile holds) and is checked semantically by the
   evaluation (`one_question`, `missing_excludes`), never by exact prose. The web app shows
   only the latest question; earlier turns stay one action away.

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
   held ESCO release, so it is reproducible without storing a second copy.
   - *Retrieval.* Each query runs twice against ESCO's English full-text index: occupations
     matching every word score their rank over the best such rank; those matching only some
     words score at most half that (any-word search ranks a common word in a title highly).
     Nessa adds the current role (searched) and the person's own target titles (exact label
     matches). A model title becomes a candidate only if ESCO holds it as a label (DIV1-04);
     otherwise it is listed as an unsupported hypothesis, never suggested.
   - *Pool.* Hits are pooled by concept (an alias is the same concept); occupations sharing
     any non-hidden label (as a concept key) are near-identical and count once, the most
     relevant representing them (DIV1-05). The pool is bounded at 120 (the soft 60-120
     target), and the excess is counted.
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
     be evaluated, not an estimate of fit.

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

7. **The minimal support policy** (`nessa.profile.safety`, `support-policy-1`).
   - *Explicit acute distress* (wanting to die, suicide, self-harm, in so many words) is
     screened before any model call: `POST .../interview/turns` answers 200 with a fixed
     support response and four UK services, checked on their own pages on 2026-10-28
     (999 or A&E; NHS 111, mental health option; Samaritans 116 123; Shout 85258), and
     nothing is sent to the interviewer or stored. It is kept apart from career
     suitability: it scores and remembers nothing. Only explicit wording counts, so a
     figure of speech does not; a mention in another context (a suicide-prevention
     volunteer) does, by design, and the person can then send the message anyway
     (`send_after_support`).
   - *Inappropriate inference.* Model output may not name a health condition, a diagnosis,
     a personality type (or MBTI code), a protected characteristic or a percentage that the
     person's own messages never used; a condition the person names may be acknowledged,
     to ask which adjustment would help, but is never recorded in a career field. Both are
     validation problems, so the one bounded repair applies.
   - **Provisional, needs reviewed sign-off (R6; H-12):** the wording, the phrase lists and
     the resources. Clinical screening is out of scope; this is not one.

8. **The early requirement sketch** (`GET .../sketch`, STATE-05) resolves each target
   title against ESCO: one occupation gives its essential skills (the first six and the
   count); several give a choice (nothing guessed); none gives the nearest occupations and
   "not researched". Three generic steps (compare, find options, check time and cost)
   are always `unresolved`. It is labelled "Early sketch, not a checked route", names no
   provider, price or date, and lists which minimum inputs are not asked yet.

9. **The live evaluation is its own capped command** (`make live-eval`,
   `tools/live_eval.py`) on the existing usage ledger: the cases marked live (at most 6),
   one synthetic workspace each with a run limit of exactly one attempt, the test model
   only, the `live-eval` scope's cumulative cap (24 requests, no production request, $0.05
   worst case), every attempt ledgered after the worker stops, a leak scan, and results
   with failures by type appended to `docs/evidence/live-eval.md`. It is never part of
   `make check` or `make acceptance`. The offline evaluation runs the deterministic
   subjects (support screen, output guard, discovery with the fixture proposer over the
   full release); it certifies the pipeline, not the model.

10. **Export format 3** adds the discoveries (with their validated searches; slates are
    recomputed) and the interview preferences.

## Consequences

- Migration 0010; new run kind `discovery`; new event kind `interview.preferences_updated`;
  new source kind `occupation_choice`; new endpoints for preferences, discoveries, slates,
  targets and the sketch; `submit_turn` may answer 200 with the support response.
- Not done: model-written suggestion explanations; applying the salary floor (Sprint 3,
  with pay evidence); a salary floor per target; a human review of the evaluation cases
  and of the support policy (H-12).

## Human review checklist (H-12, not run — requires human)

- [ ] **Support policy** (decision 7): the fixed wording, the explicit-distress phrase list,
  the decision not to send or store the message, the "send anyway" path, and the four
  resources and their wording (checked against the services' pages on 2026-10-28).
- [ ] **Inference rules** (decision 7): the health, type and protected-characteristic word
  lists, and refusing a condition in a career field.
- [ ] **Slate policy** (decision 5): channel weights, the partial-match weight, the floor,
  the bonuses, quotas and the family limit.
- [ ] **Evaluation cases** (decision 9): the 39 cases and their semantic expectations.
