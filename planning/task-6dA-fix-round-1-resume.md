# Task 6d slice A, fix round 1 of 5: resume after a crash

The machine rebooted while the previous fix implementer was working. You are a fresh
implementer and you finish its round. Careerwright L0, branch `l0-local-release`, main tree
`/Users/darianraad/Code/careerpathoptimizer`, HEAD 8ad36a6 (FIX_BASE 8ad36a6).

## Your requirements
`.superpowers/sdd/l0-sprint-tasks/task-6dA-fix-round-1.md` is the fix list. Read it first and
follow it exactly, including its "Read first", "Not now", "Then", "Hard rules" and "Report"
sections. Everything below only adds to it.

## What the previous implementer left (uncommitted, unverified)
`git diff` in the main tree shows its work in progress:
- `apps/web/src/components/SketchCard.tsx`, `apps/web/src/lib/vocabulary.ts`: a start on item 1
  (`RESEARCH_STATUS` now worded from the match and the coverage; a pack target with no ESCO
  match shows no "Not researched" line).
- `apps/web/src/components/SketchCard.test.tsx`, `apps/web/src/lib/discoveryWords.test.ts`,
  `backend/tests/domain/test_targets.py`, `backend/tests/integration/test_discovery.py`,
  `backend/tests/integration/test_targets.py`: new tests, likely for items 1, 3 and 4.
- No migration 0035 yet.

Treat it as a draft, not as done:
1. Read the diff. Keep what is right; change what isn't.
2. Each fix still needs RED before GREEN. For a fix already applied, show RED by stashing that
   source change (or `git stash push -- <path>`) and running its test, then restore it.
3. Record in your report which parts you kept from the draft.

## Docker
After the reboot the Docker daemon was down. The controller has asked the product owner to start
Docker Desktop. Integration tests and `make acceptance` need it.
- Check with `docker info >/dev/null 2>&1`. If it is down, do the code and the fast checks
  first, then try again later. Never start Docker yourself and never open an app or window.
- If it is still down at the end, report "integration and acceptance not run: Docker down".

## The acceptance lock
The controller will also run Task 3b's `make acceptance` under the same lock, in its worktree.
Take the lock exactly as the contract says, in one guarded command. If it is held, do other
work and try again; never remove or recreate it.

## Another implementer
None right now. A reviewer reads Task 3b's worktree (`careerpathoptimizer-wt/3b`), read-only.
Commit with explicit pathspecs only.

Reply with only the contract's short report.
