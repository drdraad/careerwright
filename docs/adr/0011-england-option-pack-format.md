# ADR 0011: The England option pack's format, curation and labels

- Status: Accepted for Task 7b (Sprints 3–5 corpus items; plan v1.2). Amended in Task 7b
  fix round 1 (2026-10-29): decisions 3, 4, 7 and 9 changed, and 13 and 14 added. Amended
  again in fix round 2: decisions 2, 3 and 13; and in fix round 3: decisions 3 and 13.
  - **Provisional, need product owner confirmation (R6):** decisions 8 (P02 has no
    records), 9 (conflicting statements stay unresolved, and a bound is the label over a
    point at the same amount), 10 (pack-local skill rows) and 12 (a restrictive copyright
    notice keeps a page pending).
  - **Not run — requires human:** the labels' review (H-07, session 2) and C08's rights
    review (OI-07).
- Date: 2026-10-29
- Requirements: OPTN-08, OPTN-10, TEST1-09, OUT1-10, JOB-01; spec sections 6, 10, 11, 18
  and 20; ADR 0008 decision 1; rulings R2, R3, R6, R7, R9, R10, R11, R12

## Context

ADR 0008 decision 1 made the England option pack the first real evidence the numerical core
meets: 20 job postings, 10 course pages and 3 funding pages for the qualification personas'
targets, curated and labelled by an agent (Task 7b), then reviewed by a person at session 2
and published as a reviewed version (Task 7c). Tasks 9 and 11 load it through their own
domain models. So its format has to be boring, versioned and checked, and the labels have to
be precise enough for a person to accept or reject each one with a yes or a no.

## Decisions

1. **One JSON file per version.** The file is
   `backend/src/nessa/catalogue/packs/england_option_pack/england-option-pack-<version>.json`.
   The format is `nessa.catalogue.option_pack`: strict Pydantic models (unknown keys
   refused).
   - **Header:** a pack name, `format_version` (1), `pack_version`, `dated`, jurisdiction,
     currency, `synthetic: false` and the label review state.
   - **Content:** targets, pack-local skill rows, sources, claims, and the spec section 18
     records: job postings with their skill requirement rows, learning options with their
     dated offerings and planned outcomes (OUT-1, `PlanAction.outcomes`), and funding
     instruments.
   - **Versions:** a format change bumps `format_version`, and any change of content is a
     new `pack_version`.
