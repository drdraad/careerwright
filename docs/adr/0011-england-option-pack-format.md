# ADR 0011: The England option pack's format, curation and labels

- Status: Accepted for Task 7b (Sprints 3–5 corpus items; plan v1.2).
  - **Provisional, need product owner confirmation (R6):** decisions 8 (P02 has no
    records), 9 (conflicting statements stay unresolved), 10 (pack-local skill rows) and 12
    (a restrictive copyright notice keeps a page pending).
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
   refused), with an exported JSON Schema (`schema()`).
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
   - **Money** is integer GBP minor units, and no claim value holds a float.
   - **A record cites only its own sources' claims,** and every claim is cited by a record.
3. **The pack is committed and pinned, not fetched.** Version 0.1.0 is 209 KB and holds
   only excerpts and values, never a page body. The session 1 rights policy lets every
   class's excerpts be committed, so R7's "committed only if small and its rights permit"
   holds.
   - **The pin:** each version's file is pinned by the SHA-256 of its bytes (`PINS`), and
     `load_pack` refuses a file that is not its pin.
   - **0.1.0's content is final** from Task 7b's final candidate onwards. It changed once
     before any push or consumer: J06's pay and C02's duration became unknown (decision 9),
     and the pin moved in the same commit.
   - **Later versions:** Task 7c publishes the reviewed version as a new file and leaves
     0.1.0 unchanged.
4. **The validator runs in the fast checks.** `check_pack` returns named problems, and
   `tests/domain/test_option_pack.py` loads and checks the committed pack in `make check`.
   It checks:
   - nothing synthetic (no fixture identifier, no example or test host);
   - claim value shapes (money, pay ranges with maximum ≥ minimum, dates, no floats);
   - references and orphan claims;
   - review records;
   - outcome levels (null without a rubric, and always null for a topic mention or an
     unsupported outcome);
   - one split per template family;
   - span offsets.
5. **Review state.** Every record carries `review_state` and an `as_of` date. Every record in
   0.1.0 is `proposed` (R9). A `reviewed` record must name its reviewer, date, session and
   decision. The validator refuses one without them.
6. **The labels live in the pack.** A corpus slot's `labels.claims` (`corpus/manifest.json`)
   names its claims there. A fast test checks that the manifest and the pack agree on every
   page's URL, hash, rights, retention, family, split, retrieval time and claims, and that
   the manifest records the pack's pin.
7. **Template families and splits came before the first fetch.** The rule was written
   before any fetch (`policy.holdout_split`).
   - **Groups:** a split group is a template family, joined to another when they share a
     vacancy. Within each source class, groups are numbered by their lowest slot, and groups
     2, 5, 8 and so on are holdout.
   - **Result:** 20 development pages and 13 holdout pages.
   - **Use:** the early accuracy read uses development pages only, and no extraction was
     tuned on any page.
8. **P02 has no records.** The fixture gives P02 (unsure) no target, so no record is curated
   for P02. The cities its slate draws on are covered by the other targets (Manchester,
   Bristol, Leeds).
9. **Conflicting statements stay unresolved.** Where one page states two values for one
   field, the field is unknown, giving both claims, and both are kept as facts. Examples are
   J06's two hourly ranges, C02's 14 and 12 weeks, and J19's board place against its text's
   place. This is the product's own rule for postings that disagree
   (`pages.mark_conflicts`). It is never resolved by choosing one or averaging.
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
12. **A restrictive copyright notice keeps a page pending.** A provider page whose own notice
    says its material "may not be reproduced without permission" (The University of
    Manchester, C08) is not clearly within line A3. It stays "pending human rights review",
    with its hash and excerpts only. A job board (A6) stays reference only. Its terms
    ("private or domestic purposes" only) allow nothing more.

## Consequences

- **Consumers** (Tasks 9 and 11) read `load_pack(version)` and `Pack.value(ref)` and never
  parse the file themselves. A record is explorable but never in an unqualified
  recommendation until it is `reviewed` (OPTN-09).
- **Session 2's package** asks 314 yes/no questions (`docs/reviews/session-2-option-pack-questions.md`).
  That is about 80 minutes. Its "Answer these first" list comes first if time is short, and
  any record left undecided stays `proposed`.
- **The job corpus rests on job boards** (Reed and NHS Jobs), because no employer careers or
  applicant-tracking page could be read through the product's fetcher (OI-12). The early
  accuracy read found that boards name the advertiser as `hiringOrganization`. So agency
  names reach the employer field unless the agency words catch them. That is a finding
  for Task 8, not a fix here (R11, R12; `docs/evidence/option-pack-accuracy-read.md`).
