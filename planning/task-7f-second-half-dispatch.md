# Task 7f, second half: publish the reviewed school-leaver pack (worktree)

The school-leaver pack session is held: `docs/reviews/school-leaver-pack-session.md` is the
product owner's record. The product owner's ruling: "AI check counts as my review" (133 rows
yes). Their answers to the six rows sent back, verbatim: "yes, fix 1-3, 4. no not fair, 5
yes, 6 yes" (spelled out in the record's last section).

## Your tree
Worktree `/home/user/careerwright-wt/7f`, branch `wt-7f`, reset to the branch head (292e9e8;
`var` linked). Work and commit only there. In the main tree: the controller's acceptance run
and a documents-only clean-up (planning/, docs/plan/). Never touch them. Rebase at the end
(R15; the clean-up may move planning files: your dispatch and report stay where they are).

## Read first
`/home/user/careerwright/planning/env-cloud.md`, `implementer-contract.md`, your brief
`task-7f-brief.md` (second half), `task-7f-report.md` (all sections), the session record,
ADR 0011, how Task 7c published 0.2.0 (`planning/task-7c-report.md`, possibly moved to
`planning/archive/`).

## Deliver
1. Publish the reviewed version from the record only (as Task 7c did): pack 0.3.0 is
   unpublished, so publish it as the reviewed version (0.3.0, or a new number if ADR 0011
   requires a reviewed version to differ from the proposed one; say which and why). A record
   becomes `reviewed` only when every one of its rows is yes in the record (counting the
   corrections the product owner approved); name the reviewer as the record does ("an AI
   check, counted as the product owner's review by their ruling of 2026-11-01"), the decision
   date and the session. A record with an undecided row stays `proposed` (Q101's record).
   0.1.0 and 0.2.0 never change.
2. Apply the approved corrections with their spans cited and the decision named:
   Q75 (only the £39,160 total may change), Q95 (no "may change" on £15,415), Q104 (5% for
   non-levy employers; 25% for others, the page's words), Q110 (the T Level record states "T
   Levels started in September 2020" and providers "from September 2025"; a provider's next
   start stays unknown), Q115 (13 January 2027 for the nursing degree, citing UCAS's
   2027-entry equal consideration date for most undergraduate courses and GOV.UK's student
   finance page naming nursing; the product owner's decision named). UCAS's rights: the
   product owner allowed short quotes (record point 6): its class and terms recorded in the
   manifest; keep its excerpts minimal; its body still not in git.
3. Update `corpus/manifest.json` and `corpus/README.md` from the record; the open rights item
   for UCAS closed by the decision; the register (OPTN-14, H-07's school-leaver part, OPTN-10,
   TEST1-09) last.
4. Hand off to Task 12b in your report: the reviewed version's number and hash, which 12b pins.

## Rules
`env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24 on PATH). No acceptance
(the controller runs it). Edit/Write only (the project's generators such as
`tools.school_leaver_pack` are fine), explicit pathspecs, never stage `var` or a page body, no
web requests, no live calls, no subagents, never start Docker, never read `.env`, never push.
Never enter a value the record or a page doesn't give. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
Append "Second half" to `/home/user/careerwright/planning/task-7f-report.md`; reply with the
short contract, the reviewed version's number and hash, and your head SHA.
