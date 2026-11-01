# Task 7A, fix round 1: scoped re-review 2, security half (re-review 1 residuals and the delta)

Range `5209825..b24d264` (7 commits). The addendum is in `8c2424e` (migration 0018); part of I-4 is in `07fc4c9`. Files were read at `b24d264` with `git show`. Line numbers are at `b24d264`. The implementer's addendum claims were treated as unverified.

**What I ran (pure, no network, nothing in the repo modified):**
- The redaction probe, run again on `b24d264` sources extracted with `git archive`, using the backend venv's Python 3.12.12:
  - `/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/97b1e108-19c9-45e9-9fd3-f372d0f9e9b6/scratchpad/redaction_probe_2.py`
  - `/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/97b1e108-19c9-45e9-9fd3-f372d0f9e9b6/scratchpad/redaction_probe_3.py`
- One pure `check_url` run on other dot characters.

**Not run:**
- pytest, `make check` and `make acceptance`. The report says both checks passed on b24d264; I have not verified that.
- The deadline probe: the fetcher's deadline code did not change.

## Per-item verdicts

| Item | Verdict | Evidence |
|---|---|---|
| C-1 | Fixed | **Register.** ACQ-06 (register:447) now names the forms removed, the decoded-JSON method, the unlocated-block fail-safe and the limits.<br>**ADR.** Decision 4 (`docs/adr/0009-evidence-acquisition.md:128-149`) states the mechanism exactly: JSON-LD blocks and Adzuna's response are decoded, the HTML around them is redacted as text, IDs and URLs are never redacted. Its limits name HTML entities, "at", spelt-out and split numbers.<br>**Tests.** The escaped and CRLF forms named in C-1 are covered (`test_redaction.py:185,201,232`).<br>**Residual.** The register row is broader than the code for the text-level fallback paths (Minor N-1). |
| I-1 | Fixed | **Code.** `redaction.redact_json` (`redaction.py:100-111`) decodes, redacts every string, and re-serialises only when that changed it, with `</` escaped. Pages use it at `pages.py:418-443`; Adzuna at `acquire.py:269-270`.<br>**Probe.** An email after `\n`: 1 posting, email gone. An email after `>`: 1 posting. Adzuna, email and phone after `\n`: 1 copy, `error=None`, both gone.<br>**Tests.** `test_redaction.py:185` (posting still parses, `</script>` count 1) and `:232` (three Adzuna forms, status SUCCEEDED). |
| I-2 | Fixed | **Code.** Decoded strings have a real newline before the phone (`redaction.py:65-83`).<br>**Probe.** Phone after `\n` in JSON-LD: gone from the text and the claims. Adzuna: gone.<br>**Tests.** `test_redaction.py:185` (`\n`, `\t`, `>` before phone and email) and `:232`.<br>**Residual.** The text-level fallback paths still miss it (Minor N-1). |
| I-3 | Fixed | **Code.** Line endings are normalised before redaction, hashing and parsing (`pages.py:424`).<br>**Fail-safe.** A detail-bearing block that cannot be located sets `unlocated` (`pages.py:431-435`). The body is then not kept, the retention becomes excerpts and the rights status is labelled `body_not_kept:contact_unlocated` (`acquire.py:48,199-205`).<br>**Probe.** A CRLF page with `applicationContact`: name gone, posting parses.<br>**Tests.** `test_redaction.py:185` (CRLF, `b"\r" not in kept`) and `:201` (a raw NUL makes the block unlocatable: no body, label present). |
| I-4 | Fixed | **Code.** A refused candidate is `SearchExcluded(url=None, refused_host=<host text>, reason=ExclusionReason)` (`search.py:118-126,180-186`). Permitted-but-refused and over-the-limit entries keep checked URLs.<br>**Test.** `test_source_search.py:55`: `javascript:` gives `(None, None)` and `10.0.0.2` gives `(None, "10.0.0.2")`.<br>**Residual.** Proposals sealed before this commit are not re-validated (Minor N-3). |
| M-1 | Fixed | **Code.** `NOT_TEXT` (`redaction.py:35-38`: `identifier`, `url`, `sameAs`, `@id`, Adzuna `id`, `redirect_url`, …) is never redacted. Inside a contact, URLs are still redacted (`_contact`, `:85-97`).<br>**Probe.** `identifier.value "0123456789"` survives.<br>**Tests.** `test_redaction.py:185` (`source_job_id == "0123456789"`) and `:232` (Adzuna `id "01234567890"` and its `redirect_url`). |
| M-2 | Fixed | **Code.**<br>- `Admit` takes the seconds left (`fetcher.py:64-65,578-580`).<br>- `Pacer.wait(..., within_s)` (`acquire.py:104-115`) neither reserves a slot nor sleeps when the slot is further away. The hop then fails as a transient `timeout`.<br>- The first host is still admitted with `math.inf`, before the bound starts (`fetcher.py:719`).<br>**ADR.** Decision 3 (`:89-91`) states this exactly.<br>**Test.** `test_sources.py:265`: `slept == []`, nothing sent to the other host. Its last assertion is weak (Minor N-4). |
| M-3 | **Partially fixed** | **Done.** U+3002, U+FF0E and U+FF61 are refused before IDNA (`addresses.py:31,93`), tested at `test_addresses.py:112`.<br>**Still folded.** Nameprep still folds U+2024 (one dot leader) and U+FE52 (small full stop) to ".":<br>- `http://93․184․215․14/` becomes `http://93.184.215.14/` (decoded and allowed);<br>- `127․0․0․1` gives `address_not_allowed`.<br>This is security-neutral, because the decoded address is still checked and connected to. But the docstring (`addresses.py:4-11`) and ADR decision 3 (`:59-64`) say such forms are "refused rather than decoded", and the ruling's "non-ASCII dots" covers them (N-2). |
| M-4 | Fixed | `UNREACHABLE` labels (`test_local_stack.py:202-206`). Any other or empty output fails (`:209-216`), so a probe that did not run cannot pass. The worker is still the positive control. |
| M-5 | Fixed | `test_fetcher.py:550`: the own group's empty `Disallow:` allows, whatever the `*` group says. The probe agrees. |
| M-6 | Fixed | `tools/corpus.py:49,64-66,123-124`: off the requested host, the manifest's class applies and both hosts are named. Test: `test_corpus.py:128` (redirect to an unlisted host: pending review, both hosts named, nothing written). |
| M-7 | Fixed | **Location parts.** Cut to 120, 120, 20 and 60 characters (`pages.py:49,246-261`). Test: `test_pages.py:317`. The probe's 150-character locality now parses.<br>**Worker defects.** A defect inside acquisition is a 200 with a failed, non-transient `internal_error` attempt, recorded against the checked URL only (`acquisition.py:83-101,124-155`). Only a request that does not parse is a 422 (`:135`). Migration 0018 adds the reason to the CHECK.<br>**Test.** `test_acquisition_endpoint.py:78`. |
| Item 10 | Fixed | `apply_link` refuses anything past `MAX_URL_CHARS` = 2,048 (`addresses.py:23,127`). `JobCopy.apply_url` has `max_length` 2,048. Test: `test_pages.py:336` (whole at the bound, no claim one past it). Recorded in ADR decision 5 (`:160-167`). |

