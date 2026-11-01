# Task 7A, fix round 5 (the last): scoped re-review 6, security half

**Scope.** Range `23d6337..df44221` (6 commits). R5-1 and R5-2 are in `8a485ea`; item 4 is in `c0cd917`, `2fdc3ad`, `be45377` and `df44221`. Files were read with `git show`, and line numbers are at `df44221`. The implementer's report was treated as unverified.

**What I ran (pure, no network, no page fetched, nothing in the repo modified; `.env` and NESSA_HOME were never read, and the tool was never run).**
- `/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/97b1e108-19c9-45e9-9fd3-f372d0f9e9b6/scratchpad/redaction_probe_7.py`, on `df44221` sources extracted with `git archive`, using the backend venv's Python 3.12.12. It covers:
  - probes 4–6 in full;
  - R5-2's forms;
  - apply links on the page and Adzuna paths;
  - image names for question 4.
- A structural check of ledger rows 32–33 as committed.
- A check of the proposed image-extension rule.

**Not run.** pytest, `make check`, `make acceptance` and `make live-adzuna`. The report says they passed or completed; I have not verified that.

## Per-item verdicts

| Item | Verdict | Evidence |
|---|---|---|
| R5-2: JSON links, entity-hidden JSON strings, percent-decoded attributes, `link_detail` | Fixed | **JSON strings.** `_redacted_string` (`redaction.py:117-125`) redacts a string's `unescaped` form (`:109-114`) when that shows a detail. It is idempotent, so `parse_page`'s second pass finds the same literals.<br>**Links and attributes.** `LINK_KEYS` and `link_strings` (`redaction.py:56,163-177`) feed `decoded_holds_detail` (`pages.py:480-486`): entities, then `unquote`, normalised, `redact_shown`; detection only. `_links_show_detail` sets `LINK_DETAIL` (`:497-501,536`; `records.py:141`). Attributes use the same function (`:489-494`). Migration 0026 widens the value CHECK only.<br>**Probe.**<br>- A JSON-LD `url` `mailto:` (plain or entity) and a percent-encoded `sameAs` give `link_detail`; an ordinary https `url` gives none.<br>- An entity email in a JSON-LD description: the body is kept with no `jane` in it, the excerpt reads `…[email removed]…`, and offsets match.<br>- A percent-encoded `href` `mailto:` gives `attribute_detail`.<br>- Every earlier probe case is unchanged.<br>**Tests.** `test_redaction.py:363,374,387`.<br>**ADR.** Decision 4 (`:168-180,193-196`) now drops the percent-encoded limit. |
| R5-1: lowercase label after a spaced dot | Fixed | **Code.** `_DOT_BEFORE_LABEL` and `_DOT_BEFORE_TLD`, with `(?![\w-])` after the TLD (`redaction.py:65-70`): the rule I proposed.<br>**Probe.** Every question 1 shape from re-review 5 is now a non-match on the kept body and the model input. That includes the handle at a sentence end, the handle link followed by a "." node, "@" for "at" before a time or place, and `og:description` and `alt` attributes. All five R4-1 split forms still match.<br>**Tests.** `test_redaction.py:342`, `test_extraction.py:182`.<br>**ADR.** The over-match sentence (`:196-201`) now names only the lowercase-start residue. |
| Item 4: names diagnostic, rename and live run | Fixed | **Diagnostic.** `env_names_containing` (`tools/localenv.py:102-115`) returns only names that fully match `[A-Za-z_][A-Za-z0-9_]*` before an `=` and contain "ADZUNA" (case aside). The blocked summary (`tools/live_adzuna.py:107-113`) prints that list and the two expected names. It never prints a value or any other name, and it makes no request. A theoretical residue: a continuation line of a multi-line quoted value shaped `…ADZUNA…=` would be listed by its name-like prefix; this is negligible. Test: `tests/tools/test_live_adzuna.py:165`.<br>**Run output.** Counts and labels only; leak-scan findings are named by place and `.env` name (`:139-173`).<br>**Rename.**<br>- `ADZUNA_ENV` is `ADZUNA_APPLICATION_ID`/`ADZUNA_API_KEY`, with files `adzuna_application_id`/`adzuna_api_key` (`localenv.py:61-64`). It is shared by setup, the tool (`live_adzuna.py:58,69-70`) and the `NESSA_ADZUNA_CONFIGURED` check (`localenv.py:141`).<br>- The worker's file names match (`nessa/acquisition.py:47-48`), and a contract test binds them (`tests/tools/test_adzuna_credentials.py:55`).<br>- `git grep` finds the old names only in the two tests that prove no alias (`test_adzuna_credentials.py:91`, `test_live_adzuna.py:158-186`).<br>**Ledger rows 32–33.**<br>- They hold scope, purpose, a recorded endpoint with only `what`, `where` and `results_per_page`, status, $0 and count notes.<br>- No `app_id`/`app_key` parameter, and no alphanumeric run of 16 or more characters, in either row or its Markdown line.<br>- I cannot compare against the real values without `.env`, but nothing in their shape can carry one. |
| Apply link holding a detail is never a claim (beyond the ruling) | Correct | **Code.** The check follows `apply_link` on all three paths: `pages.py:374`, `extraction.py:554` (`PERSONAL_DETAILS`) and `adzuna.py:285`.<br>**Probe, page and Adzuna paths.**<br>- Plain, `%40` and `&#64;` emails give no claim.<br>- Ordinary links keep their claim: a `ref=01614960000` ID, a Workday-style path, a `youtube.com/@handle` path, and `utm_source=jobs.example.org`.<br>**Tests.** `test_pages.py:289`, `test_adzuna.py:188`, `test_extraction.py:622`.<br>**Note.** A phone number in a link's query value or path (`?call=0161%20496%200000`) is not detected. That follows the ID rule (`_NOT_INSIDE`) and ADR decision 4's own definition ("not inside a URL"), so it is consistent, not a defect. |

