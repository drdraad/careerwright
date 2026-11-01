# Task 7A, fix round 2, part 1: scoped re-review 3, security half (re-review 2 residuals)

**Scope:** Part 1 is `b24d264..dc8dd4d` (4 commits); the A items are in `dc8dd4d`. Part 2 (`dc8dd4d..1132cf0`) was checked only for whether it weakens a part 1 security fix: redaction before hashing and sealing, `apply_link`, or `check_url`. Files were read with `git show`. Line numbers are at `dc8dd4d` unless marked HEAD (`1132cf0`). The implementer's report was treated as unverified.

**What I ran (pure, no network, nothing in the repo modified):**
- The redaction probe, on `dc8dd4d` and `1132cf0` sources extracted with `git archive`, with the backend venv's Python 3.12.12: `/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/97b1e108-19c9-45e9-9fd3-f372d0f9e9b6/scratchpad/redaction_probe_4.py`. It holds re-review 2's cases 1–13 on the new API, plus inline-script cases 14–17 and the N-2 hosts.
- One `visible_text` check on `1132cf0`.

**Not run:**
- pytest, `make check` and `make acceptance`. The report says all three passed on `1132cf0`; I have not verified that.

## Per-item verdicts

| Item | Verdict | Evidence |
|---|---|---|
| N-1 (a) claims from redacted values | Fixed | `pages.py:486`: `parse_page` builds claims from `redact_value(json.loads(raw))`, so a pointer-cited block's excerpts are redacted.<br>Probe case 10 (raw NUL, phone after `\n`, contact): `unremovable=contact_unlocated`, phone not in the claims.<br>Test: `test_redaction.py:201`. |
| N-1 (b) every JSON script decode-redacted | Fixed | `redact_page` walks every `script` (`pages.py:433-466`, `:444`), JSON-LD or not.<br>Probe case 11 (`__NEXT_DATA__`, phone after `\n`): gone from the kept text.<br>Test: `test_redaction.py:245` (app-state JSON, phone and `<b>` email; still JSON). |
| N-1 (c) an undecodable block that holds details | Fixed | A script that is not JSON and holds a detail, looked for with JSON-style escapes decoded (`pages.py:411-422,452`), sets `BLOCK_UNREDACTABLE` (`:462`). The body is then not kept and the reason goes in the typed `body_not_kept` column (`acquire.py:200-203`; 0020 CHECK: only with excerpts).<br>This goes beyond the ruling: it covers any script, so a JS assignment such as `window.__STATE__` with `\n07700…` is also caught (probe case 14).<br>Probe case 13: `block_unredactable`.<br>Test: `test_redaction.py:259`. |
| N-1 (d) duplicate keys | Fixed | `redaction.loads_json` uses `object_pairs_hook` (`redaction.py:100-110`). A repeated key always re-serialises (`:124`).<br>Probe case 12: the shadowed phone is gone.<br>Test: `test_redaction.py:268`. |
| N-1 wording | Fixed (Minor residual R3-1) | ADR decision 4 (`docs/adr/0009-evidence-acquisition.md:137-151`) and ACQ-06 now say what the code does: every JSON script decoded, `contact_unlocated` and `block_unredactable`, claims from decoded values.<br>Residual: "looked for with the escapes decoded" (`:147`) is true for JSON-style escapes only (R3-1). |
| N-2 | Fixed | `_folds_to_address` (`addresses.py:93-100,103`): a non-ASCII character that is a digit, an IDNA dot, or whose NFKC form holds an ASCII digit or "." is refused.<br>Probe: U+2024, U+FE52 and U+2488 give `host_not_allowed`; `café.example` still passes.<br>Tests: `test_addresses.py:106-108,117`. ADR decision 3 (`:61-66`) is exact. |
| N-3 | Fixed | `SearchExcluded._only_checked_urls`, `model_validator(mode="before")` (`search.py:128-142`): on every read, a `url` is kept only as `check_url`'s normalised form; otherwise `url=None` and the host goes to `refused_host`.<br>Test: `test_source_search.py:105` (sealed `javascript:` gives `(None, None)`, `10.0.0.2` gives `(None, "10.0.0.2")`, LinkedIn is normalised). |
| N-4 | Fixed | `test_sources.py:291-292`: `pacer.wait("jobs.other.example", 5.0, within_s=5.0) is True` and `slept == [5.0]`. A taken slot would be 10 s away, so the call would return False. |

## Delta check

