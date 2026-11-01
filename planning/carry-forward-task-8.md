# Carried into Task 8 (from Task 6 / Sprint 0 critique)
- S0-V07 (Roles part): failure/unknown copy must not push the first listing behind the phone sheet.
- S0-V08 (failed Roles): one filled primary action per view.
- See docs/design/pre-review-sprint-0.md "Open findings" for full text.

# Carried into Task 8 (from Task 7A, ledger "fix round 5")
- MODEL-08: show `acquisition_model_spend` before an acquisition starts. First fix the API's "without a worker crash" figure to min(3 x one reservation, the run limit) per run, so it never exceeds the hard maximum (re-review 3-C, concern 4).
- Cancel's 202 now carries `cancellation_requested` and can answer 202 for a finished acquisition with unsettled extraction runs; the client handles both.
- `model_extraction` states (including `postings_conflicting`, `no_posting_found_by_model`) and `empty_reason` `sources_pending` have words in vocabulary.ts; nothing renders them yet.
- Apply-link `href`s stay https only (the API gives only `apply_link`-checked URLs).
- OI-04 in corpus/manifest.json and the plan still say Adzuna has no credentials; they now exist (ADZUNA_APPLICATION_ID, ADZUNA_API_KEY) and the live qualification passed (ledger rows 32-33).

## From Task 7b (re-review 1)
- N5: on recapture, locate C03's full title with its entity written out ("Adult Nursing &amp; Safeguarding Level 3 Course") so `misleading_course_title` rests on a span, not a note.
- Locate J01's header statement ("£28,000 per annum") on the next capture and keep it as a fact beside the bound.
- Corpus runs: `tools.corpus` paces within one process only — leave a host's rate limit between runs (Task 7b M9, parked for the final review).
- Accuracy-read findings for Task 8 (R11, reproduced): agency names read as the employer on J12, J14, J18, J20 (boards' `hiringOrganization`); J01's JSON-LD single £28,000 vs "Up to"; J19 place conflict; work mode read only from TELECOMMUTE; C04 a course listed as a job.

## From Task 7c fix round 1 (pack 0.2.0)
- Pin pack 0.2.0 (sha256 162d2773…a56). Q290 has no unknown form: J10.1's gate keeps only the registration both page statements require (same NMC gate). J02's link to J01's vacancy stays though the fact behind it is gone (no unknown form). J03's predicted salary is no longer served. Bare "?" answers Q227–Q242 made J02/J03/J07 fields unknown.
- J03's predicted salary (the corpus's one real predicted-pay case) is no longer served in 0.2.0: Task 8 needs another predicted-pay case for its salary-floor tests. J02 stays grouped with J01 as one vacancy though its cited evidence is gone.
