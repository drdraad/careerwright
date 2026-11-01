# Task W2B re-review 4 (scoped, read-only)

You re-review fix round 4 of Task W2, slice W2B (Careerwright L0, branch `l0-local-release`),
commit b2aa090 from BASE 392bc64. You are a reviewer: read and run read-only checks only.

## Read (all in `.superpowers/sdd/l0-sprint-tasks/`)
1. `reviewer-contract.md`
2. `task-W2B-fix-round-4.md`: the "Fix now" list you check against
3. `task-W2B-rereview-3.md`, "New findings": the findings round 4 answers (I1, I2, M1 to M4,
   and the plural title under "Other observations")
4. `task-W2B-report.md`, section "# Fix round 4" (line 1015 on)
5. `review-392bc64..b2aa090.diff`: the commit list, stat and full diff in one file

## Check
- Each item: done, with a test that would fail without it?
- Every note and label this round touched: now true in every case the re-review named, and
  in the nearest cases it didn't name (for example, a skill that is essential to some
  occupations but not reached through the person's own words)?
- The one code fix beyond tests (a one-word work style a model searched beside a task gets its
  work-style note, never "found no work"): correct and in scope?
- Every changed test input and assertion: disclosed, and still a real check?
- The web change: plain words, no new colour, strings through the existing vocabulary pattern,
  the singular "1 search" correct.
- DBOS `application_version` is still `careerwright-l0-1`.

## Scope
Matching rules, thresholds and ranking are closed (controller ruling). A finding about what the
slate suggests, and not about whether a note or label is true, is a "session W2 sheet" item,
not a fix item.

## Rules
Read-only: no edits, no commits, no `make acceptance`, no Docker pulls or new containers (the
running `careerwright-l0-*` stack is not yours; leave it), no headed browser or window on the
product owner's screen, no live model call, no web request, no subagents. Never read `.env`,
`~/.nessa` or `~/.careerwright`. Fast read-only checks are fine (`make check`, a focused
`uv run --locked pytest ...` from `backend/`).

## Output
Write `task-W2B-rereview-4.md` here: verdict (approved / not approved), each item checked with
`file:line`, new findings by severity (Critical, Important, Minor), and any session W2 sheet
items. Reply with only: verdict, counts by severity, one line per Critical or Important.