**Part 1's other commits:**
- `de6ada8` touches `acquire.py` only for B N1's `_adzuna_extraction` label.
- `48a75e5` and `06611ce` touch no security path.
- In `dc8dd4d`, B N4, N5 and N6 only add:
  - a typed `body_not_kept` column, held by a CHECK to excerpts-only rows;
  - restrictive RLS policies.
- Migrations 0019–0021 drop none of 0014's URL CHECKs (`target_urls_are_http`, `attempt_urls_are_http`, `a_target_is_a_url_a_refusal_or_a_query`).
- **No A-* regression.**

**Part 2 (`dc8dd4d..1132cf0`), limited to the three named checks:**
- **Unchanged:** `redaction.py`, `addresses.py` (so `check_url` and `apply_link`), `fetcher.py`, `adzuna.py`, `sources.py`, `compose*.yaml` and the worker endpoint. `redact_page` and the claim-building in `parse_page` are unchanged; Part 2 adds `visible_text` and renames `_conflicts`.
- **Probe:** identical on `1132cf0` for every case.
- **Redaction before hashing and sealing:**
  - The page body is still redacted before it is hashed, parsed and sealed (`acquire.py`, HEAD).
  - The new model input is `visible_text(redacted text)` (`pages.py:504-513` HEAD). It is hashed and sealed as the run input (`extraction_runs.py:99-107` HEAD), and erased when the run settles.
  - Model claims pass the quote check, which drops any quote that holds a detail (`extraction.py:391` HEAD, `PERSONAL_DETAILS`).
  - One ordering gap remains: R3-2.
- **`apply_link`:** model apply links go through it (`extraction.py:483` HEAD). Part 2 adds no other URL write.
- **`check_url`:** Part 2 adds no fetch or URL record.
- **Verdict on Part 2:** it does not weaken a part 1 fix. R3-2 is a new path with one ordering gap.

## New issues

### Critical
None.

### Important
None.

### Minor

**R3-1. JavaScript-only escapes still hide a detail in a kept body, and three descriptions are narrower than the code.**
- **Where:** `pages.py:411-422`, ADR `:147`, `records.py:100-105`, migration 0020's docstring.
- **What:**
  - `_holds_escaped_details` decodes only JSON escapes (`\uXXXX`, `\n`, `\t`, …).
  - Probe case 15: a JS string such as `"Call:\x3e07700 900123"` gives `unremovable=None`, and the phone stays in the kept body. JS `\u{…}` and octal escapes behave the same way.
  - Exposure: kept bodies only. In the runtime that is GOV.UK and the National Careers Service, plus agent-classified corpus pages.
  - `BodyNotKept`'s comments and 0020's docstring still say "a JSON-LD block", but the code applies to any script.
- **Fix:**
  - Decode `\xNN`, `\u{…}` and octal escapes in `_holds_escaped_details`, or treat any non-JSON script with a backslash-escaped digit run as unredactable.
  - Correct the three descriptions.
- **Related, not a defect:** any inline script that holds a plain email now drops body retention (probe case 16). This is conservative, and the email was already redacted.

**R3-2. Part 2's `visible_text` redacts before it collapses whitespace, so a number written with non-breaking spaces reaches the sealed model input in standard form.**
- **Where:** `pages.py:510-512` HEAD, ADR decision 15 (HEAD `:333-336`, "personal details removed again, whitespace collapsed").
- **What:**
  - `0161&nbsp;496&nbsp;0000` and `07700 900123` survive `redact_text`, because `[ .-]` holds no U+00A0. They then become `0161 496 0000` and `07700 900123` in the hashed text that is sealed and sent to the provider (check on HEAD).
  - Mitigations:
    - the source form is a recorded limit ("split by other characters");
    - quotes that hold the number are dropped, so no claim or excerpt keeps it;
    - the input is erased when the run settles.
  - The test at `test_extraction.py:103` uses plain spaces, so it does not cover this.
- **Fix:**
  - Collapse whitespace first, then `redact_text`, then cut.
  - Optionally let `_PHONE`'s separators be `[\s.-]`, so bodies are covered too.
  - Add a nbsp case to the test.

**Counts:** 4 of 4 items fixed (N-1, N-2, N-3, N-4; N-1 checked in five parts, all fixed), 0 partly fixed, 0 not fixed. Delta: 0 regressions, and Part 2 weakens no part 1 fix. New issues: 0 Critical, 0 Important, 2 Minor.
