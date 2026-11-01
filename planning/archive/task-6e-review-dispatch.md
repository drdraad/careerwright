# Review: Task 6e, research this role, the synthetic school leaver, session W2's package

You are the one reviewer for this piece (R16: experience and code together).

## This machine
Read `/home/user/careerwright/planning/env-cloud.md` first. Main tree `/home/user/careerwright`,
range 7ebb214..394c263. Read only.

## Inputs (all in `/home/user/careerwright/planning/`)
1. `reviewer-contract.md` (its Mac path means the path above).
2. `task-6e-brief.md` (requirements) and `task-6e-dispatch.md` (binding decisions).
3. `task-6e-report.md` (claims, unverified; two process departures disclosed: a Python
   one-off edit, and `corroboration.py` written before its test).
4. The package: `review-7ebb214..394c263.diff` (5,154 lines; read in passes, say so).

## Risks to check by name
1. SEC-05: the search sends only the title and "England", never the person's answers; the
   restricted acquisition worker alone reads pages, through the guarded fetcher; class from
   the manifest.
2. Corroboration by code: word-for-word span of visible text; two independent hosts or one
   official page; copies of one advert count once (ADR 0009 decision 6); otherwise "not yet
   found in independent sources", visible, never a suggestion. A blocked or failed page is
   never "none found". A page that instructs the model changes nothing.
3. `corroboration.py` had no RED of its own: do its tests assert real behaviour, including
   the edges (case, punctuation, a title inside a longer word, hidden text)?
4. Run kind: a `RunTask`, never a second call path; cancellable; caps and ledger (R5);
   migration 0042 forward-only with CHECKs and row-level security; expected version and
   `Idempotency-Key`; DBOS `application_version`.
5. `make live-role-research`: capped and ledgered like `make live-extract`; test model only
   with synthetic data; never in check or acceptance.
6. The synthetic school leaver: labelled synthetic on every surface; `fixtures/m0` untouched;
   never fills a live field; her cases invent no job title or income and call nothing close
   to what she does now.
7. Session W2's package (`docs/reviews/session-w2.md`): plain words per CLAUDE.md "Talking to
   the user"; every item "not run — requires human"; Childline held as "to add"; no internal
   codes the product owner doesn't need.
8. The experience: research shown only under the suggestions (needs a discovery first): is
   that a dead end for a person whose own title is on no list? A world, not a form.

## R16 rulings you inform
Mark each finding safety, truth (false statement, failure shown as empty success, false
evidence record) or lost input, or "list". Only the first three get fixed now.

## Rules
Read-only. No web requests, no live calls, no subagents, never start Docker, never read
`.env` or print an environment value, never compose distress or self-harm text.

## Output
Write `/home/user/careerwright/planning/task-6e-review.md`; reply with only the verdict,
counts by severity, and one line per Critical or Important finding with file:line.
