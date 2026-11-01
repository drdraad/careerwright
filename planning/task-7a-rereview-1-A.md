# Task 7A, fix round 1: scoped re-review, security half (A-*)

Range `5c5e5bb..5209825` (7 commits). Files were read at `5209825` with `git show`, never from the working tree. Fix report not yet written, so the verdicts rest on the code and tests only. Line numbers are at `5209825`.

**What I ran (no network, no live call, nothing in the repo modified):**
- One pure probe, `/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/97b1e108-19c9-45e9-9fd3-f372d0f9e9b6/scratchpad/redaction_probe.py`. It covered redaction, parsing and robots edge cases.
- One pure `check_url` call, on Unicode full stops.
- Both ran on the `5209825` sources, extracted with `git archive` to the scratchpad, using the backend venv's Python 3.12.12.

**Not run:**
- pytest.
- The earlier deadline probe. The new bound in `fetcher.py:121-250` leaves no doubt, and the new tests cover the trickle and 1xx cases.

## Per-item verdicts

| Item | Verdict | Evidence |
|---|---|---|
| A-C1 | Fixed | **Code.** `sources.py:104-112`: class from the final host's manifest entry only. `pages.py` no longer returns `hiring_hosts`. `acquire.py:182` classifies the final host. A page's `hiringOrganization` still gives the cited employer claim and `advertiser` (`pages.py:289-297,363`), as the ruling allows; it never touches retention. No untrusted page input reaches `classify`. A redirect can change the final host, but the page is then actually fetched from, and admitted for, that host.<br>**Agent override, both directions.** It is applied before anything is kept (`tools/corpus.py:47-68`). Raising: `test_corpus.py:57`. Lowering a listed page to `job-board` or `other`: `:86`. Never past a listed host: `:110`.<br>**Hostile-page tests**, through `acquire_page` against the controlled server (`test_sources.py:145`): own host, `co.uk`, `github.io`, Reed naming itself. Plus `:263`.<br>**Docs.** ADR decision 4 is corrected. One residual: the classification applies to a redirected host (Minor M-6). |
| A-I1 | Fixed | **Code.** `fetcher.py:562-578` runs before every hop's request: the address, then `admit` the first time the visit reaches a host, then that hop's origin's robots.txt. `admit` (`acquire.py:124-138`) applies the manifest access, then the pacer. The robots.txt request shares the visit, so its redirects are admitted too (`fetcher.py:683-688`). A refusal keeps the redirects so far and the final URL (`fetcher.py:510-518`).<br>**Tests.** `test_sources.py:205`: `lnkd.in`→linkedin `source_denied` and an API-only host, `redirects == [target]`, only `/robots.txt` and `/abc` requested. `:221`: other origin's robots.txt disallows, page never requested. `:238`: pacing of the second host. `test_fetcher.py:573`: same origin.<br>**Docs.** ACQ-06 is corrected (register:447). |
| A-I2 | Fixed | **Code.** `fetcher.py:316-406`, pure, no dependency:<br>- groups chosen by token, case-insensitive, else `*`, combined;<br>- longest match, with allow winning a tie (`(len, allow)` ordering, `:372`);<br>- `*` and a final `$` (`:335-354`, iterative, O(n·m));<br>- percent-encoding normalised (`:316-332`; `%2F` stays reserved);<br>- an empty `Disallow` adds no rule but closes the group (`:397-400`).<br>**Tests.** The reviewer's four cases (`test_fetcher.py:498`), equal-length allow (`:517`), group selection (`:548`) and encoding (`:498` "encoding").<br>**Unreachable robots.txt**: no page request (`:453`, paths `["/robots.txt"]`; `:465`).<br>**Probe.** Empty `Disallow` allows, an own-group empty `Disallow` beats `*` `Disallow: /`, `/café` matches `/caf%C3%A9`. An empty `Disallow` is untested (Minor M-5). |
| A-I3 | Fixed | **Code.** One deadline per visit (`fetcher.py:715-721`), held in every phase:<br>- resolve on a thread not waited past (`:121-139`);<br>- each connect `min(connect, remaining)`, at most `MAX_ADDRESSES=4` tried after all answers are checked (`:232-250`);<br>- `_BoundedStream` bounds every read, write and `start_tls` (`:142-181`), so the status line, headers and endless 1xx are bounded;<br>- a deadline check before each request (`:596-598`).<br>**Tests.** `test_fetcher.py:338`: trickled status line and endless 1xx with `total_s=1`, asserting `elapsed < 2`. `:359`: hung lookup.<br>**Docs.** ACQ-02 (register:443) is accurate. The ADR decision 3 pacing wording is imprecise (Minor M-2). |
| A-I4 | Fixed | **Compose.**<br>- `compose.yaml:141-144`: `acquisition` is on `networks: [acquisition]` only (`internal: true`, `:203-204`).<br>- `worker` is on `[internal, acquisition]` (`:111`).<br>- `compose.live.yaml:8-10`: `worker [internal, acquisition, egress]`, `acquisition [acquisition, egress]`. It is off `internal` in both modes, and nothing else is on `egress`.<br>**Stack probes.** `assert_only_the_worker_reaches_acquisition` (`test_local_stack.py:199`) runs in demo (`:209`) and live (`:264`). api, web, auth, edge and postgres are probed; the worker is the positive control.<br>**Docs.** ACQ-05 and ADR decision 1 are accurate. The probe's negatives are weak (Minor M-4). |
| A-I5 | **Partially fixed** | **Fixed fields.**<br>- Redirect targets are checked before they are recorded (`fetcher.py:409-419,521-528`; test `test_fetcher.py:107` with `javascript:`/`data:`/`file:`, now `redirects == ()`).<br>- Refused submissions become `RefusedTarget` with refusal and host as text (`acquisition.py:136-166,230-241,731-739`).<br>- A pasted `source_url` is checked or gives 422 (`:275-285`).<br>- Migration 0014 adds CHECKs and cleans old rows; NULL semantics are correct.<br>- Tests: `test_acquisition.py:210,456` and `test_migrations.py:276`.<br>**Still open.** `SearchExcluded.url` (`search.py:91-93,133`), served as `SearchOut.proposal.excluded[].url` (`research_schemas.py:299`), keeps the model's raw candidate text for a refused URL, `javascript:` included (Important I-4). |
| A-M1 | Fixed | `%` refused in literals (`addresses.py:80`), `is_site_local` (`:74`). Tests: zone IDs and `fec0::1` (`test_addresses.py:105,144`), https→http (`test_fetcher.py:128`). |
| A-M2 | Fixed | Non-ASCII digits are refused before IDNA (`addresses.py:90`). The test names each refusal (`test_addresses.py:105`). Docstring corrected. Nit: Unicode full stops are still folded (Minor M-3). |
| A-M3 | Fixed | `adzuna.without_app_id` (`adzuna.py:104-130`) strips app-id-valued parameters from `redirect_url`, and any other occurrence, before hashing or parsing (`acquire.py:245-246`). The live qualification fails on any stored credential (`live_adzuna.py:121-128`). Tests: `test_adzuna.py:138`, `test_live_adzuna.py:74`. |
| A-M4 | Fixed | `Claim._bounded` (`records.py:175,189-193`); title and employer at 200 (`pages.py:361-362`, `adzuna.py:224,234`); a too-long ID is left unknown. Test: `test_pages.py:263`.<br>**Two notes:**<br>- The apply link is exempt. This deviates from the ruling's literal "every Claim string value" and is documented in ADR decision 5, so the controller should accept or reject it.<br>- A pre-existing raise path for long location parts remains (Minor M-7). |
| A-M5 | Fixed | `fetcher.py:689-699`: FAILED `robots_unreachable`, transient, not cached, no page request. Test: `test_fetcher.py:465`. |
| A-M6 | **Partially fixed** | **What is right.**<br>- Redaction runs before hashing, parsing and sealing (`acquire.py:177-180,246`; pasted text `acquisition.py:316-322`), so span offsets index into the kept text and cannot be broken (asserted in `test_redaction.py:107`).<br>- `retrieved_sha256` is kept separately (migration 0015, `acquire.py:195,256`).<br>- The names-in-running-text limit is recorded in ADR decision 4 (`:130-132`) and not claimed solved.<br>**But (probe-confirmed):**<br>- Redaction of raw JSON text breaks JSON-LD and Adzuna JSON (I-1).<br>- Phones after a JSON escape survive (I-2).<br>- Contact blocks on CRLF pages are silently skipped (I-3).<br>- ACQ-06 and ADR decision 4 overclaim (C-1). |
| A-M8 | Fixed | `acquisition.py:145-150`: 400 `invalid_content_length` before reading. Test: `test_acquisition_endpoint.py:51` (`-5`, `abc`, `1e3`, `+4`, Arabic-Indic digit), and `:61`. |
| A-M9 | Fixed | A value scan of `/proc/*/environ`, `cmdline` and every readable file, with needles on stdin and only paths printed. The worker is the positive control (`test_local_stack.py:309-380`, test `:365`). |

