# ADR 0012: The capability model: matrices, evidence, protected gates, outcomes and readiness

- Status: Accepted for Task 9 (Sprint 4 backend, S4.1–S4.6). Amended in fix round 1
  (2026-10-29): decisions 4, 5, 7, 8, 9 and 10 changed, as marked. Amended again in fix
  round 2: decisions 4, 5, 7, 8 and 10, and the consequences; and in fix round 3: decision 7.
  - **Provisional, need product owner confirmation (R6):**
    - decision 3: how importance is derived, ESCO-only rows unknown, disputed counted as
      required;
    - decision 4: what verifies a protected gate, and the unmodelled gate for a regulated
      occupation;
    - decision 5: what evidence counts towards readiness, "with help" capped at level 1, and
      a reviewed demonstration below a self-report (review M4, parked);
    - decision 6: who reviews an assessed result;
    - decision 7: that the right to work alone is not coverage (fix round 2, review N6);
    - decision 8: the question weights, the 80% stop and the twelve initial prompts;
    - decision 10: how a target finds its pack target and ESCO seed.
  - **Not run — requires human:** the domain review of the capability reference (its
    rubrics, required levels, ESCO crosswalks and gate types). Task 11 put it in the session 2
    package, with a proposed level for every pack outcome (R1-R58,
    `docs/reviews/session-2-capability-questions.md`), and these provisional decisions on its
    decision sheet (D3-D11).
- Date: 2026-10-29
- Amended: 2026-10-31, the product owner's approval of the audit (the last section):
  decision 10's seed for a role outside ESCO, and Skills for any target.
- Requirements: MAP1-01–MAP1-08, OUT1-01–OUT1-07, OUT1-11, RDY1-01–RDY1-05, BND1-08,
  ASSESS-01, ASSESS-03–ASSESS-06, READINESS-01–04, TRACE01-06, VERSIONS-04, OPTN-09, PLN-04;
  spec sections 8, 9, 10 and 18; rulings R6, R9, R11, R12; ADR 0011 decisions 2, 10 and 13

## Context

Task 7b left the England option pack 0.1.0: real postings with requirement rows mapped to
pack-local rows (`pack:<target>:<row>`), course outcomes with an evidence kind and a
confidence but no level, and every record `proposed`. The pack is frozen. Sprint 4 needs
provisional matrices per target, evidence against behaviourally anchored levels, protected
gates, the outcome rules of OUT-1, readiness with the apply-now case, gaps and an abstract
action graph, and one question graph across the targets. Every one of these is
deterministic code: a model may later propose mappings and answers, never commit them.

## Decisions

