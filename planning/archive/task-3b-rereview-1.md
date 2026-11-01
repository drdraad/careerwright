# Task 3b re-review, fix round 1 (b54a993..c2af6b1)

Reviewer: Claude (Opus 5.5), read-only. I read the fix list, the report's "Acceptance" and
"Fix round 1" sections, and the whole 1,143-line diff. I read the branch with `git show
wt-3b:`. Outside the diff I made two focused checks:
- where the menus sit on a phone (for M2);
- what still reads the old names (for M5 and M7).
I ran no tests.

## Verdict

**Approved.** Every finding is addressed except M2, which is right on tablet and desktop
but ambiguous on a phone. Nothing new is broken in the changed code. What's left is Minor:
one wording fix in the start summary, the phone menu words, and two lines in the
controller's own documents.

## Each finding

| Finding | Status | Where |
|---|---|---|
| I1 per workspace, total printed | Addressed (2 words left, see below) | `Makefile:25-26`; `backend/tools/session.py:1-30` (docstring), `:202-237` (`session_summary`), `:244`; runbook `make session` row; `docs/adr/0003-meta-model-selection.md:205-211`; register MODEL-08, MODEL-11; ledger header (`usage_ledger.py`, `.md` header only, no row changed). Test: `tests/tools/test_session.py:137` (two, one and no workspaces) |
| M1 spending words | Addressed | `apps/web/src/lib/vocabulary.ts:60-61`; runbook step 7; `ModelSpending.test.tsx` (singular and new plural case) |
| M2 menu name | Partly | `vocabulary.ts:49`. See below |
| M3 estimate refused by the run limit | Addressed | `apps/web/src/components/RunEstimate.tsx:24-36`; new test in `RunEstimate.test.tsx` (no "can cost", no "$0.15"); story `EstimateRefusedByTheRunLimit` |
| M4 (documents) | Addressed | `Makefile:27-28`; `session.py:4-6` and `:244`; runbook `make session` row ("its API and worker restart … a run in flight restarts too") |
| M5 session-ledger | Addressed | Scope `live-app-<date>` and its purpose (`session.py:69` and `session_entry`); "with the stack up" in `Makefile:29`, the runbook row, the docstring and the start summary. Tests updated. The old scope was never used, so no ledger row changes. Nothing still reads `live-session` or the old constant names (I checked) |
| M6 ADR bound | Addressed | `docs/adr/0003-meta-model-selection.md:188-191` |
| M7 one project | Addressed | `backend/tools/stack.py:192-197` and `:229`; `session.py:112`; test `test_session.py:61`. Every CLI stack command and `make session` read it through `project_from_env()`. The only other `Stack()` builds images (`tools/setup.py:63`), so the project name doesn't matter there |
| M8 report gaps | Addressed | Report "Acceptance" section; the `test_model_registry.py` change disclosed under M8 |

## The implementer's three concerns, judged

1. **"About $5 a session" left in Task 3b's card, ADR 0003's amendment and the audit.**
   - Right for the audit: it's a record.
   - Right for the ADR's amendment (`:155`): a new paragraph in the same ADR settles it
     (`:205`).
   - Not right for the card (`docs/plan/l0-sprint-tasks.md:588`, "about $5 a session").
     The card is a live requirement, not a record.
   - The implementer missed a second live spot: the plan's S1.6
     (`docs/plan/development-plan.md:420`) says "caps each session (about $5)".
   - Both are the controller's documents (R15), so the controller should change them to
     "per workspace" or note the ruling beside them. Minor.
2. **"The menu at the top", not "top right", because of the phone layout.** The reasoning
   about "right" holds, but on a phone "the menu" isn't unique. See M2 below.
3. **`make session-ledger` still fails with a traceback when the stack is down.** That is
   what the fix list asked: say it in the documents. The documents now say it in four
   places. A clean "start the stack first" message can wait for the final review.

## Still open (Minor)

**M2, on a phone: "the menu at the top" first points to the chapter menu.**
- On a phone (up to 760px wide), the top bar shows the chapter menu: a menu glyph with the
  chapter's name (`apps/web/src/components/ChapterNav.tsx:81-84`, `globals.css:1015-1035`).
  The account menu's identical glyph is in the strip below it.
- A person following the words would probably open the chapter menu first and not find
  Model spending there.
- The words are right on tablet and desktop, where there is only one menu at the top.
- Fix options:
  - give the account trigger its own glyph (for example a person) and say "the account
    menu at the top";
  - or say which one ("the second menu at the top, beside the saved state");
  - or put the question in session W2's "words you didn't understand".

**N1 (new, wording): the start summary's "in all" leaves out synthetic workspaces.**
- Where: `backend/tools/session.py:230`.
- What: it says "So this session can spend at most $X in all", but X counts only the live
  workspaces it capped. Existing synthetic workspaces keep their own limits. They spend on
  the same Meta key, at test-model prices.
- Fix: say "on Muse Wonder" instead of "in all", or add that synthetic workspaces keep
  their own limits.
- Optional: the summary shows six decimals ("$5.000000", "$0.750000"). The person reads
  it, so cents ("$5.00") would read more plainly.

**N2 (tiny): one runbook claim is loose.**
- What: the runbook says "the dates keep each session's attempts apart". A `make dev` run
  and a session on the same UTC day share one scope.
- It does no harm, because the ledger copy names `make dev` and `make session` together.
- Fix: leave it for the final review.

## New breakage

None found in the changed code.
- The new project test replaces only `Stack.stop`, the Docker boundary, and restores it.
  It also points `CAREERWRIGHT_HOME` at a temporary folder.
- `test_owner_commands.py` still reaches `project_from_env()` through `make demo`'s
  environment.
- In the web app, only the words, the refused-by-run branch and one story changed.
- The money code is unchanged: the run cap, `session_limits`, the reservation, and the
  copied columns.
