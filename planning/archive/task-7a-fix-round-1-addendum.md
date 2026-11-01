# Task 7A — fix round 1, addendum: security re-review residuals

The security re-review (`task-7a-rereview-1-A.md`, range 5c5e5bb..5209825) found 12 of 14 A-*
items fixed. A-I5 and A-M6 are partly fixed, with 1 Critical, 4 Important and 7 Minor new
issues. Read the re-review in full. These rulings join fix round 1: do them after the B-*
items, in the same report, before you report.

1. **C-1, I-1, I-2, I-3, redaction. Ruling:** redact decoded values, never raw JSON.
   - For each JSON-LD block, `json.loads` it, apply `redact_text` and the contact removal to
     every string, then re-serialise with `</` escaped so a `<\/script>` cannot close the
     block.
   - Do the same on Adzuna's parsed JSON.
   - Redact HTML outside the script blocks as text.
   - Normalise line endings in the decoded page before redaction and parsing.
   - Fail safe: a contact-bearing block that cannot be located means the body is never kept
     (excerpts only, with a label).
   - Tests: emails and phones after `\n`, `\t` and `>` escapes, in JSON-LD and in Adzuna
     JSON; a CRLF page with `applicationContact`; a posting that still parses after
     redaction.
   - Then make ACQ-06 and ADR 0009 decision 4 say exactly what holds.
2. **I-4:** a search candidate that fails `check_url` is recorded by its refusal and its host
   as text, never in a field named `url`. Test with `javascript:`.
3. **M-1:** redact description and contact strings only, never ID or URL fields. Test that
   `identifier.value "0123456789"` survives.
4. **M-2:** pass the remaining time to admission. A pacing wait that would pass the deadline
   is refused as a transient timeout, without sleeping or reserving a slot. Keep the ADR
   decision 3 wording exact.
5. **M-3:** refuse non-ASCII dots before IDNA, and keep the docstring exact.
6. **M-4:** every negative reach probe asserts a known failure label. An empty or unknown
   output fails the test.
7. **M-5:** add the empty-`Disallow:` group test.
8. **M-6:** an agent's `--rights-class` applies only when the final host is the requested host;
   otherwise the manifest's class applies, and both hosts are recorded.
9. **M-7:** cut location parts like other claim text. An internal `ValidationError` in the
   worker is never answered as `422 invalid_request`: answer it with an internal-error label
   the client does not treat as "worker unavailable".
10. **A-M4's apply-link exemption. Ruling:** accepted, because a truncated URL is a wrong URL.
    This holds only if the apply link is bounded by the URL length check (no claim past it).
    Confirm that bound, test it, and record it in ADR decision 5.

Same rules as round 1: Edit/Write only, no subagents, never read `.env` or NESSA_HOME, no new
live calls for these items. `make check` and `make acceptance` once at the end cover both
parts.