**Register and ADR rows:**
- ACQ-02 (register:443): accurate.
- ACQ-05 (register:446): accurate.
- ADR decision 1: accurate.
- ADR decision 3: accurate except two imprecisions (M-2, M-3).
- ACQ-06 (register:447): its redaction clause overclaims (C-1). All its other clauses are accurate.
- ADR decision 4: its C1 correction is accurate. Its redaction paragraph overclaims (C-1).

## New issues

### Critical

**C-1. ACQ-06 and ADR 0009 decision 4 overclaim the redaction.**
- **Where:** `docs/requirements-register.md:447`, `docs/adr/0009-evidence-acquisition.md:121-132`.
- **What:**
  - ACQ-06 says contact details are removed "so no kept body, excerpt or claim holds them".
  - Decision 4 says "every telephone number in UK national or international form" and "in JSON-LD every name, email, telephone and fax number of an `applicationContact` or `contactPoint`".
  - Both are false for ordinary inputs. A phone at the start of a line inside a JSON-LD or Adzuna description is kept (I-2), and a CRLF page keeps its JSON-LD contact names in the body (I-3).
  - The tests use plain-text forms only.
- **Severity:** Critical as an overclaim, by this dispatch's calibration. It follows from the code defects below, not from a knowing claim.
- **Fix:**
  - Fix I-1 to I-3, preferably.
  - Otherwise narrow both texts to what holds.
  - Either way, add the escaped and CRLF forms to `test_redaction.py`.

