# Task 12b, backend half (12bA): the Options chapter's facts and commands (worktree, R17)

Careerwright L0. The current process ruling (`docs/plan/l0-sprint-tasks.md`, "How we build and
review"): a task's backend half may start before session W2 (words and looks only). Task 7f is
complete: option pack **0.4.0** (SHA-256 d005713b…01b3c8) is the reviewed school-leaver version
this task pins. Task 10's backend half (10A) is integrated. The screens half (12bB: the Options
chapter itself) waits for session W2.

## Your tree
Worktree `/home/user/careerwright-wt/12b`, branch `wt-12b` from 4a05371 (`var` linked). Work and
commit only there. Rebase onto `claude/confident-ramanujan-ux3saw` at the end (R15: renumber a
clashing migration, regenerate the client, register last).

## Read first
`/home/user/careerwright/planning/env-cloud.md`, `implementer-contract.md`, your brief
`task-12b-brief.md`, the carried items `carry-forward-task-12.md` (all still yours unless
already done: check each against the code and say which), ADRs 0011, 0012, 0013 and 0016 as
amended, `careerwright/planning/` (12a's commands and stored inputs, 12c's fee loans, the
checker, the search), `careerwright/catalogue/option_pack.py` (PINS, `load_pack`), Task 10A's
Skills facts (entry confirmations as readiness facts), and Task 6f's qualifications.

## Deliver (backend and API only; facts and codes, never sentences, R11)
1. **Pin pack 0.4.0** for planning. The capability model pins pack and reference 0.2.0, and
   0.4.0 has no capability reference of its own: settle it the simplest honest way (a check
   that 0.2.0's reference fits 0.4.0's targets, or a 0.4.0 reference built by the existing
   tool from 0.2.0's with nothing invented), state it in ADR 0011/0012, and test it. If neither
   is honest without a human review, stop and tell the controller.
2. **The checkpoint's facts:** for each option, the facts the route search lacks (start date,
   cost, weekly hours, entry confirmation) as codes; the person supplies one as their own
   figure (labelled theirs and not reviewed; where it's stored, settled by you, through a
   command with an expected version and an `Idempotency-Key`) or chooses a stated intake;
   the search then runs on what they supplied, and every route resting on a supplied figure
   is qualified. Without them, the result names what is missing, never "no route".
3. **"Add an option yourself"** (S5.7): pasted text or typed details saved as the person's own
   workspace record, `review_state: proposed`, dated, with its source; the planning catalogue
   reads it beside the pack; a route on it is qualified. Values come from the person (typed,
   or chosen as spans of their pasted text, reusing 10A's span pattern in UTF-16 units); no
   new run kind (the infrastructure is frozen for L0).
4. **The carried items** (stacking unresolved until confirmed; the payment cap's meaning with
   D15's answer and a finding naming repayments; the explicit "no" to entry requirements as its
   own finding; ledger month rows never partial-as-known; outcome accept/override at the
   checkpoint), each tested.
5. **School leavers (plan v1.6):** baseline "staying in education" and "not working: 0 hours,
   £0" as facts; an expected qualification never met; each scheme's age rule beside it,
   never applied to an unknown age; the tuition fee loan and Advanced Learner Loan through 12c's
   command.
6. **Never truncate silently:** over 24 options or two intakes, a code asking to retain
   variants, with the counts.
7. P01's acceptance at the API level: with the missing facts supplied, computed routes from the
   route search, each qualified where it rests on a supplied figure; without them, the missing
   facts named.
8. Migration if needed (forward-only, CHECKs, row-level security); the generated client; ADR
   lines; register rows marked "backend; screens in 12bB".

## Rules
`env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24 on PATH). Focused
integration runs of the tests you touch, under the lock with the build shim, one guarded command
each (if the lock is held, wait and retry; never remove a lock you didn't take):
`export PATH=/tmp/ccr-shim:/opt/node24/bin:$PATH; L=/home/user/careerwright/.superpowers/acceptance.lock; mkdir $L && { cd /home/user/careerwright-wt/12b/backend && env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY uv run --locked pytest -m integration <files> > /tmp/12b-int.log 2>&1; rc=$?; rmdir $L; exit $rc; }`
No whole acceptance (the controller runs it per batch). Edit/Write only (generators fine),
explicit pathspecs, no web requests, no live calls, no subagents, never start Docker, never read
`.env` or print an environment value, never push. One paper file: your report (the review and
fix round get appended to it). Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
`/home/user/careerwright/planning/task-12bA-report.md`; reply with the short contract and your
head SHA.