1. **Its own module.** `careerwright/capability` (dispatch ruling 2; plan section 3, the capability
   half of "Capability and catalogue"): `reference.py` (the reference data and its loader),
   `matrix.py`, `evidence.py`, `outcomes.py`, `readiness.py`, `questions.py` (all pure),
   `store.py` (the SQL adapter, migration 0029, listed in the architecture test) and
   `commands.py` (use cases). It reads the catalogue (the pack, ESCO), the evidence module
   (the title key and the count of the person's examples), the profile (its targets) and
   identity. Only the API imports it.

2. **The capability reference.** A committed JSON file beside the module, pinned by its
   SHA-256 like the pack (`capability-reference-0.1.0.json`), written by an agent and
   `proposed`:
   - a rubric for each of the eight pack skill rows: an observable task, five behavioural
     anchors (spec section 8: 0 no evidence of performance … 4 designs or leads), a proposed
     required level (2 for every row: the postings are entry-level), acceptable proof,
     prerequisites (none stated by the sources) and one ESCO skill crosswalk, each an
     essential relation of the target's crosswalked occupation in ESCO v1.2.1;
   - the two gates the postings name, typed: NMC registration as legal practice, the right
     to work in the UK as eligibility;
   - an ESCO occupation crosswalk for each pack target (data quality specialist, ICT help
     desk agent, nurse responsible for general care, bookkeeper).

   The loader refuses a reference that is not its pin or does not fit its pack, and checks
   the pack references the capability model reads and Task 7b's validator leaves unchecked
   (Task 7b M3, dispatch ruling 4): option and skill-row targets, a requirement's target
   against its posting's, the sources postings and options name, and every gate wording
   having exactly one typed gate. The pack and its pin are unchanged. A version holds its
   rubric versions (`<row>@0.1.0`), so a revised rubric is a new rubric that earlier levels
   do not count for.

3. **Matrix rows and their importance (provisional).** A target's rows come from:
   - **pack rows**, from the postings of the pack target with the same title, each citing
     its claims (span, excerpt, hash, retrieval date, review state);
   - **gates**, from requirements whose row is a credential (NMC registration) or that name
     a gate without a row (the right to work);
   - **one posting's own requirements** (no pack row), employer-specific;
   - **ESCO seed rows**: the occupation's skill relations, except those a pack row's
     crosswalk folds in.

   Importance is what the postings state: all essential is essential, all preferred is
   preferred, a mix is disputed (SQL for P01's target: three postings essential, one
   preferred), none is unknown. An ESCO relation is a seed, not a requirement: an ESCO-only
   row is unknown and has no rubric, so it is reported as not modelled and never enters
   readiness (otherwise a nurse target would need evidence on 92 rows). One posting's
   requirement says nothing about the target, so its row is unknown, with the posting's own
   importance in its citation, and an essential one is listed as that posting's check. A
   **disputed row counts as required** until the person decides: some postings require it,
   so readiness never rests on leaving it out. Prevalence counts distinct vacancies
   (copies once): full-description vacancies apart from snippets and unknown descriptions,
   which are never evidence of absence.

4. **Protected gates.** A gate row carries its type, issuing body, jurisdiction and
   verification, and is always required. Setting any other importance is refused with the
   new code `PROTECTED_GATE` (409), before anything is written, and a stored edit can never
   demote one. The person may challenge its source: the reason is recorded on the row, the
   gate stays. Relaxing an employer's requirement out of the definition needs the explicit
   warning acknowledged (`CONFIRMATION_REQUIRED` otherwise), and then shows as a preference
   conflict gap. A gate is satisfied only when the person states they hold it **and verified
   it at its source** (their own entry on the NMC register; an employer's right to work
   check), recorded as their confirmation (provisional: L0 checks no register). Held but
   unverified, "don't know" and no answer are unresolved, never ineligible. A result resting
   on such a statement is qualified `person_confirmed_verification` (fix round 1, I3).

   **A regulated occupation is never silent** (fix round 1, C1(c); provisional). When ESCO
   records the target's occupation as regulated and no typed legal-practice or recognition
   gate models it, the matrix holds an unmodelled protected gate `gate:occupation-regulation`
   (`modelled: false`): always required, never demoted, not asked, listed as unresolved, and
   never satisfied by a statement (a statement on it is refused). ESCO flags only 16 of 3,039
   occupations (nurse and general practitioner among them; bookkeeper, data quality
   specialist and ICT help desk agent are not), so a regulated UK role ESCO does not flag
   gets no such gate. Decision 7's `insufficient_coverage` still keeps it from reading
   ready.

5. **Evidence (provisional).** An answer is about a subject (an ESCO skill, a pack row, a
   gate), so it is shared across targets, but a level counts only against the rubric it was
   chosen for: another target's row with the same subject and another rubric asks for its
   own level and offers the earlier example. Kept apart: the person's own level, a level a
   reviewed demonstration or assessment showed, and the confidence.

   **Towards readiness:**
   - a reviewed demonstration's level, `provisional` and never `corroborated` while L0 has
     no reviewer: the person enters it, so a result resting on one is qualified
     `person_confirmed_demonstration` (fix round 1, I3);
   - otherwise the latest self-report with a concrete example and when it was last done
     (`provisional`);
   - a level with no example stays `unsupported`, self-reported and not false, and counts
     for nothing.

   Time in a job adds nothing by itself: no field turns duration into a level. AI assistance
   is kept on every reading.

   **The five answers carry their meaning** (fix round 1, I2; spec section 9).
   - "I have not learned this" and "I understand it but have not tried" are a known level 0:
     a learn gap, not asked again.
   - "I am unsure" is unknown, never level 0: an unresolved assumption, listed and not asked
     again.
   - These level-free answers are shared across targets, never assumed the same (fix round
     2, review N1). One given under another rubric fills a row only when the row has no
     answer under its own rubric, and never supersedes one. If it is later and says "not yet
     done" against the row's own level above 0, that is a `conflict`, asked as a
     clarification. A later levelled answer under another rubric reopens a level-free
     reading, so the row is asked again (`other_rubric`).
   - An answer that contradicts its level is refused (`VALIDATION_FAILED`,
     `inconsistent_evidence`), as are the not-yet-done answers above level 0. Migration 0030
     repeats the rules as CHECKs (`NOT VALID`, so an earlier row is kept as written).
   - **"I did it with help" is at most level 1 (provisional):** spec section 8's anchors
     define level 1 as "performs with guidance" and levels 2 to 4 by independence, which is
     this reading's basis. The anchors do not state the ceiling in so many words.

   **"I've used this" (Task W2 slice W2B, plan section 4 "Usual is not confirmed"; provisional,
   R6).** A sixth answer, `used`: the person says they have used the skill, with no level and
   no word on independence (migration 0031 keeps it level-free and a self-report). It is how
   the world records a usual skill of the person's role picked as theirs, and a confirmed
   overlooked strength (ADR 0014 decision 3). It is level-free like "unsure", so it fills a
   row with no answer of its own, and reads as self-reported, `unsupported`, level unknown:
   it counts for nothing towards readiness and the row is still asked for its level
   (`UNSUPPORTED_CLAIM`). The evidence command also accepts, as subjects, the essential
   skills of the occupation the person's current or last role names (`esco:<skill ID>`);
   with no rubric there, only level-free answers fit.

   **Parked for session 2's decision sheet and the final review (review M4):** a reviewed
   demonstration below a concrete self-report sets the current level to the demonstration's
   (a self-report of 3 and a course assessment of 1 give 1, with `conflict: true`). An
   introductory assessment may show "at least 1" rather than "at most 1". The conflict
   prompts a clarification, so nothing is lost, but the rule is a choice.

6. **Outcomes (OUT-1).** The pack's planned outcomes load as provider claims with their
   span, evidence kind, confidence, rubric version, claim state and review state. A level on
   completion needs an assessed kind (exam or assessed work sample), the row's rubric and,
   for a provider claim, a source that supports it; a topic mention or unassessed practice is
   null. Credentials and supervised experience are their own outcome types and never have a
   level: C08's degree leads to eligibility to apply to the NMC, never to the registration
   gate itself. Accepting a mapping makes it `accepted_assumption`; a user override is a
   separate record beside the provider's, `accepted_assumption` and never `reviewed`. An
   outcome counts only in a conditional scenario, after its offering's completion gate and
   once accepted or reviewed; it never changes current evidence, and overlapping outcomes
   take the highest level, never a sum. An assessed completion changes evidence only as a
   new assessment record, once its review date is recorded (provisional: in L0 the review is
   the person's confirmation of the result and its assessor; there is no third-party
   reviewer).

7. **Readiness, gaps and the action graph.** For one matrix and definition version, ready
   means every required skill row at its required evidenced level and every required
   credential, experience and eligibility row satisfied. Blockers keep their kind: below the
   required level, no usable evidence, not modelled, not held, unresolved, and a pathway
   outside the model (every supporting pathway's shortest stated duration beyond the
   24-month M0 horizon: C08's three years, `MODEL_SCOPE_EXCEEDED` on the action). Nothing
   finds a person ineligible. Gaps are learn, demonstrate, credential, experience,
   eligibility, information or preference conflict, one abstract action each; options are
   offered only for learn, credential and experience gaps (and an unresolved credential gate
   shows its pathways for the case it is not held), never for a demonstration or an
   eligibility gap, and never before the person has said where they are. Each candidate says
   whether its source supports the mapping and whether a numeric solve may use it (a null
   level leaves a partial sketch). Ready now leads with reviewing current postings and
   applying (P05): no forced training, no route chart as the main result, evidence recency,
   the postings' own checks, optional development apart. Every L0 result is qualified: the
   matrix is provisional, and proposed records, proposed rubrics, self-reported evidence and
   assumptions are each named (OPTN-09, R9).

   **States keep what is known apart from what is not** (fix round 1, C1(a) and I1; Global
   Constraint 6):

   | State | When |
   |---|---|
   | `insufficient_coverage` | Nothing covers the target: no required skill row a rubric models, and no modelled legal-practice or recognition gate (an unknown target, ESCO seed rows only, a regulated occupation with only the unmodelled gate, or the right to work alone). A target-level blocker `no_modelled_requirements` (row ID null). Also when a required row no answer can settle sits beside modelled ones: a row with no rubric, or the unmodelled regulation gate (fix round 2, N5). Never ready |
   | `not_ready` | A known shortfall: below the required level, not held, or a pathway beyond the model. It comes first: a coverage gap or an unknown never hides a known shortfall, and is carried as its own blocker (fix round 3, re-review 2 R2-1) |
   | `not_yet_assessed` | Only unknowns the person's answers can settle block: no usable evidence, unresolved |
   | `conditional_on_assessed_completion` | Met only by a scenario's planned outcomes |
   | `ready_now_for_modelled_requirements` | Met now |

   `insufficient_coverage` is not the same state as `not_yet_assessed`: the person's answers
   can settle the second, never the first. A conditional scenario is a partial sketch,
   qualified `missing_outcome_level`, when a completed offering has an assessed, supported
   outcome for a required row with no stated level. A topic mention or unassessed practice
   rules a level out, so it is not "missing" (C06's exam is; C02's topic mention is not).

   **What counts as coverage (fix round 2, review N6; provisional).** "Ready" needs at
   least one required skill row a rubric models, or a modelled legal-practice or
   recognition gate. The right to work, or another eligibility or credential statement,
   alone is not coverage. Without this, a target whose skill rows the person had relaxed
   would read ready on the right to work. This is fail-safe, in the spirit of C1.

   **A route chart only when there is something to plan** (fix round 2, review N3; fix
   round 3, R2-1): `show_route_chart` follows the plannable gaps, not the state. It is true
   exactly when a mandatory gap an option could address (learn, credential or experience)
   exists. So it is false when ready now, and when only unknowns or coverage gaps remain. It
   stays true for a known shortfall beside a coverage gap: for example, P01's data quality
   target with every modelled row at level 1, after an ESCO row with no rubric is set to
   essential.

   **An open conflict is named** (fix round 3, re-review 2 R2-2). A result whose met
   required row rests on evidence in conflict is qualified `open_conflict`. That covers a
   demonstration disagreeing with a self-report, and a later "not yet done" under another
   rubric against the row's own level (decision 5). The result may still be ready now; the
   qualification says it rests on evidence awaiting the person's clarification (spec
   section 9). With pack 0.1.0 this is reachable through the demonstration case.

8. **The question graph (provisional weights).** One graph across the targets, a shared
   subject asked once. Requirements and gates first; then importance (essential 3, disputed
   2, preferred 1) × uncertainty (4 no answer, 3 unsupported, 2 another rubric's answer or a
   conflict, 0 usable) × route impact (targets served) / burden (1). The first twelve prompts
   are the initial set. Asking is "enough" once every gate is known or marked unresolved and
   at least 80% of the weighted required rows have usable evidence; "stopped" when the
   person stops or pauses, with every open question kept. Coverage is counts, never a
   percentage. With no modelled row or gate the state is `insufficient_coverage`, never
   "enough" (fix round 1). An unsure answer and a gate's "don't know" are not asked again
   and stay in `unresolved`. When coverage is short and they are all that remains, the
   state is `only_unresolved`, never "asking" with nothing to ask (fix round 2, review N2):
   what remains is an optional work sample, or stopping (spec section 9).

9. **Versions.** A matrix has a `matrix_version` (a digest of its content) and a
   `definition_version` (a digest of its required rows, their levels, rubrics and gate types).
   The workspace has a capability version, the expected version of every capability write.
   Every derived result carries the target, both matrix versions, the evidence version and
   the pack and reference versions; `ensure_current` refuses a result against another
   definition (`STALE_INPUT_VERSION`). An edit stores its actor, reason and old and new
   versions; an edit whose row the sources no longer give is reported, never dropped. Each
   gap depends only on its own row's subject and names the records it rests on, so an
   evidence change alters only the gaps it affects.

   **Labels on every result** (fix round 1, I4 and M8). The pack's date and each record's
   review state reach every derived result: the question graph's envelope carries the pack
   and reference labels; prompt rows, readiness rows and gaps carry their row's review
   state; candidate options carry their `as_of` date. Every capability response carries the
   workspace's `synthetic` and `data_mode`. A synthetic workspace's matrices, readiness and
   questions say `synthetic: true`.

10. **Persistence and the API (provisional matching).** Migration 0029: `capability_states`
    and the append-only `skill_evidence`, `requirement_statements` and `matrix_edits`, under
    row-level security, their CHECKs repeating the domain rules. Nothing derived is stored:
    matrices, questions and readiness are computed on read from the profile's targets. A
    target's pack target is the one with the same title (case and punctuation folded), or
    else the one pack target whose crosswalk names the target's ESCO occupation (fix round
    1, C1(b)). Choosing an occupation in the product stores ESCO's preferred label ("nurse
    responsible for general care"), and the second route brings it to the pack's rows and
    the NMC gate. Several such pack targets are never guessed between, and the matrix says
    why it has none (`pack_target_note: ambiguous_crosswalk`, fix round 2, review N4). The
    match is recorded as `pack_target.basis`.

    **The ESCO seed, in order** (fix round 2, C1(b)):
    1. the occupation the person chose, read from the choice's own source (its locator is
       the ESCO URI), never re-derived from the label (`occupation.basis:
       occupation_choice`);
    2. otherwise the one occupation ESCO labels with the title;
    3. otherwise, where several carry the label, the one whose *preferred* label is the
       title, which is how the product stores a choice. "bookkeeper" is ESCO's preferred
       label for bookkeeper and an alternative label of accountant;
    4. otherwise the pack target's crosswalk;
    5. otherwise none, with the reason.

    Two equal matches stay ambiguous. Migration 0030 adds the answer CHECKs (decision 5).
    Endpoints under
    `/v1/workspaces/{id}/capability`: `GET matrices`, `GET questions`, `GET readiness`,
    `POST evidence`, `POST statements`, `POST edits`, `PUT questions/state`, each write with
    an expected version and an Idempotency-Key, returning the new version.

