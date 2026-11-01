# Task 7b re-review 2 (FIX_BASE 46de02d, HEAD 8f61821)

Scoped to round 1's leftovers (M6, M7), N1–N4 and N7, and the last re-cut. N5 and N6 are
carried or parked and not counted.

How I checked:

- **Read-only.** No live call (no fetch, Adzuna or Meta), no subagent, no `.env` or
  `NESSA_HOME`.
- **What I read:** the diff, the committed pack at HEAD, and the J01 and J12 captures in
  scratch.
- **What I ran:** read-only scripts in scratch (`rr/r2`, `rr/r2b`) through the backend's own
  environment. They:
  - diff the round 1 and round 2 packs claim by claim;
  - run `check_pack`, `review_package`, `schema_text` and `dump_pack` against the committed
    files;
  - run `accuracy_read.job_labels` across the pack versions.

**Counts:** 8 items fixed, 0 partly fixed, 0 not fixed. New issues: Critical 0, Important
0, Minor 1.

## Verdicts by item

### M6 leftover: J19's working pattern. Fixed

`J19.working_pattern` is now `{"pattern": "full_time", "hours_per_week": 36}`, against the
excerpt `Full time (36 hours) vacancies available` (pack: `J19.working_pattern`; package
Q315). "Days or nights" is gone.

### M7 leftover: the J01 header note. Fixed

- `J01.salary`'s note again says the header shows "£28,000 per annum", marked "(not yet
  located: Task 8's recapture)".
- The bound is still the label, and `J01.salary_point` is named beside it.
- Locating the header is carried to Task 8, as ruled.

### N1: C04's duration. Fixed

**The flag.** `DurationPart.typical: bool` is required, so no part leaves it unsaid
(`backend/src/nessa/catalogue/option_pack.py:466-467`).

**C04's two facts:**

| Claim | Value | Package |
|---|---|---|
| `C04.duration` | 6–8 months, `typical: true` | "typically 6–8 months", via `tools/option_pack_files.py:155-156` |
| `C04.access_period` (new fact, same span 5809–5904) | at most 12 months (`minimum` null, `maximum` 12), `typical: false` | Q56, "up to 12 months" |

- **The labels list it.** The new fact is in the manifest's C04 `labels.claims`.
- **The table declares the flag:** ADR 0011 decision 13's duration row.
- **The test:** `test_option_pack.py:543-559` pins both values.

### N2: the rate shape. Fixed

- **The field:** `Rate.repayable: bool | None` is required, and null means "the page does
  not say" (`option_pack.py:421`).
- **The values:**
  - C08.support_grant is `repayable: false`, from "which they will not need to pay back".
    The package shows "not repayable".
  - C08's two yearly fees are `repayable: null`.
- **The table:** ADR 0011 decision 13's rate row states the null rule.

### N3: lengths and hours as text. Fixed

**Mapped to shapes** (`option_pack.py:560-564`):

- `access_period` now takes the duration shape.
- `working_pattern` now takes the schedule shape, which gains `flexible`.

**Every working pattern checks out against its excerpt:**

| Pattern | Slots |
|---|---|
| Full time | J05, J09, J11, J13, J15, J17 |
| Full time; nights in the note | J06 ("Full-time available (nights).") |
| Flexible | J10 |
| Full time, 37 hours | J14 ("Full Time 37 hours per week ...") |
| Full time, 36 hours | J19 |

**Access periods:** C10's is 12 months.

**No length or hours remains as free text.** I ran a scan over every text-shaped claim
holding a digit. C03's "Lifetime access" is null; see the new Minor R2-1.

### N4: uncounted occurrences. Fixed

- **The field:** `Claim.occurrences: int | None`, with null meaning "not counted"
  (`option_pack.py:172-175`). ADR 0011 decision 2 says so, naming `J01.salary_point`.
- **J01.salary_point:** the pack now writes `"occurrences": null` for it, and a test pins
  it (`test_option_pack.py:559`).
- **No consumer breaks.** No tool or product module reads `occurrences` as an integer.

