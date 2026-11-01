# Task 7A, fix round 3: scoped re-review 4, security half (R3-1, R3-2 and the kept-body fail-safe)

**Scope.** Range `1132cf0..dcaac22` (5 commits). My items are in `81f93c2`; I checked the rest of the delta only for any weakening of redaction, `apply_link` or `check_url`. Files were read with `git show`, and line numbers are at `dcaac22`. The implementer's report was treated as unverified. As instructed, entity-encoded details inside attribute values (an obfuscated `mailto:`) are ruled for round 4 and are not raised here.

**What I ran (pure, no network, nothing in the repo modified).** I ran `/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/97b1e108-19c9-45e9-9fd3-f372d0f9e9b6/scratchpad/redaction_probe_5.py` on `dcaac22` sources, extracted with `git archive`, using the backend venv's Python 3.12.12. It covers:
- part A: re-review 3's cases 1–17, including 15 and 16;
- part B: C-I1's four forms (NBSP, a phone split by newlines or `<br>`, a zero-width space, a soft hyphen), each as a literal character and as an entity, on the kept body and on the model input;
- part C: more JavaScript escapes and separator edges.

I also ran one inline-markup check.

**Not run.** pytest, `make check` and `make acceptance`. The report says they passed; I have not verified that.

## Per-item verdicts

| Item | Verdict | Evidence |
|---|---|---|
| R3-1: JavaScript escapes, detection only | Fixed | **Code.** `_ESCAPE` and `_unescaped` (`pages.py:417-442`) decode JSON's escapes and JavaScript's `\xNN`, `\u{…}` (≤ U+10FFFF) and octal. `_holds_escaped_details` (`:444-448`) feeds `block_unredactable`. No JavaScript is parsed.<br>**Probe.** Case 15 (`\x3e`), `\u{3e}`, octal `\076` and `\x40` (an email) all give `block_unredactable`. An escaped backslash before `x3e` is not taken for an escape, which is correct. Case 16 (plain email in JS) is `block_unredactable`, as before.<br>**Wording.** "Any script" in `BodyNotKept` (`records.py:124-133`) and in ADR decision 4 (`:147-158`). Migration 0022's docstring records the 0020 correction; 0020 is untouched.<br>**Test.** `test_redaction.py:346` (`\x`, `\u{}`, octal). |
| R3-2 / C-I1: normalise, then redact, then cut the model input | Fixed | **Code.** `visible_text` (`pages.py:548-557`) is now `redact_text(normalised_text(_plain(text)))`, then the byte cut. `normalised_text` (`:451-456`) collapses every whitespace form and drops what does not print.<br>**Separators.** `_SEP` (`redaction.py:50-53`) adds tab, NBSP, U+1680, U+2000–U+200A, U+202F, U+205F and U+3000, never a line break.<br>**Probe.** None of the ten forms (NBSP character and entity, newline and `<br>` splits, zero-width character and entity, soft hyphen character and entity, two split emails) reaches the model input. A tab and a narrow no-break space now join a number in text; a newline does not.<br>**Tests.** `test_extraction.py:140` (the four forms), `test_redaction.py:317,330`. |
| Kept-body fail-safe (`visible_text_detail`) | Fixed | **Code.** `_shows_detail` (`pages.py:459-464`) normalises the redacted page's visible text and looks again. A hit sets `VISIBLE_TEXT_DETAIL` (`:511-513`), so the body is not kept (`acquire.py`, unchanged path; 0020's excerpts-only CHECK still holds). Migration 0022 widens only the `body_not_kept` value CHECK.<br>**Probe.** The NBSP entity, newline and `<br>` splits, zero-width (character and entity), soft hyphen (character and entity) and split-email forms all give `visible_text_detail`. A literal NBSP is redacted in place, and the body is kept.<br>**Test.** `test_redaction.py:303` (the four forms).<br>**Docs.** ACQ-06 (register:447) and ADR decision 4 (`:147-170`) say exactly this.<br>**Residual.** One markup form the normaliser does not join: R4-1. |

## Delta check (`1132cf0..dcaac22`)

**No weakening found.**

| Area | What I checked |
|---|---|
| Redaction | Only `81f93c2` touched `redaction.py` and `pages.py`, and only as above. Every earlier probe case is unchanged on `dcaac22`. |
| `apply_link`, `check_url` | `addresses.py` is untouched in the range. |
| Extraction | `extraction.py` changes (`b56952b`, `31e35fa`, `dcaac22`) are pay reading, the byte validator, work-mode negation and state. They do not touch the quote check that drops a quote holding a detail, or the use of `apply_link`. |
| Other code | `fetcher.py`, `acquire.py`, `adzuna.py`, `sources.py`, compose and the worker endpoint are untouched. `extraction_runs.py`, `acquisition.py` and `research_schemas.py` changes (`8ce5d2a`, `31e35fa`) add no URL write and no new sealed or kept text. |
| Migrations | 0022–0024 drop and re-add only value CHECKs (`body_not_kept`, `not_run`, `outcome`). 0014's URL CHECKs and 0020's `a_body_not_kept_is_not_kept` stay. |
| Not my scope | 0023's SECURITY DEFINER function is the B and C reviews'. |

**Observed, not a defect.** The fail-safe is conservative:
- It also refuses bodies whose separate table cells read as a number once joined (`<td>0161</td><td>496</td><td>0000</td>`).
- Any inline script with a plain email still gives `block_unredactable`.

Both lose body retention only; nothing leaks.

## New issues

### Critical
None.

### Important
None.

### Minor

**R4-1. An email split by inline markup is neither detected nor redacted.**
- **Where:** `pages.py:275-276,451-464,555`; ADR decision 4 limits (`:166-170`).
- **What.** `_plain` joins every text node with a space, so `jane<span>@</span>recruit.example` normalises to `jane @ recruit.example`. A reader sees `jane@recruit.example`.
  - **Kept body:** `body_not_kept=None`, so the body keeps it (probe).
  - **Model input:** the sealed text sent to the provider keeps `jane @ recruit.example`, or `jane@ recruit .example` for `jane@<b>recruit</b>.example`.
  - Phones split this way are caught, because the inserted space is a separator.
  - **Exposure:** kept bodies (GOV.UK and the National Careers Service in the runtime) and model input for pages without structured data. Excerpts are mostly protected by the quote check, but that check misses the spaced form too.
  - The ADR's list of markup that hides a detail (entities, line breaks, invisible characters) does not name this case, so the docs are not false, only incomplete.
- **Fix:**
  - For detection and the model input, take visible text with inline elements joined without a separator; block elements keep a space.
  - Or detect and redact emails with optional whitespace around `@` and the domain's dots in normalised text.
  - Add the case to the four-form tests, or name it as a limit.

**Counts:** 3 fixed, 0 partly fixed, 0 not fixed. Delta: no weakening of redaction, `apply_link` or `check_url`. New issues: 0 Critical, 0 Important, 1 Minor.
