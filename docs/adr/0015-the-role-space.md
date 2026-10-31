# ADR 0015: The role space

- Status: Accepted, 2026-10-31. The product owner approved the audit's decisions 2
  (recognise any UK job title, and always keep the person's own) and 3 (research roles that
  no list holds), and the matching `CLAUDE.md` wording. Details marked "to be settled by
  Task <id>" are open, for that task.
- Date: 2026-10-31
- Source: the whole-solution audit (`docs/reviews/l0-audit-2026-10-31.md`, section 3) and its
  role-space appendix (`docs/reviews/l0-audit-2026-10-31/F-role-space.md`); the product
  owner's research on ESCO's limits (their own file, not committed).
- Requirements: DIV1-03, DIV1-04, DIV1-10, DIV1-13, DIV1-14, DIV1-15, REC1-05, REC1-06,
  PROF-08, PROF-10, PROF-11, PROF-12, MAP1-09, TEST1-15; spec sections 4 (REC-1, DIV-1), 5
  (TAX-1), 6, 11, 16 and 18; ADRs 0006, 0007, 0009, 0010, 0012 and 0014

## Context

The product owner, 2026-10-31: "One thing that is really important to me is that we aren't
limited to a prefilled list of roles - the real world is much more complex than those
standardised job lists, and I want to avoid the frustration of your ideal job not appearing
as an option to select. This is where deep research and LLMs have a part to play to fill out
the "role space" more fully. I want it to feel like you have an omniscient career coach who
knows all possible jobs that could fit you."

What the audit found:
- **Keeping roles to ESCO was a local ruling, not the specification.** DIV-1 says a role
  library "is a cache accelerator, never the universe of recommendable careers", asks for
  "emerging roles absent from older taxonomies", and says "LLM-generated titles are search
  hypotheses until corroborated by an authoritative occupational/professional source or
  independent employer evidence; duplicated adverts do not constitute independent support".
  ADR 0007 narrowed that to "only if ESCO holds it as a label", and the employer-evidence
  half was never built.