### Important

**I-1. Redacting raw JSON text breaks the JSON, so postings are lost and a whole Adzuna page fails with the wrong label.**
- **Where:** `redaction.py:30,52`, `pages.py:420`, `acquire.py:246`.
- **What:** `redact_text` runs over the JSON-LD script text and Adzuna's raw response.
  - When an email follows a JSON escape (`\n`, `\t`, `>`, i.e. an email at the start of a line or paragraph), the email pattern also takes the escape's letters. That leaves an invalid escape such as `\[email removed]`.
  - Probe, a JSON-LD description `"Send your CV to:\njane.smith@recruit.example"`: `postings=0`, `issues=['jsonld_invalid']`. The same happens with `<p>jane…`.
  - Probe, Adzuna: the same in one description gives `copies=0`, `error=response_invalid`. The whole page fails, reported as Adzuna's fault.
- **Fix:**
  - Redact decoded string values, not raw JSON.
  - For each JSON-LD block: `json.loads`, apply `redact_text` to every string (with the contact removal), then re-serialise. Escape `</` when re-serialising, so a `<\/script>` cannot close the block.
  - Do the same on Adzuna's parsed JSON.
  - Redact HTML outside the script blocks as text.
  - Test with `\n`- and `>`-prefixed emails.

**I-2. A phone after a JSON escape is not removed.**
- **Where:** `redaction.py:32-38`.
- **What:** The look-behind `(?<![\w/=?&#%.+-])` sees the escape's last character (`n`, `t`, `E`, `0`) as a word character.
  - Probe: JSON-LD description `"Call us:\n07700 900123"` yields "phone kept in text: True".
  - It stays in the kept body and, within the first 200 characters, in the description's excerpt. Adzuna JSON behaves the same way.
- **Fix:** As I-1, since decoded strings have a real newline there. Test the escaped forms.

**I-3. A JSON-LD contact block on a CRLF page is silently not redacted.**
- **Where:** `pages.py:410-414`.
- **What:**
  - lxml returns the script text with LF line endings, so `text.find(raw, cursor)` misses the CRLF original and the block is skipped (`continue`).
  - Probe: the same posting with `applicationContact.name` gives "contact name kept: True" with CRLF and False with LF. The posting still parses, through pointer spans.
  - Emails and phones in the block are still caught (unless I-2 applies); names are not.
