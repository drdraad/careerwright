# Task 7 slice 7B — review A (pay, salary floor, UK SOC, datasets, R6-1, web)

Package `review-df44221..04f95cf-A-pay.diff` (4,579 lines), read in ten passes: web and API
schemas; `ashe.py`; `esco.py`/`pay.py`; `releases.py`/`soc.py`/`xlsx.py`/`cli.py`; evidence
(`acquisition.py`, `jobs.py`, `redaction.py`, `store.py`); `exploration.py`/`slate.py`; domain
tests; integration tests; `tools/`; docs. The report was treated as unverified claims. I read
outside the package only for a named risk: `profile/role_evidence.py`, `catalogue/reference.py`,
`reference_store.ashe_benchmarks`, `api/reference_schemas.py`, `evidence/records.py`
(`Salary`), the salary readers in `pages.py`, `extraction.py` and `adzuna.py`,
`tests/architecture/test_boundaries.py`, `tools/setup.py`, the committed mapping-review pack,
ADR 0010, the register rows, and spec section 5 (lines 303–395).

Checks I ran (read-only; nothing in the repository changed):
- SHA-256 of the seven files in `var/datasets/`: each one matches its pin.
- `git ls-files var`: empty. `/var/` is gitignored.
- The import closure of `nessa.acquisition` (the test's own helper): it reaches
  `catalogue.pay`/`ashe`/`xlsx`/`releases`, and no `nessa.profile` module or store (GC8 holds).
- A probe of `job_against_floor` against `salary_from` and `pages._salary` outputs (issue I1).
- A probe of both email patterns on 11 image-name and address forms (R6-1).
- A count over the real SOC index by coded SOC/ISCO pair: 32,435 both coded, 231 neither, 4
  with SOC only. This confirms the report's 32,435 entries and 235 uncoded.

I did not re-run `make check` or `make acceptance`. I made no live call and read no `.env` or
NESSA_HOME.

### Spec Compliance

- ❌ Issues found: the floor treats an open-ended advertised salary ("From £24,000", a JSON-LD
  `minValue` with no `maxValue`, "£24,000+") as if its stated amount were the job's top pay,
  and leaves the job out. That treats unknown pay as below the floor: named risk 2, CLAUDE.md
  "Unknown is never zero or ineligible", JOB-03
  (`backend/src/nessa/evidence/jobs.py:324-328`; I1).
- Named risk 1 (is "applied" honest): ✅ on the slate. The words and counts say what happens:
  "…is applied: 0 left out because their official pay is below it; N kept because no
  reviewed UK occupation code links them to pay data. Unknown pay is never treated as below
  it." (`api/discovery_schemas.py:346-363`). `kept_by_reason` gives the same counts, so the
  floor removes nothing, and says so; no GC6 defect. `limits_not_applied` is fully replaced
  (no remaining reference in code or exports). The committed review pack is empty
  (`catalogue/packs/uk_soc_mapping_reviews.json`), and `modelled_pay_of` returns
  `no_reviewed_mapping` before reading any mapping, so the claim "no suggestion is removed in
  L0" is true. Three wording and doc gaps remain (M1, M2).
- Named risk 2 (unknown and predicted pay are never below the floor; gross, period and source
  stay distinct; modelled pay is distinct):
  - ✅ Predicted pay is kept as `predicted`.
  - ✅ Adzuna pay has `period=None` (`adzuna.py:205`), so it is never compared.
  - ✅ A period is never converted: another period is `period_differs`; a month floor on the
    slate is `period_differs`.
  - ✅ No pay means kept.
  - ✅ An "up to" maximum below the floor is correctly below it.
  - ✅ Modelled pay is its own `basis: modelled` in the API.
  - ❌ A minimum-only salary is left out (I1).
  - Two Minor points: the internal conflation (M6) and a mislabelled reason (M5).
- Named risk 3 (ASHE):
  - ✅ Only four-digit SOC 2020 unit groups and 11 ONS work regions are imported. Every
    figure carries `geography: region` and its region code and name, and is shown only for
    the regions of the person's cities; none is labelled a city.
  - ✅ A withheld value is null with ONS's marker (`x`, `..`, `:`, `-`), never 0. A withheld
    P90 keeps the occupation (`not_published`). `jobs_thousands` is carried.
  - ⚠️ Reliability is carried for the median only (M4).
  - ✅ Nothing is averaged. `ashe_benchmarks` has no aggregate; modelled pay uses one reviewed
    code; the floor uses `all()` over regions.
  - ✅ The rule "P90 below the floor in every region of the person's cities" is applied as
    stated (`pay.py:297-321`). A missing region keeps the occupation, and an empty region
    set returns `no_work_area` first.
- Named risk 4 (UK SOC crosswalks): ✅
  - Every candidate is kept, with `resolution` (`ambiguous`, `title_resolved`,
    `single_candidate` or `no_candidate`) and an unreviewed `proposed_soc_code`.
  - `reviewed` is only possible through the pack, and only for a code among the candidates.
  - ASHE per candidate is labelled "about the unit group, not this occupation, unless the
    mapping is reviewed" (`reference_schemas.py:134`).
  - No occupation gets a precise ASHE salary through its ISCO group.
- Named risk 5 (datasets, R7): ✅
  - Each file is pinned by URL, version, size and SHA-256. Local files match.
  - `tools.setup` calls `datasets.main`, which now walks every pin (`PINNED`). A failure in
    one file continues to the next and exits 1, with the manual step.
  - The files are never committed.
  - Licence and attribution are in each pin, `reference_releases`, `docs/dependencies.md` and
    ADR 0010.
  - The ILO pin is sound: an immutable `raw.githubusercontent.com` path at a full 40-hex
    commit SHA, with size and hash checked before the file takes the pinned name and again
    before import.
  - A redirect is followed only to https on the pinned host (`tools/datasets.py:_next_hop`),
    and the hash still decides.
- Named risk 6 (R6-1): ✅
  - Both patterns (`redaction.py` `_EMAIL`, `_SHOWN_EMAIL`) refuse png, jpe?g, gif, webp,
    avif, svg, ico, bmp and tiff? as a TLD, case-insensitively, only when nothing that
    continues a word follows.
  - My probe: kept unchanged were `/img/logo@2x.png?v=3`, `url(/a/hero@2x.webp)` and
    `logo@2x-dark.png`. Still removed were `careers@acme.co.uk`, and real TLDs that only
    start like an extension (`jobs@acme.gifts`, `hr@shop.tiffany`).
  - The documented residue reproduces as stated: `logo@2x.retina.png` and `x@y.co.jpg` read
    as addresses. That errs safe, and ADR 0009 decision 4 records it.
  - The JSON-LD `logo`, percent-encoded `srcset`, `src` and `srcset` tests exist and assert
    that the body and the path are kept.
- ⚠️ Cannot verify from diff:
  - The `make check` and `make acceptance` results. In particular, that the Storybook and
    Playwright phases ran with `04f95cf`, a one-line hint change made after `make
    acceptance` started on `732af52`.
  - That the six URLs still serve the pinned bytes (no network used).
  - The licence readings (R6, product owner).
  - H-10, which is correctly recorded as "not run — requires human".

### Strengths

- **The floor is a counted, explained hard filter on both paths.** Each kept item has a
  reason. Pagination, `total_jobs` and `city_counts` all exclude what the floor left out,
  and the integration test asserts all three (`test_acquisition.py`). An emptied listing
  says `all_below_salary_floor`, never "none found".
- **Modelled pay is gated in one place.** `reviewed_soc_code` returns a code only for a
  reviewed candidate, and the integration test with a synthetic `MappingReviewPack` shows
  the slate path end to end: `below_salary_floor` appears under "show why".
- **The parsers fail closed.** They check the structure and title of each table, its
  header row, its region names and SOC codes, version strings, duplicate keys and inflated
  member sizes. Pence come from decimal text, never a float. The xlsx reader needs no new
  dependency and refuses a DTD.
- **The full-release integration test fails rather than skips when files are absent.** It
  asserts counts that were counted independently.

### Issues

#### Critical

None.

#### Important

**I1. An open-ended advertised salary is read as its top, so the floor removes vacancies
whose pay is unknown.**
- Where: `backend/src/nessa/evidence/jobs.py:324-328` (`highest_minor_units=max(...)` over
  whichever of minimum and maximum is present); the test at
  `backend/tests/domain/test_jobs.py:308`.
- What: the `Salary` contract writes a single amount as `minimum == maximum`
  (`pages.py:169,171`; `extraction.py:337` `high = low`). A minimum with
  `maximum_minor_units=None` means "from" or "minimum": the upper end is unknown
  (`extraction.py:salary_from`; `pages._salary` for a JSON-LD `minValue` with no
  `maxValue`).
- Reproduced against a £26,000 a year floor; each of these is `(below, None)`, so the job is
  left out of the page, `total_jobs` and `city_counts`:
  - `salary_from("From £24,000 per annum")`;
  - `salary_from("Minimum £24,000 a year")`;
  - `pages._salary({... "minValue": 24000, "unitText": "YEAR"})`.
- Same outcome by another path: 7A's `salary_from("£24,000+ per annum")` reads a single
  £24,000. This slice makes that existing misreading consequential (R11: a probe reproduces
  it).
- The test row `pay(2_500_000, None) -> BELOW  # a single amount is its own top` locks this
  in, but that `Salary` is a minimum-only (open) one, not a single amount.
- Why it matters:
  - It contradicts "unknown or predicted pay is never treated as below the floor" (the
    dispatch, ADR 0010 decision 8, the `ProfileInput.minimum_salary` description) and
    CLAUDE.md's "Unknown is never zero or ineligible".
  - The `all_below_salary_floor` words ("Vacancies with unknown … pay are always kept") are
    then untrue.
  - A hard filter silently narrows the person's market on a guess.
- Fix:
  - When `maximum_minor_units is None`, return `UNKNOWN` with a new reason (for example
    `no_upper_amount`), unless the minimum already meets the floor (then `meets`). Only a
    stated maximum, or a single amount with min == max, can put a job below the floor.
  - Correct the test row and add the "From" and JSON-LD `minValue` cases.
  - Read a trailing `+` after an amount as a minimum in `salary_from`, or refuse it as
    `salary_invalid`, with a test.

#### Minor

**M1. The You chapter's hint promises suggestion screening that L0 cannot do.**
- Where: `apps/web/src/lib/vocabulary.ts:177`.
- What: the hint says "suggestions and vacancies whose stated pay in that period is below it
  are left out". Suggestions have no stated pay. Their rule is official pay through a
  reviewed UK SOC mapping (P90 in every region), and none exists in L0.
- Why it matters: the slate's own sentence then discloses "0 left out … N kept because no
  reviewed UK occupation code links them to pay data", so the floor is not silent and there
  is no GC6 defect. But a person setting the floor is told something that cannot happen yet.
- Fix: for example, "…vacancies whose advertised pay in that period is below it, and
  suggestions whose reviewed official pay is, are left out; Nessa says how many, and why the
  rest were kept."

**M2. Some docs still say the floor is recorded, not applied.**
- `docs/requirements-register.md:130`: the DIV1-06 row, "verified", still says "Confirmed
  limits that need evidence (salary floor) are recorded, not applied".
- `docs/adr/0007-conversation-discovery-and-support.md:61-64`: decision 2 still says the
  slate reports the floor in `limits_not_applied`. The slice updated only that ADR's "Not
  done" list.
- `backend/tools/setup.py:2`: still says "pinned datasets (ESCO)".
- Fix: update each to name `salary_floor` and ADR 0010 decision 8.

**M3. An empty listing hides that sources are still pending.**
- Where: `backend/src/nessa/evidence/acquisition.py:645-648`.
- What: `_empty_reason` returns `all_below_salary_floor` before it checks `sources_pending`.
  An empty page filtered by the floor, while sources are still being fetched, says "Every
  vacancy found advertises less than your minimum salary" and drops the "an answer is still
  coming" state that review B N7 required.
- Fix: check `PENDING` first, or carry both.

**M4. Reliability is the median's only.**
- Where: `backend/src/nessa/catalogue/ashe.py:251-252` keeps only the median's CV from each
  "b" table, although the table has a CV per statistic (same `_HEADER`).
  `api/reference_schemas.py:100` exposes one `reliability` beside every statistic,
  including the P90 the floor compares.
- Why it matters: ONS withholds a statistic whose CV is above 20%, so a published P90 is at
  least "acceptable", but its band can be worse than the median's (spec: "sample
  reliability" is a required qualification).
- Fix: keep each statistic's CV and band, or rename the field `median_reliability`.

**M5. Pay with an unknown basis is counted as "no pay".**
- Where: `backend/src/nessa/catalogue/pay.py:294`.
- What: Adzuna pay whose `salary_is_predicted` is absent (`PayBasis.UNKNOWN`) falls through
  `floor_verdict` to `no_pay` ("no pay stated"), although pay is stated. It is kept either
  way, but the count's reason is wrong.
- Fix: add a `basis_unknown` reason.

**M6. Modelled pay passes through the advertised-pay rule.**
- Where: `backend/src/nessa/catalogue/pay.py:317`.
- What: ASHE P90 figures go through `floor_verdict` as `StatedPay("advertised", …)`. Harmless
  today, but it labels modelled pay "advertised" internally (JOB-05 keeps them distinct), so
  any change to the advertised-pay rule (I1's fix, for one) silently changes the occupation
  rule too.
- Fix: compare the figures with the floor directly.

**M7. The slate sentence never mentions occupations that meet the floor.**
- Where: `backend/src/nessa/api/discovery_schemas.py:352-357`.
- What: the sentence lists left-out and kept-by-reason counts but not `meets`. With a
  reviewed mapping, "N meet it" never appears and the sentence's counts do not add up to the
  considered pool. In L0, `meets` is always 0.
- Fix: add the `meets` count to the sentence.

**M8. The floor sentence has no Storybook state.**
- Where: `apps/web/src/stories/Conversation.stories.tsx:205`.
- What: the stories set `salary_floor: null`, so the visual review package never shows the
  floor sentence. A Vitest case covers its text only.
- Fix: add a story with a floor.

### Assessment

**Spec compliance:** ❌ Issues found (I1)
**Task quality:** Needs fixes
**Reasoning:** The pay, UK SOC, ASHE, dataset and R6-1 work is careful, and "applied" is
honest on the slate. But the vacancy floor reads an open-ended "from £X" or `minValue`-only
salary as its top and leaves the job out. That is unknown pay treated as below the floor,
which the slice's core contract forbids, and a test currently asserts it.