## Question 4: are image names like `logo@2x.png` refused?

`_EMAIL` reads `logo@2x.png` as an address, because `png` passes as a letters-only TLD. The probe showed two outcomes:

| Where the name appears | Result |
|---|---|
| A JSON-LD link (`hiringOrganization.logo`, `image`) | The body is refused (`link_detail`) |
| A percent-encoded attribute (Next.js-style `srcset="/_next/image?url=%2F…logo%402x.png…"`) | The body is refused (`attribute_detail`) |
| A plain `src`, `srcset` or inline CSS `url(…@2x.jpg)` | Not refused. The text pass rewrites the image path to `/assets/[email removed]` in the kept body. This was already so; it is harmless to the evidence. |

**Commonness.**
- On the runtime's kept-class hosts it is uncommon. GOV.UK Frontend names its assets with `-2x`/`_2x`, and GOV.UK's JSON-LD logo and image URLs carry no "@"; the probe's GOV.UK-style `-2x` image triggers nothing.
- On employer careers sites it is common: iOS-style `@2x` names, employer `logo` URLs in JSON-LD, Next.js image URLs. Those reach kept bodies only through the corpus tool's agent classification (Task 7b).

**Tightest fix.** Never read an image file extension as a TLD, in `_EMAIL` and `_SHOWN_EMAIL` both. Put a lookahead before the TLD:

```
(?!(?:png|jpe?g|gif|webp|avif|svg|ico|bmp|tiff?)(?![\w-]))
```

- None of these is a delegated TLD.
- Checked on samples: `logo@2x.png`, `hero@3x.webp`, `icon@2x.svg` and `photo@2x.jpeg` are left alone. `jane@recruit.example`, `hr@northwind.co.uk`, `jane@png.example`, `jane@recruit.pngs` and `a@b.jpg.example` are still removed.
- It also stops the in-place rewrite of plain `@2x` image paths in kept bodies.

## Delta check (`23d6337..df44221`)

**No weakening found.**

| Area | What I checked |
|---|---|
| Redaction | Only `8a485ea` touches `redaction.py`, `pages.py`, `extraction.py` and `adzuna.py`, and each change adds a check or narrows the R5-1 over-match. Every earlier probe result is unchanged or improved: re-review 5's sentence shapes now keep their bodies. |
| `apply_link`, `check_url` | `addresses.py` is untouched. `apply_link` is unchanged and still runs first on every path. |
| Other code | `fetcher.py`, `acquire.py`, `sources.py`, compose and the Makefile are untouched. |
| Adzuna credentials | `be45377` changes only the file-name constants in `nessa/acquisition.py`. Setup's copy (`localenv.place_adzuna_credentials`) changes only its names. |
| Estimate | `22c0f30` is the estimate only. |
| Migrations | 0026 drops and re-adds only `body_not_kept`'s value CHECK. 0014's URL CHECKs and 0020's excerpts-only CHECK stay. |

## New issues

### Critical
None.

### Important
None.

### Minor

**R6-1. An image file name with `@2x` reads as an email address.**
- **Where:** `redaction.py:58,67-70`, through `pages.py:480-501`.
- **What:** As shown in question 4:
  - in a JSON-LD link or a percent-encoded attribute, the body is refused;
  - in a plain attribute or CSS, the image path is rewritten.
  - Nothing leaks.
  - It is not recorded in ADR decision 4's limits; only the implementer's report states it.
- **Fix:** The image-extension lookahead above, with tests for `logo@2x.png` in a JSON-LD `logo`, a percent-encoded `srcset` and a plain `src`. Otherwise, record it as a limit.

**Counts:** 4 of 4 fixed or correct (R5-2, R5-1, item 4, the apply-link extension), 0 partly fixed, 0 not fixed. Delta: no weakening of redaction, `apply_link` or `check_url`. New issues: 0 Critical, 0 Important, 1 Minor.