11. **Not in this task.**
    - **The person's examples' requirement rows** are not read: their count is shown
      (`exemplar_rows_read: false`). Reading them needs a model proposal over the sealed
      text, or the person's own selection of spans; neither exists yet.
    - **Outcome decisions are not stored:** accept and override are domain functions. The
      option checkpoint (Task 12) owns accepting modelling assumptions (OUT1-11) and their
      persistence.
    - **No run kind and no model call:** nothing here is model-backed, so DBOS
      `application_version` is unchanged.
    - **No conditional-readiness endpoint:** Tasks 11 and 13a call `assess(..., completed=)`
      in the domain.

## Consequences and open items

- With pack 0.1.0 every readiness result is qualified, and every planned outcome's level is
  null, so every pack option is excluded from a numeric readiness solve until a reviewed
  version (Task 7c) or an accepted assumption gives a level. Task 11's TRACE-01 checker run
  on P01's real option set can check finances; its readiness stays a partial sketch.
- The capability reference needs the same human review as the pack's labels. Its rubrics,
  required levels, crosswalks and gate types are in session 2's package (Task 11, generated
  by `tools.session_2_files`).
- **Session 2's answers on the reference (R1-R40; Task 7c, 2026-10-30).** Yes to the four
  occupation crosswalks, every observable task, every ESCO skill, both gate types and the
  right-to-work check. "?" to every required level 2: the postings do not establish that
  entry threshold. No to every anchor set ("No evidence yet" must stay unknown, never level
  0) and to the NMC check (a matching PIN is not enough: check the registration's status,
  its register entry and any restrictions). Those answers change this model's own rules, so
  they are carried to Task 10 and nothing changes yet. Reference 0.2.0 carries 0.1.0's
  rubrics and gates unchanged to the reviewed pack 0.2.0, records these answers and stays
  `proposed`, so a readiness result resting on a rubric stays qualified `proposed_rubrics`.
  With pack 0.2.0 every outcome level is still null: session 2 accepted no proposed level.