2. **Every value is a claim.** A claim is a value read from one source, with its span and
   the exact excerpt there (at most 200 characters, the evidence records' bound).
   - **The span:** character offsets into the text whose SHA-256 is recorded (after
     redaction), or a JSON pointer into an API response.
   - **A record's field** cites a claim id or holds `{"unknown": "<why>"}`. Unknown is never
     zero, empty or a default.
   - **A record cites only its own sources' claims,** and every claim is cited by a record.
   - **Occurrences:** a claim records how often its excerpt occurs in the text, and its span
     is the first. The count is exact, except on the 21 fetched pages whose text is not
     kept: their excerpts were located before the locator counted past 5, so their source
     records `occurrence_cap: 5`, and a count of 5 there means at least 5. The Adzuna
     claims cite JSON pointers, each found once. A null count means not counted: a span the
     pipeline read itself, never located as an excerpt (`J01.salary_point`).
3. **The pack is committed and pinned, not fetched.** Version 0.1.0 is about 212 KB and holds
   only excerpts and values, never a page body. R7's "committed only if small and its rights
   permit" holds as follows.
   - **Pages within the policy's classes:** the session 1 policy permits committing excerpts
     for every class but `other`.
   - **C08, the one `other` page,** keeps hash and excerpts on R3's default for a page
     pending rights review. Whether those excerpts may stay is a question for the rights
     review before any push (OI-07).
   - **The pin:** each version's file is pinned by the SHA-256 of its bytes (`PINS`), and
     `load_pack` refuses a file that is not its pin.
   - **The canonical form:** a version's file is written by `tools.option_pack_files --pack`
     in the format's own canonical text (`dump_pack`), which a fast test checks.
   - **0.1.0 was re-cut twice before any push or consumer, each time with its pin moved in
     the same commit:**
     - `b38e462`: J06's pay and C02's duration became unknown (decision 9).
     - Task 7b fix round 1:
       - every value was put in its field's one shape (decision 13), and C06's intake
         became unknown (no future intake stated);
       - values on excerpt-only pages were reduced to what their excerpts show;
       - J19's place was left unresolved, and J01's single structured-data value was added
         as a fact (decision 9);
       - kept bodies' counts were made exact.
     - `format_version` stayed 1, since no consumer had read the earlier form.
     - Task 7b fix round 2, the last re-cut:
       - working patterns took the schedule shape and access periods the duration shape;
       - C04's 6 to 8 months became typical, never bounds, and its year of access became
         its own fact (at most 12 months);
       - rates state `repayable`, with C08's support grant not repayable, as its excerpt
         says;
       - J19's working pattern was reduced to its excerpt ("full time, 36 hours");
       - `J01.salary_point`'s count became null (not counted), and `J01.salary`'s note
         mentions the header again;
       - in fix round 3, part of this last re-cut, durations gained a declared "no end"
         (`unbounded`), and C03's "Lifetime access" took it in place of null.
     - `format_version` still stayed 1, for the same reason.
   - **0.1.0 is frozen from the end of Task 7b.** Any later change, Task 7c's reviewed
     version included, is a new file.
4. **The validator runs in the fast checks.** `check_pack` returns named problems, and
   `tests/domain/test_option_pack.py` loads and checks the committed pack in `make check`.
   It checks:
   - nothing synthetic (no fixture identifier, no example or test host);
   - every claim value against its field's shape, and every record field against the shape
     it declares for the claims it cites (decision 13);
   - references and orphan claims;
   - review records;
   - outcome levels (null without a rubric, and always null for a topic mention or an
     unsupported outcome);
   - one split per template family;
   - span offsets.

   The JSON Schema export (`schema()`) states the structure, every value shape and the
   shape each claim field and record field declares. It is committed beside the packs
   (`england-option-pack.schema.json`), and a fast test checks it against the export.
5. **Review state.** Every record carries `review_state` and an `as_of` date. Every record in
   0.1.0 is `proposed` (R9). A `reviewed` record must name its reviewer, date, session and
   decision. The validator refuses one without them.
6. **The labels live in the pack.** A corpus slot's `labels.claims` (`corpus/manifest.json`)
   names its claims there. A fast test checks that the manifest and the pack agree on every
   page's URL, hash, rights, retention, family, split, retrieval time and claims, and that
   the manifest records the pack's pin.
7. **Template families and splits came before any read or tuning.**
   - **The rule** was written before the first fetch.
   - **Groups:** a split group is a template family, joined to another when they share a
     vacancy. Within each source class, groups are numbered by their lowest slot, and groups
     2, 5, 8 and so on are holdout.
   - **A clause added at assignment:** "a family keeps the split it first got in every
     class" was added when the splits were assigned, after the captures and before any read.
     It changed two pages. C04's family already had the job class's development split, so
     it was not numbered again among the course groups. That made C07 development rather
     than holdout, and C08 holdout rather than development.
   - **Result:** 20 development pages and 13 holdout pages (`policy.holdout_split`).
   - **Use:** the early accuracy read uses development pages only (a test pins it), and no
     extraction was tuned on a holdout page. The one pipeline fix was reproduced on J01 and
     J12, both development pages.
8. **P02 has no records.** The fixture gives P02 (unsure) no target, so no record is curated
   for P02. The cities its slate draws on are covered by the other targets (Manchester,
   Bristol, Leeds).
9. **Conflicting statements stay unresolved; a bound is the label over a point.**
   - **Conflicts:** where one page states two values for one field that disagree, the field
     is unknown, giving both claims, and both are kept as valued facts. Examples are J06's
     two hourly ranges, C02's 14 and 12 weeks, and J19's board place against the advert
     text's place. This is the product's own rule for postings that disagree
     (`pages.mark_conflicts`). It is never resolved by choosing one or averaging.
   - **A bound and a point at the same amount** do not disagree: the bound is the label, and
     the point is kept as a fact. J01's advert says "Up to £28,000 per annum", so that is
     its pay. The structured data's single £28,000 is the fact `J01.salary_point`.
10. **Skill rows are pack-local.** A requirement maps to a row named `pack:<target>:<row>`,
    drawn from the postings' own requirements, or to no row. Task 9 maps rows to ESCO and
    gives them rubrics. Until then every planned outcome has `level_on_completion: null`,
    its evidence kind (topic_mention, practice, exam or assessed_work_sample) and its
    confidence.
11. **Adzuna slots use make live-adzuna's own path.**
    - **The search:** `tools.corpus --adzuna WHAT WHERE` runs one search through the
      `live-adzuna` scope's capped, ledgered, leak-scanned search. Two requests filled J02,
      J03 and J07 (ledger rows 34 and 35, $0), 4 of the scope's 10 used in all.
    - **The labels:** their values are the adapter's own readings, checked by the agent
      against the API excerpts beside them. So the accuracy read does not score them.
12. **A restrictive copyright notice keeps a page pending.**
    - **C08:** The University of Manchester's notice says its material "may not be
      reproduced without permission". That is not clearly within line A3, so the page stays
      "pending human rights review", with its hash and excerpts only.
    - **C01:** Netcom's "©Copyright 2026 all rights reserved" was read as an ordinary
      notice within A3, so its body is kept privately.
    - **Open question:** whether the two should be treated alike is put to the rights review
      before any push (OI-07).
    - **Job boards (A6)** stay reference only. Their terms ("private or domestic purposes"
      only) allow nothing more.
13. **Every value has one shape, declared by its field.**
    - **The shapes are boring:** numbers, ISO strings, fixed words or text. A value is never
      a float, and never a range written as a string. A null value means only that the page
      withholds or lacks the value, so it has no shape. A value the page states is never
      null: a stated "no end" is a duration with `unbounded: true`.
    - **Claim fields:** each claim field declares its shape (`CLAIM_FIELD_SHAPES`), and a
      field not listed holds text.
    - **Record fields:** each record field declares the shape of the claims it cites
      (`RECORD_FIELD_SHAPES`). The validator checks a cited claim against it, whatever the
      claim's own field is called. This closes the path by which 0.1.0's C06 intake cited a
      list of past months.
    - **Facts, rules and funding conditions** take their claims' own field shapes.

    | Shape | Value | Record fields that declare it |
    |---|---|---|
    | money | `{"currency": "GBP", "minor_units": int ≥ 0}` | `Offering.fee_total`, `Offering.extra_costs` |
    | rate | money plus `"period"`, `"at_least": bool` and `"repayable": bool or null` (a yearly fee or grant; null means the page does not say, never false) | (facts and conditions: `fee_per_year_*`, `support_grant`) |
    | pay | `{"currency", "minimum_minor_units", "maximum_minor_units", "period", "basis"}`: integer ends, either may be null but not both, maximum ≥ minimum; `period` year, month, week, day, hour or null; `basis` advertised, predicted or unknown | `JobPosting.salary`, `Offering.wage` |
    | instalment | `{"currency", "minor_units": int or null, "period", "count": int or null, "at_least": bool}`, with an amount or a count | `Offering.instalment` |
    | date | an ISO date `YYYY-MM-DD` or month `YYYY-MM` | `Offering.intake`, `Offering.application_deadline`, `JobPosting.date_posted`, `FundingInstrument.published_on`, `FundingInstrument.rules_updated_on` |
    | deadline (datetime) | an ISO date, or an ISO datetime with its UTC offset | `JobPosting.valid_through` |
    | duration | a list of `{"unit": hours, weeks, months, years or null, "minimum", "maximum", "mode": full_time, part_time, self_paced or null, "typical": bool, "unbounded": bool}`, one per way of taking it; integer ends with their unit; `typical: true` is what is typical (an average), never bounds; `unbounded: true` is a stated "no end" ("Lifetime access"), with no maximum and, if no minimum, no unit; otherwise at least one end | `Offering.duration` (facts: `contract_duration`, `duration_limit`, `access_period`) |
    | schedule | `{"pattern": full_time, part_time, flexible or null, "hours_per_week": int or null}`, with at least one | `Offering.schedule` (facts: a posting's `working_pattern`) |
    | place | `{"label", "locality", "region", "postal_code"}`, the label required | `JobPosting.location`, `Offering.location` |
    | level | an RQF level, 0 to 8 | `LearningOption.level` |

    The other shapes are these: dates (a list of dates), count, flag, names (a list of
    text), age_rule, earnings_rule, levels, level_change, crosswalk, advertiser, work_mode,
    description_kind and text. The committed schema states each one.
14. **Session 2's package is generated, ordered by the gates it closes.**
    - **Generated:** `tools.option_pack_files` writes the whole package from the pinned
      pack, its text included, so question numbers are stable. Task 7c applies the answers
      by number. A fast test checks the committed package against the tool's output.
    - **What it asks:** every consequential field, which is pay and its basis, money,
      dates, durations and schedules, entry requirements, gates, eligibility rules, award
      status, outcome levels and open conflicts. It also asks every fact of those shapes, and
      every essential credential or eligibility requirement, gated or not. Instrument kinds
      are shown beside their claims.
    - **The order:**
      1. P01's section in full (TRACE-01's real option set);
      2. P03–P05's options, offerings, outcomes, then the funding (H-07 for Sprints 4–5);
      3. P03–P05's job postings and requirements (Task 8 may take any left over).
    - **The reviewer may stop at the end of any part.** Each record's rows all fall in one
      part.
    - **The partial-record rule, which Task 7c applies:** a record becomes `reviewed` only
      when every one of its rows is answered yes. Otherwise it stays `proposed`, and a "no"
      records the correction for a later version.

## Consequences

- **Consumers** (Tasks 9 and 11) read `load_pack(version)` and `Pack.value(ref)` and never
  parse the file themselves. They can rely on decision 13's shapes. A record is explorable
  but never in an unqualified recommendation until it is `reviewed` (OPTN-09).
- **Session 2's package** asks 344 yes/no questions in three parts of about 17, 38 and 32
  minutes (`docs/reviews/session-2-option-pack-questions.md`). The session may stop after
  any part, and anything unanswered stays `proposed`.
- **The job corpus rests on job boards** (Reed and NHS Jobs), because no employer careers or
  applicant-tracking page could be read through the product's fetcher (OI-12). The early
  accuracy read found that boards name the advertiser as `hiringOrganization`. So agency
  names reach the employer field unless the agency words catch them. That is a finding
  for Task 8, not a fix here (R11, R12; `docs/evidence/option-pack-accuracy-read.md`).
