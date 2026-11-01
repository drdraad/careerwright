# Review: Task 13a, the route search core

You review one task of Careerwright L0. It was built in the worktree branch `wt-13a`,
rebased onto `l0-local-release` at ec4d060. The commits are ec4d060..0eb11b5. This search is
the source of every computed route a person will see, so its truth matters more than its
style.

## Read first (paths from `/Users/darianraad/Code/careerpathoptimizer`)
1. `.superpowers/sdd/l0-sprint-tasks/reviewer-contract.md`, including its calibration.
2. The brief: `.superpowers/sdd/l0-sprint-tasks/task-13a-brief.md`. It holds the Global
   Constraints, the standing rulings and the card. The card's line about an instance from
   P01's stored inputs waits for Task 12a (it has no store yet): that part is out of scope
   here.
3. The dispatch the implementer worked from: `.superpowers/sdd/l0-sprint-tasks/task-13a-dispatch.md`.
4. The implementer's report (unverified claims): `.superpowers/sdd/l0-sprint-tasks/task-13a-report.md`.
5. The diff: `.superpowers/sdd/l0-sprint-tasks/review-ec4d060..0eb11b5.diff` (3,680 lines).
6. As needed:
   - spec section 12 (OPT-1 with "Consequence of the M0 limits", ROU-1, FIN-1, RDY-1);
   - the plan's Sprint 6a card;
   - ADR 0013 and the new ADR 0016 (in the diff);
   - `CLAUDE.md`'s planning invariants: Pareto layers over the full archive, dominated
     schedules included, equal points not dominating each other; a truncated search is never
     "no route"; `NO_ROUTE_IN_BOUNDED_MODEL` needs complete coverage; readiness milestones
     come only from `careerwright.capability.readiness.assess`; the oracle shares no code with
     `careerwright.planning.checker`.

## What matters most
Grade by the effect on the person.
- Can the search ever report "no route" or `complete` when it did not exhaust the declared
  tree, or drop a feasible schedule through an unsound prune?
- Is each pruning rule's proof correct?
- Is the oracle genuinely independent, so that it could catch a defect the search and the
  checker share?
- Are the layers computed over every feasible schedule found, dominated ones included, with
  equal points not dominating each other?
- Is money integer throughout?
- The measurements (sizes, states, times) are a deliverable that sizes Task 13b. Are they
  measured as claimed, and stated honestly?
- The report says every reviewed-pack offering lacks a fact the search needs, so every pack
  target's result is "unresolved". Check that this reading of the pack is correct, and that
  the result's words and codes say what was missing rather than implying no route exists.

## Rules
- Read the code on the branch: `git show wt-13a:<path>`. The worktree is at
  `/Users/darianraad/Code/careerpathoptimizer-wt/13a`; read only.
- Read-only everywhere. Never modify any tree, index, HEAD or branch. Other agents are working
  in the main tree.
- `make check` passed after the rebase (the implementer's run): don't re-run suites. One
  focused test is fine when reading raises a specific doubt. If you need to run it, use the
  worktree's environment
  (`cd /Users/darianraad/Code/careerpathoptimizer-wt/13a/backend && uv run --locked pytest <path>`),
  which changes nothing tracked.
- No web requests, no live calls, no Docker, no browser, no subagents. Never read `.env`,
  `~/.careerwright` or `~/.nessa`.

## Output
Write the review to `.superpowers/sdd/l0-sprint-tasks/task-13a-review.md`, in the contract's
format. Then reply with at most 10 lines: counts by severity, each Critical or Important item in
one line, and the path.
