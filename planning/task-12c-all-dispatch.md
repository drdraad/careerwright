# Task 12c follow-up: the Advanced Learner Loan follows the tuition fee loan rule

The product owner answered your question (1 November 2026): "I think so". So an Advanced
Learner Loan paid straight to the provider is a loan to repay, exactly as Task 12c treats a
tuition fee loan: not the person's cash, direct spending or payment-cap money; never support;
listed as a loan to repay with repayment unknown; the same status rules (approved counts,
otherwise conditional beside the self-paid route); an unknown amount unresolved. Recorded as
the product owner's provisional yes; session W2 asks it again plainly.

## Your tree
Worktree `/home/user/careerwright-wt/12c`, branch `wt-12c`, reset to
`claude/confident-ramanujan-ux3saw` at c746e42 (it holds all of Task 12c, migration 0041,
and Task 6e's migration 0042). Running in the main tree beside you: Task 6e's fix round
(evidence, research, web; no planning code). Rebase onto the branch at the end (R15: a
migration takes the next free number after the branch's highest; regenerate the client).

## Build
1. The smallest change that lets the person state an Advanced Learner Loan on an option the
   way they state a tuition fee loan (a kind or a field on the same statement is fine; your
   call, stated in ADR 0013). Everything else in the rule is shared, not copied.
2. The oracle reads the rule again independently (it covers both loans in every state); the
   search equals the oracle; pruning version only if a rule changes.
3. A migration only if the stored inputs change, forward-only, CHECKs repeating the rule.
4. Maintenance loans and every other loan stay refused as support.
5. ADR 0013 amendment line; register (FUNDING-06/FUNDING-04 rows) last.
6. Update `planning/task-12c-claude-md-proposal.md` so the proposed CLAUDE.md line names both
   loans (don't edit CLAUDE.md).

## Checks and rules
RED before GREEN. `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24 on
PATH). Docker is now running, but the controller runs integration and acceptance once, at the
end, for all pieces: don't run them. Hard rules as before: Edit/Write only (generators fine),
explicit pathspecs, no web, no live calls, no subagents, never read `.env` or print an
environment value, never push. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
Append "Follow-up: the Advanced Learner Loan" to `planning/task-12c-report.md` (in the main
tree's planning folder); reply with the short contract and your head SHA.
