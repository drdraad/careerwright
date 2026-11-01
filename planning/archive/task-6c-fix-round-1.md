# Task 6c — fix round 1 (FIX_BASE 865ab59; docs and one comment)

Review 1: Spec ✅, Approved, no Critical or Important. The controller upgrades three Minors
(honesty of recorded gates; a binding UI invariant) to fix now. Docs and a code comment only.
`865ab59` is the controller's approved CLAUDE.md commit (the `next` sentence); leave it.

1. Decision 12 bullet and REC1-11 say more than answer 3
   (`docs/adr/0007-conversation-discovery-and-support.md:472-478`,
   `docs/requirements-register.md:119`). They say "the readiness, pay and hiring word lists
   and phrasings" were accepted; answer 3 accepted the blocking rule with four example
   words, not the full lists. Word both places as the checklist tick at `:525-535` does
   ("as answer 3 put them: the rule, with its examples"), and keep the full lists among
   what was not asked.
2. Stale rows in the latest sprint review (`docs/reviews/sprint-2.md`):
   - `:302`: the `next` 16.4.1 age exception is "Open: not yet 14 days old" — close it, citing
     Task 6c's removal (ac94bf4) and the frozen-install evidence.
   - `:297` and `:464` (H-12 rows) still say "Not run — requires human". Controller ruling:
     update both to the recorded outcome — session 1 (2026-10-28) and its item 7 addendum
     close seven of the checklist's nine items, citing `docs/reviews/session-1.md`; the open
     items (the counterfactual pass rule and fields; the written-explanation details not
     asked) stay "not run — requires human". Say no more than the register's H-12 row says.
3. The forward rule for computed routes (`apps/web/src/components/RoutePreview.tsx:6-9`,
   `docs/design/README.md:102-104`, `docs/reviews/sprint-1.md:305`): state explicitly that
   computed routes (Task 14) take their qualification from their own computed readiness
   state, never from the fixture adapter's words, and never show an unqualified "Ready in …"
   when that state carries a condition. Comment and docs only; no behaviour change.

Also: `make check` (the comment touches a source file). No acceptance run needed for docs and
a comment. Edit/Write tools only. Append the fix report to task-6c-report.md and reply with
the short contract.