- **UK-regulated roles in the reviewed pack** (Task 9 re-review 1, N7). The only one is the
  registered nurse, whose NMC registration is typed as a legal-practice gate (R37 yes),
  whatever ESCO's flag says; a test checks it. Live research must type such gates itself
  (Tasks 8, 10 and 12).
- The P01 demo workspace's target has the pack target's title, so it shows the real pack
  matrix (public reference data, as ESCO is), not TRACE-01's synthetic matrix.
- Ranks do not exist yet: Tasks 11 and 13a must key planning inputs and ranks by
  `definition_version`, so a changed definition makes them stale (MAP1-04).
- **The regulation guard rests on ESCO's flag** (fix round 2, review N7; forward risk).
  ESCO v1.2.1 flags 16 occupations. UK-regulated roles it does not flag (social worker,
  physiotherapist, occupational therapist, diagnostic radiographer) are kept from reading
  ready today only because nothing models them (decision 7). Task 7c's reviewed pack and
  live research must type a UK-regulated role's gate, whatever ESCO's flag says.
- **Migration 0030's `NOT VALID` CHECKs** (fix round 2, review N8). 0029 ran only on test
  databases, on this unpushed branch. A legacy row contradicting its level would be refused
  when read back by the domain validator, so every capability read for its workspace
  would answer `INTERNAL_ERROR`, observable, never silent. A populated-upgrade test is left
  for the final review (R12).