### N7: OI-13's places for KAPLAN. Fixed

OI-13 (`corpus/manifest.json:183`) now gives both places for "KAPLAN FINANCIAL LIMITED":
the pack, and "as 'Kaplan', in this manifest's C09 slot (its why)".

### The last re-cut. Fixed

- **The pin matches.** `PINS["0.1.0"]` (`option_pack.py:55`), the manifest's
  `option_pack.sha256` and the file's SHA-256 are all `6ee1134b…99038f`.
- **The files are regenerated.** The committed file is `dump_pack`'s canonical text,
  `check_pack` gives no problems, and the committed schema and package equal
  `schema_text()` and `review_package()`. I checked each offline.
- **It is recorded.** ADR 0011 decision 3 sets "Task 7b fix round 2, the last re-cut" beside
  round 1's, with its list of changes and `format_version` still 1 (`:75-84`).
- **0.1.0 stays declared frozen** from the end of Task 7b. N6, parked, still applies.

## Named checks

1. **C03's lifetime access as null.** Not honest by the format's own definition; see R2-1.
   - **Decision 13 defines null** as "the page withholding or lacking the value". C03's page
     states the value: "Lifetime access", meaning no end.
   - **So null stores a known value as unknown.** The note says "the page states no end",
     which discloses it, but the value contradicts its own note.
   - **It also misleads the package.** Q99 shows "unknown (null)" beside `Lifetime access`.
     The package's rule says yes on an unknown row means "the page does not state it", so
     the correct answer is no. Under the partial-record rule that keeps `option:C03`
     `proposed` because of a format limit, not a label error.
   - **The direction is fail-safe.** Nothing gets an end it does not have.
2. **The 13 new rows.** There are 10 working patterns and 3 access periods, placed by
   record.
   - **Part 1** grows to 67: J05's pattern (Q8) and C04's access period (Q56).
   - **Part 2** grows to 152: C10's (Q86) and C03's (Q99) access periods.
   - **Part 3** grows to 125: the 9 remaining patterns.
   - **The structure holds.** `parts()` is unchanged, the parts test still holds (one part
     per record, part 1 P01 only, no job row in part 2), and each part still closes its own
     gate.
   - **The minutes are right:** 17, 38 and 32, about 86 in all.
3. **The offline accuracy comparison.** Unchanged for every scored outcome.
   - **Against the pack before round 1** (`1c4bc07`): only J12's place differs among the
     scored job labels, and it scores `correct` in both versions against the capture's
     "manchester".
   - **Against round 1** (`46de02d`): no scored job label changed.
   - **Course and funding:** C03 moves from 11 to 10 labelled values and C04 from 13 to 14.
     The course total stays 84 and funding stays 28, as the evidence doc now says.

## New issues

### Critical

None.

### Important

None.

### Minor

**R2-1. C03's "Lifetime access" is a known value stored as unknown** (pack
`C03.access_period`; package Q99).

The duration shape cannot say "no end", so the value is null. That breaks decision 13's
meaning of null, and it turns Q99 into a row the reviewer must answer no. Pack 0.1.0
freezes at the end of this task, so this is the last cheap chance to fix it.

**Fix**, either of these, declared in ADR 0011 decision 13:

- **A declared "no end".** Give the access-period shape a fixed word or flag for it, for
  example `"lifetime"` or `{"unit": …, "unbounded": true}`.
- **A different reading.** Re-word Q99's reading, and have the generator show null claims
  that hold a known no-end as "no end stated (lifetime)" rather than "unknown (null)".

The first keeps the data honest. The second only mends the package.

## Observation (not counted)

The schedule shape has no slot for a time of day or a shift. So J06's "nights", J14's
"7.30am to 5.30pm" and C05's "morning AND afternoon" survive only in their notes. Their
excerpts show all three.

Night shifts can matter to a route, P04's in particular. A `shift` or time-of-day field
would be the fix, if a consumer needs one. This is the same class as re-review 1's note on
C05.
