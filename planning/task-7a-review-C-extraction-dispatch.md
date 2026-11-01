# Task 7A — review C: model extraction (fix round 2, part 2)

You review the model extraction that fix round 2 added to slice 7A (evidence acquisition) of
Nessa L0. This is a full review of new work, not a re-review. Follow
`reviewer-contract.md` in this directory exactly (method, calibration, output).

Inputs (all in `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/`):
- Requirements: `task-7a-fix-round-2.md`, **part 2, items 9–16** (the controller's rulings),
  read with `task-7-brief.md` (slice 7A's card, ACQ-03/ACQ-04, OI-09, GC8).
- The implementer's report: `task-7a-report.md`, section "Fix round 2" (unverified claims).
- The diff: `review-dc8dd4d..1132cf0.diff` (part 2's four commits, 4.6k lines). Part 1
  (b24d264..dc8dd4d: B N1–N7, B-M2, A N-1–N-4) is reviewed by others; inspect it in git only
  where extraction depends on it (for example the `no_posting_readable` labels or redaction).
- Already ruled, do not re-raise: cancelling an acquisition will cancel its extraction runs
  not yet settled (next fix round). Erasing the extraction input for every rights class is
  accepted (stricter than ruling 11; kept bodies follow their own retention).

Named risks to check, one focused check each (say what you checked):
1. GC8: the acquisition worker (`nessa/acquisition.py`, its container and network) still
   holds no model key, master key or database credential, and extraction runs only in the
   DBOS worker.
2. One call path: extraction is a run kind on the one bounded activity (one `RunTask`,
   ADR 0002/0006), with its own reservation, the repair bound, access/model/key/budget
   re-checks, sealed input opened just in time, failures classified with the message
   discarded. No second provider call path.
3. Eligibility and cap: only retrieved, permitted pages whose structured data gave no
   posting; never refused, failed, pasted or parsed sources; at most
   `MAX_EXTRACTIONS_PER_ACQUISITION`; a run not started leaves a typed `extraction_not_run`
   reason, never "none found"; demo workspaces never call a provider; the test model takes
   synthetic data only.
4. Span verification and approval: every approved field has a verbatim quote verified as a
   span of the hashed redacted text, then the same validation as the JSON-LD path (pay,
   currency, dates, https apply link via `apply_link`, redaction, claim bounds); unverified
   fields dropped with a reason; critical disagreement quarantined; provenance shows the
   model read it; no model output in any receipt.
5. Retention: the sealed input is erased once the run settles for classes whose body may
   not be kept (hash, verified spans and excerpts of at most 200 characters remain), and a
   test proves it; kept classes follow existing retention; redaction happens before hashing
   and sealing.
6. Honesty: a model run that finds no posting never supports
   `none_found_in_sources_checked`; only an API's own empty answer does. Words in
   `vocabulary.ts` say what happened.
7. Prompt injection: no tools on the agent; the fake-provider tests cover an unquoted value,
   a quote not in the text, a `javascript:` link, an extra field, a field claiming the
   person's profile or key, and page instructions changing nothing outside the run.
8. Live cap and cost: scope `live-extract` is test model only, a synthetic labelled fixture
   page, at most 3 requests and $0.30, never in `make check`/`make acceptance`, every call
   ledgered with tokens, cost and a leak scan.
9. Workflows: whether any committed workflow's step sequence changed and, if so, whether
   DBOS `application_version` changed with a recorded reason.
10. Migrations: forward-only, new files only, CHECKs on new label columns, RLS on any new
    table, worker grants least-privilege.

Do not compose self-harm or distress example text; point at existing tests instead. Never
read `.env` or NESSA_HOME. Read-only. No subagents. Never run live Meta calls.

Write your full report to `task-7a-review-C.md` in this directory, then reply with only the
two verdicts and the counts of Critical, Important and Minor issues.
