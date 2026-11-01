# Task 6e: research this role, the synthetic school leaver, session W2's package (main tree)

Careerwright L0. Tasks 6d, 6f (except Childline) and 3b are complete; Task 12c landed.

## This machine first
Read `/home/user/careerwright/planning/env-cloud.md` (Node 24 on PATH, checks with the Adzuna
variables unset, Docker down: integration, acceptance, browser tests and captures can't run;
report them as not run, never start Docker).

## Your tree
Main tree `/home/user/careerwright`, branch `claude/confident-ramanujan-ux3saw` (head
bd5298b). Commit with explicit pathspecs. Nothing else runs beside you now; a worktree task
may start later (planning or the option pack, never your files).

## Read first (all in `/home/user/careerwright/planning/`)
1. `implementer-contract.md`.
2. Your brief, `task-6e-brief.md`: your requirements, with the role-space appendix (F)
   section 6 "Second slice", ADR 0015, ADR 0009 decision 12, Task 3b's run pricing.
3. `task-6f-report.md` (both sections): the no-job answer, the two new answers, interview
   prompt version 5, what the demo reads.
4. `audit-no-job-yet.md`, section on personas and evaluation cases (finding 7).

## Decisions that bind you
1. **You make no live call and no web request.** Build and test everything offline with
   fixtures: two hosts → found; one page or two copies of one advert → "not yet found in
   independent sources"; a page that instructs the model → changes nothing. The capped live
   runs (the synthetic title's research run, and the school leaver's interview cases on
   prompt version 5) are the controller's, after you report. Write the exact commands and
   their caps in your report; add a `make` target or `tools` entry for them if none fits,
   capped and ledgered like `make live-extract` (R5).
2. **Role research** is a new purpose of the existing source search, sending only the title
   and "England" (SEC-05); pages read only by the restricted acquisition worker through the
   guarded fetcher; class from the manifest. Corroboration by code, word for word as a span
   of visible text. Never a suggestion until found; the person's own title stays choosable
   without research.
3. **Duties and entry requirements on opening a found role:** settle whether it fits L0's
   per-role spend bound (ADR 0015). If it doesn't fit simply, defer it with reasons in ADR
   0015 rather than stretch the bound.
4. **The synthetic school leaver** exactly as the card says; labelled synthetic on every
   surface; `fixtures/m0` untouched (hashes still match); never fills a live field. Four to
   six evaluation cases, passing offline on the demo interviewer. Nothing called close to
   what she does now; no invented job title or income.
5. **Childline is held back** (the controller can't reach its website yet). Session W2's
   package keeps its yes/no line as "to add when Childline's details are checked", not a
   drafted panel line.
6. **Session W2's package** in plain words (CLAUDE.md "Talking to the user"): how to start
   the session command, the five questions, two or three personas (one whose role is on no
   list; the school leaver), the record sheet, and the questions the ledger has gathered for
   session W2 (ledger lines starting "Session W2" in `planning/progress.md`). Every item
   "not run — requires human".
7. R11: facts and codes from the API, words in the web. Every write takes an expected
   version and an `Idempotency-Key`; a run kind is a `RunTask`, never a second call path
   (ADR 0006); DBOS `application_version` stays `careerwright-l0-1` unless a workflow's step
   sequence changes. Forward-only migration (next free: 0042) with CHECKs.
8. Regenerate the client.

## R16
One reviewer after you report, one fix round at most. RED before GREEN.

## Hard rules
Edit/Write for every source change (generators are fine). Explicit pathspecs; never stage
`answers-2.md` or `esco_research.txt`. No web requests, no live calls, no subagents, never
start Docker, never read `.env` or print an environment value, never push, never write
distress or self-harm text, pnpm only. Disclose every changed test input or assertion. The
register and `docs/plan/*` last. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
Write `/home/user/careerwright/planning/task-6e-report.md` (with the live commands and caps
for the controller), then reply with only the short contract.