- **An authoritative UK title list is already pinned and imported, and discovery doesn't
  use it.** The ONS SOC 2020 coding index (v14, 2026-08-27, Open Government Licence v3.0)
  holds about 23,900 distinct titles, about 20,300 of them no ESCO label ("Registered
  nurse", "Data quality analyst", "Prompt engineer", "Retrofit coordinator", "Doula"). Each
  carries ONS's own SOC 2020 unit group and ISCO-08 group. Until now it served only pay codes
  (ADR 0010 decision 5).
- **The model's title ideas were thrown away** unless ESCO held them ("couldn't match … so
  not suggested"): the frustration the product owner described.
- **The best-covered roles were the ones the You chapter couldn't recognise.** Three of the
  option pack's four reviewed targets are not ESCO titles.
- **Downstream, a role outside ESCO loses almost nothing.** Every role outside the pack is
  already "can't be assessed yet", ESCO roles included, and job search already takes any
  title as text.

The product owner's research supports ESCO as a shared vocabulary under a richer record of
the real role, which is what the reviewed pack already does for its four targets. It
conflicts with the design in three places: ESCO's essential skills alone drove several
revelations; no one could say "none of these is my job"; seniority and industry weren't
kept.

## Decisions

1. **Four layers, from the cheapest.**
   1. **ESCO** (the pinned v1.2.1 release): the shared vocabulary of occupations and skills.
   2. **The ONS SOC 2020 coding index** (pinned, hash-checked): about 24,000 UK job titles,
      each with ONS's own unit group and ISCO-08 group. An authoritative occupational source
      for DIV-1's corroboration. Free, offline, and it works in the demo.
   3. **The person's own words:** always accepted, always kept as typed, as a provisional
      concept (ADR 0006 decision 5), never refused.
   4. **Researched roles:** for a title no list holds, at the person's request, one bounded
      web search and the pages it finds (Task 6e).
   Not in L0: one deep-research run that maps a person's whole role space. It is M1 in the
   specification, it would break today's budget rules, runs of more than two searches are
   unqualified, and it would send the person's words to a web-searching model.

2. **The corroboration rule.** A title the model proposes becomes a suggestion only when
   deterministic code corroborates it, in one of three ways:
   - an ESCO label, as a concept (`careerwright.concept_key`);
   - a title in the pinned ONS coding index, matched exactly on the index's normalised
     title;
   - the title verified as a quoted span of the visible text of pages from **two
     independent permitted sources**, or of one page of an **official source**.
   **Independent** means distinct hosts or distinct employers. Copies of one advert fold
   into one job (ADR 0009 decision 6) and never count twice. **Official** means a page whose
   class in the source manifest is `govuk`, `public-sector` or `professional-body`. An idea
   nothing corroborates is shown as "not yet found", never hidden and never a suggestion.
   Nothing is claimed beyond what its source holds ("ONS lists this title", or "found on
   these pages"), and the quotes and dates are one step away.

3. **The role record.** A role outside ESCO is a provisional concept, private to its
   workspace, holding:
   - the person's words, the title as typed;
   - its sources: the person's confirmation, the ONS entry with its SOC 2020 and ISCO-08
     codes, or the SourceClaims of verified pages with their dates;
   - the ESCO occupation the person chose as closest, or none ("None of these is my job");
   - optional seniority and industry, which matching ignores and display and search keep;
   - for researched evidence, `review_state: proposed` (ruling R9).
   Each target is stored once with its occupation (or none), the source of that link and how
   far Careerwright can cover it, and every module reads that record (Task 6d; ADR 0012,
   amendment).

4. **ESCO under the real role** (the product owner's research). Skills ESCO lists for a role
   are described as "ESCO lists these for this kind of work". The person can mark one "not
   part of my job", a display state that is never evidence. No revelation rests on ESCO's
   essential skills alone; how the unexpected connection (ADR 0007 decision 14) meets this is
   to be settled by Task 6d, asking the product owner before a second round.

5. **What is sent.** Role research sends only the title and "England", never the person's
   answers (SEC-05). Title ideas still come from the existing discovery call, which reads
   only the person's confirmed answers about work.

6. **Per-role spend bounds.** The first step (Task 6d) adds no model call. The second (Task
   6e) makes one search request per role with no repair (ADR 0009 decision 12): worst case at
   most $0.045 a role on Spark, about 1–5 US cents in the audit's estimate. On Muse Wonder,
   the session command's run limit (about $0.75, ADR 0003, amendment) lets three attempts
   fit. Quoting a found role's duties is optional and must fit decision 15's extraction
   bounds (ADR 0009); whether it does is to be settled by Task 6e. The estimated cost shows
   before research starts, and every call is ledgered (R5).

7. **The model choice.** Role research is a run like any other: the test model for synthetic
   workspaces, the production model for the rest (Spark; Muse Wonder in the product owner's
   own sessions). A demo workspace never searches, so the second step is live only; the
   first step works offline and in the demo.

8. **What later chapters show for such a role.**

   | Chapter | Shows | Unknown or not yet |
   |---|---|---|
   | Skills | What the chosen closest occupation lists, labelled as ESCO's; what the person's chosen adverts ask for; the person's answers as evidence | Required levels and readiness: `insufficient_coverage`, as for every role outside the pack. With "None of these is my job", no ESCO rows at all |
   | Pay | An ONS-coded title: ASHE for its own unit group or groups by region, labelled the group's (ADR 0010, amendment). A researched role: advertised pay read from verified spans | Modelled pay and the salary floor's rule, unchanged: only through a reviewed mapping. Never a city's pay |
   | AI evidence | Its ISCO-08 group's exposure, labelled the group's | Resilience: unscored, as for every real role in L0 |
   | Roles | Real listings: the source search and Adzuna take the title as text | "No listings" is a demand signal, never "this job doesn't exist" (DIV1-09) |
   | Options and routes | Options the person adds and options research finds, as proposed records (ADRs 0011 and 0013, amendments) | Anything else: "not researched yet" |

9. **Where it is built.** Task 6d (S2.8, "your title, recognised") and Task 6e (S2.9,
   "research this role"), before session W2 and Skills, so the product owner judges the
   suggestions with the role space open. Task 8 shows such roles on the opportunity map; how
   they are grouped where no ESCO occupation joins them is to be settled by Task 8. Task 16's
   live journey includes a persona whose target is outside ESCO.

## Consequences

- `CLAUDE.md`'s discovery invariant changes, in the product owner's approved words. ADR 0006
  decision 5, ADR 0007 decisions 4, 5, 13 and 14, ADR 0009 decision 12, ADR 0010, ADR 0012
  decision 10 and ADR 0014 decisions 3 and 4 are amended on the same date.
- The specification's revision record (section 22, 2026-10-31) names the ONS coding index as
  an authoritative occupational source for DIV-1, defines "independent", and records that L0
  widens DIV-1's corroboration clause as the product owner approved (two independent
  permitted sources of any class, or one official source). No invariant is relaxed: the
  model proposes, deterministic code corroborates, the person chooses, and unknown stays
  shadow.
- Register: new rows DIV1-13, DIV1-14, DIV1-15, PROF-10, PROF-11, PROF-12, MAP1-09 and
  TEST1-15. DIV1-04 is corrected: its employer-evidence half was never built in Task 7, and
  Task 6e builds it.
- Risks, and their answers:
  - Matching and wording loops, the kind that took five rounds in W2B: the sentence rule from
    the start, the product owner judging suggestion quality at session W2, and at most one
    matching round (rulings R11 and R14).
  - The quality of the live search for role pages is unqualified until Task 6e's live test.
  - Some ONS titles are dated ("Bookkeeper-typist"), and some are coded to more than one
    group ("Registered nurse"): every group is shown, none picked.
  - A page from a source class the session 1 rights policy doesn't cover stays with a person
    (ruling R10).

## Amendment line, Task 6d slice A (2026-10-31): each target is stored once

Decision 3's last sentence is built (`careerwright.profile.targets`, migration 0034).
- **The record.** `target_records` holds one row per target title of a workspace, keyed by the
  title as a concept: its kind (an ESCO title chosen as such, or the person's own words), the
  ESCO occupation it names or none, the source of that link (`occupation_choice`,
  `exact_label`, `pack_crosswalk` or `none`), every occupation holding the title as a label,
  and its coverage (one of the option pack's targets, by title or by the crosswalk of its
  occupation, or not; several crosswalked pack targets are never guessed between). Its CHECKs
  already allow slice B's kinds: an ONS title (`kind = 'ons'`, with its SOC 2020 and ISCO-08
  codes) and "None of these is my job" (`none_of_these`), so slice B needs no second migration.
- **One resolver, one set of rules.** `resolve_target` decides the record when a target is
  chosen or saved (the one profile write path stores a record for each new target title, and
  the person's choice of an occupation replaces its title's record). A title is compared as a
  concept, hidden labels included; several labels stay several, none picked. It replaces the
  four resolvers the audit found (the code appendix, F5). The slate, the sketch and the
  strength join work only to an occupation ESCO itself names (the person's choice or the one
  label: ADR 0007 decision 13, unchanged); Skills also reads the pack's crosswalk (ADR 0012).
  The web reads the records (`GET .../targets`): the world's destinations and "already a
  target" are keyed by them, never by comparing titles.
- **The concept key** reads "&" as "and" and folds accents (every Latin-1 Supplement and
  Latin Extended-A letter that decomposes to one ASCII letter), in migration 0034, which
  rebuilds the label index. So "food and beverage supervisor" is ESCO's "food & beverage
  supervisor", and "facade cleaner" its "façade cleaner"; a provisional concept with such a
  title is refused as that occupation, as any ESCO label is.
- **Existing profiles migrate forward:** 0034 gives each current target its record by the same
  rules, against the pinned pack 0.1.0 and its crosswalks (a test checks the backfill against
  `resolve_target`). A later pack that drops a target needs a forward migration of the
  records it names; the capability model refuses a record naming a pack target the committed
  pack lacks (`INTERNAL_ERROR`), never silently.
- **Every version's targets (fix round 1).** 0034 recorded only each workspace's newest
  targets, but a discovery is read from the profile version it pinned, so one made before a
  target was replaced could not open. Migration 0035 records every target title of every
  version that has no record (once per workspace and title as a concept, spelled as the
  latest version holding it), by the same rules; 0034 is unchanged, as a lasting database
  may already hold it. 0035 also decides again each record the restored bracket rule reaches
  (ADR 0012's line).
- **A title with no record (fix round 2)** is decided on read by `resolve_target`, as it
  would be stored, and nothing is stored on a read: never an error, and never "couldn't
  match" where no match was tried. Every write path stores its targets' records; an
  architecture test keeps profile versions written only by the one write path and the
  fixture seed, and integration tests check their records in the tables themselves.
- **One record, two spellings.** The concept key reads brackets as word breaks, but the
  bracket rule reads them as a qualifier. So "Registered nurse adult" and "Registered nurse
  (adult)" share one record key, though only the second reaches the pack's "Registered nurse"
  by title. Whichever is saved first stands for both.
- **Coverage shown where a target is chosen:** one plain line from the record's coverage
  ("Careerwright can check skills, options and routes for this role" for a pack target),
  worded in the web; session W2 judges the words.

## Amendment line, Task 6d slice B (2026-10-31): your title, recognised

Decisions 1 to 3's first step is built (S2.8; `careerwright.catalogue.uk_titles`, migration
0036). Words are worded in the web from facts (ruling R11); session W2 judges them.
- **The first question** leads the You chapter's start: its type-ahead offers ESCO's titles
  and the UK job-title index's (`GET /v1/taxonomy/titles`: every title holding each typed word
  as a word beginning, one per title however many entries the index gives it, with every SOC
  2020 unit group and ISCO-08 group ONS codes it to, none picked), marked "UK job title
  (ONS)". A title ESCO itself offers (a preferred or alternative label, as a concept) is
  offered as ESCO's only. Best first: what was typed, then a title beginning with it, then the
  rest, ESCO first on ties. ESCO's closest titles ("Careerwright couldn't match that title in
  ESCO. Is it one of these?") only when neither list holds every word, with "None of these is
  my job", which keeps the person's own words. "Use my own words" is always the last option
  and keeps the title exactly as typed (`POST .../origin/role/title`); nothing is refused, no
  model is called, and it works without a key and in the demo. "Skip for now" goes on to how to
  start, saving nothing. The answer lights the person's light at once; a browser test proves
  it within ten seconds; on the full release the type-ahead took about 20 ms and the save and
  the origin read together about 50 ms (`test_first_answer.py`, one run on this machine).
- **"Which of these is closest?"** is asked for a role whose title the index lists and no ESCO
  occupation holds as a label (the origin's `role.closest`; `POST .../origin/role/closest`):
  the ESCO occupations in every ISCO-08 group ONS codes the title to, by group, none picked (a
  group the held release has no occupation in says so). A choice becomes the role's ESCO
  occupation with the person's words kept (the role cites it, as `choose_role` does); "None of
  these is my job" leaves the role with no ESCO occupation, its words say what isn't known yet,
  and nothing asks for another job. A title the index doesn't list has no groups, so its words
  say what Careerwright did with it and what isn't known yet, with no closest question.
- **The record** (decision 3) holds a title's words as `esco`, `ons` (a title the index lists
  exactly, on its normalised title, with its SOC 2020 and ISCO-08 codes) or `own_words`; the
  closest occupation the person chose (`occupation_choice`, citing its source) or
  `none_of_these`. The role named at the first question is recorded in the same table, one
  record per title as a concept, so a target with the same title reads the same record. The
  record is the provisional concept this decision describes; the older `provisional_concepts`
  table keeps its own API (DIV1-03). The CHECKs needed no change: a choice still cites its
  source, an ONS title's codes are in its row, and "None of these is my job" names no
  occupation and is recorded with who decided it and when. `resolve_target` refuses to decide
  without the index (`REFERENCE_DATA_UNAVAILABLE`), never "not listed"; setup imports the
  reference data before the seed. Migration 0036 makes each stored own-words record whose
  title the index lists an ONS title with its codes.
- **Title ideas** (decision 2): each carries what Careerwright did with it (`reason`:
  `in_esco`, `in_uk_title_index`, `not_yet_found`, `not_searched`). One the index lists and
  ESCO doesn't is a suggestion in its own list beside the slate ("Title ideas found in the UK
  job-title index", with the answers it came from), never in the slate's pool; one no list
  holds is named as not yet found and never suggested. The evaluation case DSC-20 checks it on
  the full release. Making such an idea a target is not built in this slice (it can be named as
  a target in What we know).
- **Another nursing field.** A qualifier in brackets naming another field the Nursing and
  Midwifery Council registers ("(mental health)", "(children's)", "(learning disabilities)")
  never takes a title to the pack's "Registered nurse", whose evidence is adult nursing
  (`careerwright.profile.targets.OTHER_FIELDS`); a neutral one ("(adult)") still does. 0036
  decides again each stored record the bracket rule had taken there.

## Amendment line, Task 6d slice B fix round 1 (2026-10-31): one record for the role, and the person's refusal kept

The two reviews' findings, fixed (the fix list, `task-6dB-fix-round-1.md`). Session W2 still
judges the words.
- **The role's record is its one truth** (decision 3). Every reader takes the role's ESCO
  occupation from its title's record (`careerwright.profile.targets.role_record`), as each
  target's is taken, never from the role's source. Every write that changes the role stores it
  (`record_role`, in the one write path): a decision the person makes (an ESCO title chosen as
  such, a closest occupation, "None of these is my job") replaces the record of that title;
  any other change keeps the record of its title as a concept, so capitals, or away and back,
  never lose a choice, and the origin never says "chosen" for an occupation the role no longer
  names. A role saved before its record was kept is decided as it would be stored.
- **"None of these is my job" is the person's refusal, wherever it is offered.** Under the
  type-ahead's partial list it is recorded on the title (`NameRole.none_of_these`), and at the
  closest question every answer is a new profile version, so a tab holding an older version
  conflicts. Enter with no option chosen keeps the person's typed words, never a partial match
  and never a refusal they didn't make. The slate's fact for a role kept in their words,
  `role_not_matched`, asks for no other job ("Careerwright keeps “…” as your role, in your
  words. It couldn't match it to an occupation in ESCO, so it joins no other work to it by
  shared skills."), and "Something different" is said only where the slate's own fact says the
  role's or a target's kind of work is known (`familiarity_known`).
- **The first question goes through the support screen** (ADR 0007 decision 7, the
  controller's ruling): a title that triggers it matches nothing, is offered nothing and never
  repeated back, is never kept as the role, and the calm panel shows and stills the world.
- **The closest question** is not asked when none of the title's groups holds an ESCO
  occupation in the held release (there is nothing to pick); its groups are named in plain
  words, never by code; and "Change my job title" goes back to the first question.
- **Migration 0038's CHECKs** repeat the rules: an ONS title has at least one SOC 2020 and
  one ISCO-08 code, and `none_of_these` is recorded only with who decided it, on an ONS title
  or the person's own words (the partial list's refusal is on their own words), never an ESCO
  title.
- **Known limits (L0, recorded, not fixed; ruling R11):**
  - A record is keyed by the title as a concept, but its kind is decided on the exact spelling
    of whichever write came first: "Registered nurse." and "Registered nurses" share the record
    of "Registered nurse", and "Registered nurses" is not itself an index title.
  - The type-ahead leaves out an index title that ESCO holds as a concept, but ESCO's own list
    matches word beginnings: an index title whose ESCO twin is written with "&" or an accent
    can drop out of both lists and fall to the partial list.
  - On a database migrated to 0035 without the index, own-words records stay own words once
    the index arrives: nothing decides them again. Setup imports the index before anything is
    stored, so this needs a database made outside setup.
  - 0036's SQL folds case with `lower()` where the index's normalised titles use Python's
    `casefold()`; they differ only for letters such as "ß", which no index title holds.

## Amendment line, Task 6d slice B fix round 2 (2026-10-31): the person's own answer first

The re-reviews' findings, fixed (`task-6dB-fix-round-2.md`). Session W2 still judges the
words; a real phone's keyboard stays a human check.
- **"Use my own words" is the type-ahead's first option** (before: the last), and under a
  partial list "None of these is my job" sits right under the question, so the person's own
  answer is in a phone's first screen however many titles follow. The option the person
  arrowed to is kept by its key, so a title that moves as the list arrives is never Enter's
  pick, and own words arrowed to never become a refusal when a partial list arrives.
- **The first question's support panel sits above the title field**, as the message panel
  sits above the reply field, and stays until the person dismisses it, after a skip or
  another answer too. A title it answers is kept only by the person's choice in the panel
  (ADR 0007, amendment line, fix round 2). While fixing a title, the way back to the closest
  question is named for what it does ("Back to “Which of these is closest?”").
