# Review: Task 12c, a tuition fee loan is a loan to repay

You are the one reviewer for this piece (R16: experience and code together; here backend only).

## This machine
Read `/home/user/careerwright/planning/env-cloud.md` first. The code is in the worktree
`/home/user/careerwright-wt/12c` (branch `wt-12c`, head b2b4eeb, based on 0118ea0). Read only.

## Inputs (all in `/home/user/careerwright/planning/`)
1. `reviewer-contract.md`: your method and output format (its Mac path means the paths above).
2. `task-12c-brief.md` (requirements) and `task-12c-dispatch.md` (binding decisions).
3. `task-12c-report.md` (the implementer's claims, unverified) and
   `task-12c-claude-md-proposal.md`.
4. The package: `review-0118ea0..b2b4eeb.diff` (2,548 lines; lockfiles and the generated
   client excluded).

## Risks to check by name
1. The fee is counted nowhere twice and nowhere it shouldn't be (FIN-1): the cash ledger,
   direct spending, the payment cap, receipts, support. And the economic cost counts it
   exactly once.
2. Status: only an approved loan counts unconditionally; otherwise conditional beside the
   self-paid route with a blocking verification. An unknown amount is unresolved, never £0.
3. Every other loan (maintenance, Advanced Learner Loan) still refused as support.
4. The oracle shares no code with the checker and covers every loan state; pruning version
   raised; rule 2 classification right.
5. Migration 0040: forward-only, row-level security kept, CHECKs repeat the domain rules (it
   has never run on PostgreSQL: Docker down; read it closely).
6. Expected version and `Idempotency-Key` on the write; R11 (facts and codes, no sentences).
7. Any changed expected value in TRACE-01, the A–I fixture or a regression family.

## R16 rulings you inform
Mark each finding as safety, truth (false statement, failure shown as empty success, false
evidence record) or lost input, or as "list". Only the first three get fixed now.

## Rules
Read-only. No web requests, no live calls, no subagents, never start Docker, never read
`.env` or print an environment value.

## Output
Write the review to `/home/user/careerwright/planning/task-12c-review.md` and reply with only
the verdict, counts by severity, and one line per Critical or Important finding with file:line.
