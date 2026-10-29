# ADR 0010: Reference data, the salary floor and the AI Resilience record model

- Status: Accepted for Task 7, slice 7B (Sprint 3: S3.1's ASHE and UK SOC part, the salary
  floor, the reduced S3.6). Decision 4 (the full-time tables), decision 8 (the 90th
  percentile at unit group, kept rather than Table 15 (3)'s broader minor group; advertised
  pay read as gross), decision 7's evidence-quality words (limited, moderate, strong) and
  every licence reading in decision 2 (the ILO scores from the lead author's repository
  included) were **confirmed by the product owner (R6) on 2026-10-29**. They kept the 90th
  percentile knowing that the pinned Table 15 (4) publishes no percentile at region x unit
  group, so with this release the occupation floor can never leave a suggestion out
  (decision 8; fix round 2). Fix round 1 (2026-10-29) amended decisions 4, 7, 8, 9 and 10 as
  marked; fix round 2 decisions 4 and 8.
- Date: 2026-10-29
- Requirements: TAX1-02..07, AIR1-02, AIR1-03, AIR1-04, AIR1-05 (backend), AIR1-07,
  AIR1-10, AIR1-11, AIR1-12, JOB-05, DIV1-07, JOB-03 (the floor's part); spec sections 4, 5,
  17 and 18; rulings R2, R6, R7; plan v1.1 S3.1 and S3.6

## Context

Slice 7A left jobs with advertised and provider-predicted pay, and a confirmed salary floor
recorded but not applied. Spec section 5 asks for an official pay benchmark (ONS ASHE) with
its code, geography, period and reliability; UK SOC 2020, US SOC and O*NET-SOC kept as
distinct namespaces with unresolved alternatives kept; pinned ILO exposure and Anthropic
observed-use imports with a compatible ESCO to O*NET mapping; and an AI Resilience Score
that is a reviewed range or unscored, never a formula. L0 has no accountable reviewer
(H-10), so no real mapping or assessment can be reviewed.

## Decisions

1. **Where it lives.** All of it is market intelligence (spec section 17: "taxonomies,
   regions, role cards, AI resilience methodology/assessments"), so it is in
   `nessa/catalogue` beside ESCO and the city list: `releases.py` (the generic pin),
   `xlsx.py`, `ashe.py`, `soc.py`, `ai_evidence.py` (parsers), `reference_store.py` (the SQL
   adapter, migration 0027), `reference.py` (imports and an occupation's evidence),
   `pay.py` (mapping, modelled pay, the floor) and `ai_resilience.py` (the record model).
   The catalogue imports neither profile nor evidence, so the slate (profile) and the job
   listing (evidence) both use it without a cycle. `nessa/profile/role_evidence.py` joins
   it to a workspace (the person's regions, the pack that applies).

2. **Pinned releases (R7, TAX1-04).** Each file is pinned by URL, size and SHA-256, fetched
   by `make setup` (`tools.datasets`, now every pin) into `var/datasets/`, verified again
   before import, and recorded in `reference_releases` with its version, licence,
   attribution, native code version, transformation version, import time and counts. A
   redirect is followed only to https on the pinned host (Hugging Face answers 307); the
   hash decides. One release of each dataset is held; another is refused, as for ESCO.

   | Dataset | Pinned file (URL) | Bytes, SHA-256 | Licence (read 2026-10-29) |
   |---|---|---|---|
   | ONS ASHE Table 15, 2026 provisional | ons.gov.uk `.../regionbyoccupation4digitsoc2010ashetable15/2026provisional/ashetable152026provisional.zip` | 67,460,310, `fefd20c5…f081` | OGL v3.0 (session 1, line A2) |
   | ONS SOC 2020 Volume 2 coding index, version 14 (2026-08-27) | ons.gov.uk `.../soc2020volume2thecodingindexexcel20260827v2.xlsx` | 3,717,451, `59d3ec71…0b9a` | OGL v3.0 |
   | ILO-NASK GenAI exposure index 2025 (ILO WP 140) | raw.githubusercontent.com `pgmyrek/2025_GenAI_scores_ISCO08/ce5fc25…/Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx` | 2,598,951, `c1940b87…c90a` | CC BY 4.0, ILO attribution and adaptation disclaimer |
   | Anthropic Economic Index 2025-03-27, `task_pct_v2.csv` | huggingface.co `Anthropic/EconomicIndex/resolve/4e5f69f…/release_2025_03_27/task_pct_v2.csv` | 435,372, `0c20f184…97db` | CC BY (no version stated); O*NET content CC BY 4.0 |
   | Anthropic Economic Index 2025-03-27, `onet_task_statements.csv` | the same release | 3,592,256, `82e4c418…97ec` | as above |
   | ESCO to O*NET crosswalk, version 1 (September 2022) | esco.ec.europa.eu `/system/files/2023-08/ONET_%28Occupations%29_0_updated.csv` | 2,986,823, `82179a0a…b620` | Commission Decision 2011/833/EU; O*NET content CC BY 4.0 |

   The ILO's publication page offers only the paper; the occupation scores are published,
   with the ILO's attribution terms, in the lead author's repository, pinned by commit
   (controller-delegated ruling of this slice: the file the paper's own authors publish,
   pinned immutably and hash-checked). Full hashes are in the pins and `docs/dependencies.md`.

3. **A standard-library workbook reader.** ONS and the ILO publish `.xlsx`. `xlsx.py` reads
   a named sheet's cells as text (shared and inline strings, numbers as their decimal
   text), refuses a document type declaration (no entity can expand or be fetched) and any
   member over 64 MiB inflated. No dependency is added.

4. **ASHE, as ONS publishes it (TAX1-06, TAX1-05).** Three tables, gross weekly (15.1),
   hourly (15.5) and annual (15.7) pay, each with its coefficient-of-variation table (the
   "b" file), the "Full-Time" sheet only (R6: a floor usually means a full-time salary), for
   the 412 SOC 2020 unit groups in ONS's 11 work regions: 13,596 estimates. Each keeps its
   code, title, region (with its GSS code: a region, never a city), period, pay definition,
   jobs in thousands, every statistic (median, mean, ten percentiles) in pence, rounded to
   the penny from its decimal text, and ONS's marker (`x` unreliable, `..` disclosive, `:`
   not applicable, `-` negligible) where a value is withheld: null with its marker, never 0.
   Each statistic keeps its own CV from the "b" table and so its own ONS quality band,
   shown beside it, a P90's never the median's (fix round 1, review A M4; migration 0028,
   transformation `nessa-ashe-import-2`, which removes the held ASHE import so
   `setup-database` imports it again). One release is held, so the trend is `unavailable`,
   `single_snapshot`. What this release publishes (fix round 2, re-review 1-A N1, counted on
   the pinned file and pinned in
   `test_reference_data.py::test_the_pinned_files_import_with_their_documented_counts`): at
   region x four-digit unit group, no percentile at all (0 of 135,960 percentile cells, in
   any period); the median for 5,091 of 13,596 estimates, and the mean. Table 15 (3), the
   three-digit minor groups, does publish percentiles; it is not imported.

5. **UK SOC 2020 mapping (TAX1-02, TAX1-03).** ONS's coding index codes each of 32,435 job
   titles to a SOC 2020 unit group and an ISCO-08 group (235 entries without a code are
   counted, not guessed). An ESCO occupation's ISCO group gives every SOC unit group one of
   its titles is coded to (`candidates`, all kept, most titles first); an ESCO label equal to
   an index title of exactly one candidate narrows it (`title_resolved`); otherwise one
   candidate is `single_candidate`, several `ambiguous`, none `no_candidate`. Nothing here
   is reviewed: a mapping is `reviewed` only through an accountable reviewer's decision in
   the committed, dated mapping review pack (`catalogue/packs/uk_soc_mapping_reviews.json`,
   empty until a reviewer exists, H-10), and only when it names one of the candidates.
   Modelled pay exists only through a reviewed mapping, for that one code and the person's
   regions: one ISCO group's ASHE figure is never given to every ESCO occupation in it, and
   no figure is averaged across codes.

6. **AI evidence in native tables (AIR1-11, TAX1-07, AIR1-03).** ILO exposure by ISCO-08 unit
   group (427 groups: the mean and spread of 2025 task scores, 0 to 1, and the paper's
   gradient), O*NET task statements (19,530 tasks of 974 O*NET-SOC 2019 occupations; the
   release does not state its O*NET database release) and each task's observed share of
   Claude conversations (3,364 tasks; the release's "none" row is not a task), and the
   crosswalk's 4,253 rows with their SKOS match types. The bridge from the crosswalk's ESCO
   v1.1.0 to the held v1.2.1 is by URI identity, counted at import (3 rows name occupations
   v1.2.1 lacks; 235 O*NET codes have no task in the release; 43 rows name an ISCO group):
   never matched by title. An occupation shows its ILO group's exposure (labelled the
   group's, technical potential, never a prediction of job loss) and, per O*NET match, how
   many tasks the release lists and observed, with the largest shares as published: never
   summed, never averaged across matches. A task the release did not observe is "not
   observed", never zero and never protection. None of this is a score.

7. **The AI Resilience record model (AIR1-02, AIR1-04, AIR1-07, AIR1-12).** A record is data
   entered through `AssessmentRecord`. Its `origin` decides (fix round 1, review B I2): a
   `model_proposal` never publishes, whatever its decision says; a reviewer who accepts one
   enters it as their own `reviewer_entry`. No code path writes a record: the packs change
   only by a reviewed commit, and the product pack is held empty by a test.
   `publication_failures` checks, deterministically: a reviewer entry; an accountable
   reviewer's decision, which records the bounds it approved, so a record whose bounds
   differ does not publish (review B M1); a reviewed mapping; technological and geographic
   scope; observed supporting evidence; at least two evidence families from at least two
   independent sources (two named sources repeating one study are one), not all of them
   exposure (task exposure and observed use alone are exposure evidence only and keep
   resilience unscored, spec AIR-1 step 4; `exposure_only_evidence`, review B I1); the
   reviewer's grade of the evidence (spec section 18's evidence quality: limited, moderate,
   strong; provisional words, R6; review B M6); contradictions recorded (an empty list is
   "none found", a missing one is not recorded); physical-automation coverage stated; a
   range on the rubric's band edges unless a documented anchor names the integer, and a
   widening reason for a range across bands; no reference point (M1); no seniority or local
   modifier (M0 inherits); a five-year horizon; this method version; a missing observation
   never as protection; a synthetic record labelled. A reviewed null skips the
   evidence-sufficiency checks (it is the reviewer's answer to evidence that cannot support
   a range) and reads `reviewed_null` (review B M2). A withdrawn record, or one a known
   material correction affects (by source or record), is never published. Packs are
   committed, versioned and dated (`catalogue/packs/`), loaded and checked when the API
   starts, before any session, so a correction invalidates what it affects at once; every
   slate and evidence answer names the pack's version and date. The product pack is empty
   (no reviewer, H-10), so every real role is unscored. The fixture pack holds one
   conspicuously labelled synthetic record (data quality specialist, 5-8, with a synthetic
   accountability family bearing protection beside the two exposure families) and applies
   only in the fixture workspace. `synthetic` describes the record, false where a role has
   none (review B M3). The assessment reads only a pack: `ai_resilience` imports no
   evidence table, so no formula can exist. Beside a published range the imported
   evidence's state is `assessed`, never `exposure_only` (review B I1).

8. **The salary floor as a hard filter (DIV1-07, JOB-05; H-11 item 4).** Something is left
   out only when the top of the pay it states, in the floor's period and in GBP, is below
   the floor; unknown, provider-predicted, unknown-basis (`basis_unknown`), other-period
   (never converted), open-ended and unpublished pay is kept, and every case is counted with
   its reason.
   - The slate (the floor of the discovery's pinned answers): an occupation's pay is its
     modelled pay, so only a reviewed mapping can put it below the floor, and then only when
     ASHE's 90th percentile for the floor's period is below it in every region of the
     person's cities (R6: a career most of whose jobs pay less but some pay enough is not
     removed). ASHE's figure is compared with the floor directly, never through the
     advertised-pay rule (fix round 1, review A M6). Left-out occupations say
     `below_salary_floor` in "show why this wasn't included"; `salary_floor` gives the
     counts and a sentence with every count, `meets` included (review A M7). In L0 no
     mapping is reviewed, so the floor removes no suggestion and says why. And it never
     could with this release, a reviewed mapping or not (fix round 2, re-review 1-A N1): the
     pinned Table 15 (4) publishes no percentile at region x unit group (decision 4), so the
     90th percentile is always unpublished and every occupation is kept, after a review as
     `not_published`. The rule is not changed here: a median or mean would remove careers
     where many jobs pay more (DIV1-07), and a minor-group figure from Table 15 (3) would be
     a broad-SOC estimate the spec admits only with an explicit label. Which statistic or
     geography the floor uses is the product owner's decision (R6).
   - The job listing (the current profile's floor; `pay.floor_verdict`): a vacancy is left
     out only when every advertised GBP amount its copies state in the floor's period has a
     top (a range's maximum, an "up to", or one amount) below it. A minimum with no maximum
     ("From £24,000", "Minimum £24,000", a JSON-LD `minValue` alone, and "£24,000+", which
     the span reader now reads as a minimum) is open above: `no_upper_amount`, kept, unless
     the minimum already meets the floor (fix round 1, review A I1). Advertised pay is read
     as gross, as UK adverts state pay (R6). Adzuna states no period, so its pay is never
     below a floor. The page, `total_jobs` and `city_counts` leave out what the floor left
     out; `salary_floor` counts it; a listing the floor empties says
     `all_below_salary_floor`, never "none found", and `sources_pending` first while a source
     is still being read (review A M3). Examples are never filtered.

9. **The AI Resilience filter (AIR1-05, backend part).** `min_ai_resilience` (Any when
   absent, 0 to 10) applies to the lower end of a published range; unscored occupations are
   kept unless `include_unscored` is false, and never read as 0 or 10. On the slate it is a
   view parameter, counted (`ai_resilience_filter`: scored, below the minimum, unscored,
   unscored left out, and `synthetic` when a scored range is the fixture's, whose summary
   then says "synthetic fixture range"; fix round 1, review B M8). It never constrains a
   plan (AIR1-06, T11/T13a).

10. **Contract changes.** New: `GET /v1/workspaces/{id}/occupations/{concept_id}/evidence`;
    the slate's `salary_floor` and `ai_resilience_filter` (replacing `limits_not_applied`)
    and its two query parameters; three `NotIncluded` reasons; the listing's
    `salary_floor` and `EmptyReason.all_below_salary_floor`; the error code
    `REFERENCE_DATA_UNAVAILABLE` (503); migration 0027. `setup-database` imports the six
    datasets after ESCO. Fix round 1: each ASHE statistic's `cv` and `reliability` beside
    it (replacing the benchmark's `median_cv` and `reliability`; migration 0028); the
    floor reasons `no_upper_amount` and `basis_unknown`; `ai_evidence.state` `assessed`;
    `ai_resilience.evidence_quality`; the filter's `synthetic`; the publication failures
    `exposure_only_evidence`, `model_proposal`, `bounds_not_decided`,
    `evidence_quality_not_stated` and `widening_not_explained`; the decision's `lower` and
    `upper`. No workflow's step sequence changes: DBOS `application_version` stays
    `nessa-l0-1`.

## Evidence

`make check`; `make acceptance` (`test_reference_data.py`: the manifests, the import once and
refusal, the pinned files' counts, an occupation's evidence through the API, the fixture
record in the fixture workspace only, modelled pay through a synthetic reviewed mapping;
`test_discovery.py`: the floor and the AI filter on a slate; `test_acquisition.py`: the floor
on vacancies). Domain tests: `test_reference_parsers.py`, `test_pay.py`,
`test_ai_resilience.py`, `test_slate.py`, `test_jobs.py`. No live call was made. Fix round
1 added: open-ended pay as the readers give it (`test_jobs.py`), the occupation rule at its
boundary (`test_pay.py`), each statistic's CV, the floor sentence's counts
(`tests/api/test_floor_words.py`), a pending page the floor emptied, the new publication
checks, a published synthetic range through the slate, the evidence state beside it, and the
evidence endpoint's 503 and 404.

## Consequences and open items

- Not run, requires a human (R2): H-10, every reviewed UK SOC mapping and every published
  AI Resilience record. (The licence readings above, decisions 4 and 8 and decision 7's
  evidence-quality words were confirmed by the product owner on 2026-10-29, R6; the
  occupation floor removes nothing with this release, as they chose.)
- Jobs carry no occupation ID yet (JOB-01's open part), so a vacancy shows its own pay and no
  modelled pay; the Roles chapter that shows an occupation's evidence and the pay lens is
  Task 8.
- One ASHE release and one Economic Index release are held; refreshing either is a reviewed
  migration. Monitoring source releases for corrections is M1; L0 checks the pack's
  recorded corrections at start.