## Amendment, 2026-10-31 (the product owner's approval of the audit)

The product owner approved the audit on 2026-10-31: the decision path first, Skills for any
target, and roles beyond a fixed list (ADR 0015). The capability model changes as follows;
its rules on protected gates, unknown and readiness (decisions 4, 5 and 7) are unchanged.

- **Decision 10: the ESCO seed for a role outside ESCO.** For a provisional or researched
  role, the seed is the occupation the person chose as closest ("Which of these is
  closest?", recorded as an `occupation_choice`). "None of these is my job" means no seed:
  the target is `insufficient_coverage`, never ready. The seed order otherwise stands.
- **One stored target record.** Each target's occupation (or none), the source of that link
  and its coverage are stored once when it is chosen or saved (Task 6d). The capability
  model reads that record instead of resolving the title again, so You, Skills and the world
  can't disagree about the same target (the audit's code appendix, finding F5).
- **Skills for any target** (Task 10): what the seed occupation lists, labelled as ESCO's
  ("ESCO lists these for this kind of work"); the person's own examples' rows, read by their
  own selection of spans, with no new run kind (decision 11's open item); and "not assessed
  yet" with what the target asks, wherever no reviewed rubric exists (decision 7 already
  makes such a target `insufficient_coverage`).
- **"Not part of my job"** (the product owner's ESCO research): a skill the person marks so
  is a display state. It is never evidence, never a level and never a demotion of a
  protected gate.
- **Seniority and industry** beside a target are kept for display and search; matching and
  readiness ignore them.
- **Decision 11's owners.** Persisting accepted modelling assumptions and outcome overrides
  is Task 12a's (the stored planning inputs); the checkpoint's interface for them is Task
  12b's. Done in Task 12a: the planning inputs' `outcome_decisions` keep each acceptance or
  override with who made it and when; `planning.inputs.decided_outcomes` applies them through
  this model's own `accept` and `user_override`, and a decision this model refuses is refused
  at the write (ADR 0013, Task 12a's settlement).
- **Amendment line, Task 6d slice A (2026-10-31): Skills reads the stored target record** (ADR
  0015, amendment line). A matrix's ESCO seed and pack target are what the target's record
  names, never the title resolved again: the seed by any link (the person's choice, the one
  occupation holding the title as a label, or the pack target's crosswalk), the pack target by
  title or by its crosswalk, and several such pack targets stay `ambiguous_crosswalk`.
  `find_pack_target` and `pick_occupation` are gone. One set of rules now serves every
  chapter, so decision 10's seed order changes in two places, both the slate's rules (ADR
  0007 decision 13): a title is matched as a concept (case, punctuation, plurals, "&" and
  accents folded) with hidden labels included, and step 3 is dropped: where several
  occupations hold the title as a label, none is picked, even the one whose preferred label it
  is. A typed "bookkeeper" is now ambiguous in Skills, as in You, until the person chooses which
  they mean (the sketch asks); a chosen one still reaches P05's pack target through the
  crosswalk (`test_capability.py`). The evidence, statements and edits keep their
  `title_key` (data keying, unchanged). Fix round 1: a qualifier in brackets is left out
  again to reach a pack target by its title, as `title_key` did before ("Registered nurse
  (adult)" is P03's "Registered nurse"); the whole title as a concept comes first, and ESCO's
  labels are still matched by the whole title. Migration 0035 decides again each stored record
  this rule reaches.
- **Amendment line, Task 6d slice B (2026-10-31): the closest occupation, or none** (ADR 0015,
  amendment line). Decision 10's seed for a title the person keeps in their own words is the
  ESCO occupation they chose as closest (its record's `occupation_choice`), or none after
  "None of these is my job" (`none_of_these`: no ESCO rows; a pack target found by its title
  keeps its own rows). A qualifier naming another nursing field ("(mental health)",
  "(children's)", "(learning disabilities)") never reaches P03's adult "Registered nurse" by
  its title; a neutral qualifier still does. Migration 0036 decides again each stored record
  the bracket rule had taken there.