- **Fix:**
  - Normalise line endings in the decoded page before redaction and parsing. Kept bodies are already re-encoded, so the hash and spans stay consistent.
  - Alternatively, treat a contact-bearing block that cannot be located as unredactable: never keep the body.
  - Test CRLF.

**I-4. The search proposal still serves unchecked URLs in a URL-named field.**
- **Where:** `search.py:133`, model `:91-93`, API `research_schemas.py:299`.
- **What:**
  - A candidate that fails `check_url` is kept as `SearchExcluded(url=<raw model text>)` and served as `proposal.excluded[].url`.
  - Model output follows search results, which are untrusted pages, so `javascript:` reaches an API URL field.
  - This is the I5 defect class. ACQ-01 (register:442) now says "only checked http(s) URLs in URL fields".
- **Fix:**
  - Record such a candidate by its refusal and its host as text, never as `url`, the same as a refused target. A checked URL may stay as `url`.
  - Test it with `javascript:`.

### Minor

**M-1. A 10- or 11-digit identifier with a leading zero is redacted as a phone.**
- **Where:** `redaction.py:36`, `pages.py:275-287`.
- **What:** Probe: `identifier.value "0123456789"` becomes `source_job_id "[phone removed]"`. Two such postings from one provider then share the source key `(provider, "[phone removed]")` (`jobs.py:155`), which risks a wrong merge.
- **Fix:** With I-1, redact description and contact strings only, never ID or URL fields.

**M-2. A later host's pacing is not bounded by the deadline.**
- **Where:** `acquire.py:135`, `fetcher.py:573-577,596-598`, ADR `:84`.
- **What:**
  - `pacer.wait` sleeps in full inside the visit. The hop then fails as a timeout, so a page fetch can exceed 20 s by the queue wait (interval × waiting requests for that host).
  - ADR decision 3 says the 20 s holds "later hosts' pacing included, enforced in every phase".
- **Fix:** Pass the remaining time to admission and refuse as a transient timeout, without sleeping or reserving a slot, when the wait would pass the deadline. Otherwise reword the ADR.

**M-3. "Never decoded" is not exact.**
- **Where:** `addresses.py:4-11` docstring, ADR `:58-63`.
- **What:** IDNA folds Unicode full stops. `http://93．184．215．14/` becomes `http://93.184.215.14/`, and `127。0。0。1` gives `address_not_allowed`. This is security-neutral: the decoded address is still checked and connected to.
- **Fix:** Refuse non-ASCII dots before IDNA, or reword.

**M-4. The reach probe's negatives accept any output that is not "connected".**
- **Where:** `test_local_stack.py:188-204`; `Stack.exec` uses `check=False`.
- **What:** A probe that did not run (empty stdout) passes as "unreachable".
- **Fix:** Assert each negative is a known failure label (for example `gaierror`, `ENOTFOUND`, `ConnectionRefusedError`, `timeout`, `blocked`).

**M-5. An empty `Disallow:` is untested.**
- **Where:** `test_fetcher.py:548`.
- **What:** The behaviour is correct by the pure check.
- **Fix:** Add `"User-agent: NessaL0\nDisallow:\n\nUser-agent: *\nDisallow: /\n"`, which should be allowed.

**M-6. The corpus agent's classification applies to whatever host a redirect reaches.**
- **Where:** `tools/corpus.py:59-66`, `acquire.py:182`.
- **What:** `--rights-class employer-posting` for URL A keeps the body of unlisted host B when A redirects there.
- **Fix:** Apply the classification only when the final host is the requested host (else the manifest's class), or record both hosts.

**M-7. Pre-existing, adjacent to A-M4: a long location part fails the whole page with a misleading label.**
- **Where:** `pages.py:248-258`, `records.py:163-167`.
- **What:**
  - A location part over its model bound (for example `addressLocality` over 120 characters) raises `ValidationError` in `parse_page` (probe: raised).
  - The worker answers it as `422 invalid_request` (`acquisition.py:119`), and the client maps that to transient `acquisition_worker_unavailable` (`service_client.py:49-53`).
- **Fix:** Cut location parts like other claim text, and stop mapping an internal `ValidationError` to 422.

**Verdict: open: A-I5, A-M6** (and the C-1 correction to ACQ-06 and ADR 0009 decision 4)

Counts: 12 fixed, 2 partially fixed, 0 not fixed. New issues: 1 Critical, 4 Important, 7 Minor.