## Delta check (5209825..b24d264)

**Security paths:**
- Unchanged in the range: `sources.py`, `sources.json`, `adzuna.py`, `compose.yaml`, `compose.live.yaml` and `service_client.py`.
- Touched only by `783d9b3` (B-*), then `8c2424e`: `fetcher.py`, `acquire.py`, `pages.py` and `records.py`.

**Result: no regression of any A-* item.**

| A-* item | Delta |
|---|---|
| A-C1 | `classify` is unchanged (`acquire.py:198`). The only additions lower retention: the unlocated fail-safe and M-6. |
| A-I1 | `_before_request` is unchanged apart from the M-2 `within_s` path. Denied and API-only hosts are still checked before pacing (`acquire.py:143-151`). |
| A-I2, A-M5 | The robots code is unchanged. `783d9b3` only renamed `http_NNN` to `http_error`, and `http_status` is still set, so the 4xx-allows test still holds. |
| A-I3 | The deadline code is unchanged. |
| A-I4 | Compose is unchanged. The stack probes are stricter (M-4). |
| A-I5 | `_recordable`, `RefusedTarget` and `_reference_url` are unchanged. The 0014 CHECKs are not dropped by 0016, 0017 or 0018 (0018 drops and re-adds only `attempt_reasons_are_labels`, now with `internal_error`). No new URL-named API field. With I-4, A-I5 is now fixed. |
| A-M1, A-M2 | `addresses.py` is only extended. |
| A-M3 | `without_app_id` still runs before redaction (`acquire.py:269`). `redirect_url` is in `NOT_TEXT`, so it is kept exactly as stripped. |
| A-M4 | `Claim._bounded` and the title and employer cuts are unchanged. |
| A-M6 | Pasted-text redaction is unchanged. Pages and Adzuna are now redacted in decoded form (above). |
| A-M8 | `do_POST` is unchanged. |
| A-M9 | The value scan is unchanged. |

**The two acceptance expectations changed in b24d264:**
1. `test_live_smoke_ledger.py:217`: strengthened. The substring check became exact JSON fields, plus new assertions on `excluded`, `source_hosts` and no `https://` in the notes.
2. `test_local_stack.py:509,660,697`: still an exact set, updated to `{internal, acquisition}` to match the A-I4 compose change.
   - Not weakened. "No route out" now also relies on the `acquisition` network being `internal: true` (`compose.yaml:203-204`), which this test does not inspect.
   - The demo-mode probe test shows the worker has no route out directly.
   - Optionally, assert the network's `Internal` flag here.

**Probe on b24d264.** Every earlier case now passes:
- emails and phones after escapes, in JSON-LD and Adzuna;
- CRLF contacts;
- a long locality;
- a leading-zero ID;
- the robots edge cases;
- span offsets in a rewritten block that escapes `<\/script>`: 1 closing tag, offsets match.

Cases 10–13 found the residuals in N-1.

## New issues

### Critical
None.

### Important
None.

### Minor

**N-1. The text-level fallbacks still miss a detail right after a JSON escape.**
- **Where:** `pages.py:123-124,431-443`, `redaction.py:108-110`, register:447.
- **What:** Four paths, from the probe:
  - **(a) An unlocated JSON-LD block's claims.** They come from the text-level-redacted block. Its pointer excerpt keeps the phone: `"Call:\n07700 900123 or [email removed]"` (`redaction_probe_3.py` case 10). The body is not kept.
  - **(b) Inline JSON in other script elements**, such as an app-state `<script type="application/json">`. It is redacted as text, so the phone stays in the kept body (case 11).
  - **(c) A JSON-LD block that is not valid JSON.** It stays in the kept body (case 13).
  - **(d) A duplicate key.** The decoded values are unchanged, so the raw block, with its shadowed value, is kept (case 12).
- **Exposure:** In the runtime, bodies are kept only for GOV.UK and the National Careers Service (manifest), plus agent-classified corpus pages.
- **Wording:** ACQ-06 says "JSON in its decoded values (so details after `\n`, `\t` or `>` escapes go…)", which is broader than the code: only JSON-LD blocks and Adzuna's response are decoded.
- **Fix:**
  - Build claims from `redact_value`'d data in `parse_page`.
  - Decode-redact every script whose content parses as JSON.
  - Treat an undecodable JSON-LD block whose text-level redaction changes it like an unlocated one.
  - Detect duplicate keys (`object_pairs_hook`) and always re-serialise.
  - Otherwise name these paths in ACQ-06 and the decision 4 limits.

**N-2. The M-3 residual: nameprep still folds U+2024 and U+FE52 to ".".**
- **Where:** `addresses.py:4-11,31,93`, ADR `:59-64`.
- **What:**
  - `http://93․184․215․14/` is decoded to `93.184.215.14` and allowed.
  - `127․0․0․1` is refused only by the address check.
  - This is security-neutral, but the docstring and the ADR say "refused, never decoded".
- **Fix:** Refuse any non-ASCII host character whose NFKC form contains an ASCII digit or ".". This covers both characters and any others.

**N-3. Search proposals sealed before 07fc4c9 are not re-validated.**
- **Where:** `search.py:122`.
- **What:** `SearchExcluded.url` has no validator, so a proposal sealed earlier, with a raw `javascript:` value in `url`, still validates in `search_view` and is served.
- **Fix:** A validator that keeps `url` only when it is a checked http(s) URL, and otherwise moves the host to `refused_host`.

**N-4. The M-2 test's last assertion cannot fail.**
- **Where:** `test_sources.py:265` (last line).
- **What:** `pacer.wait(..., within_s=0.0) is False` holds whether or not a slot was taken: the next slot is at 105 or 110, and both are more than 0 seconds away.
- **Fix:** Assert `pacer.wait("jobs.other.example", 5.0, within_s=5.0)` returns True with `slept == [5.0]`, which proves the original slot is unchanged.

**Verdict: open: M-3** (partially fixed, security-neutral), plus the Minor new issues N-1 to N-4

Counts: 12 fixed, 1 partially fixed, 0 not fixed. Delta: 0 regressions; both b24d264 expectation changes not weakened. New issues: 0 Critical, 0 Important, 4 Minor.
