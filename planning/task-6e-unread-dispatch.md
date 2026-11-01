# Task 6e follow-up: unread pages are never "not on any page" (truth)

Found by the controller's first live role-research run (ledger row 44, 2026-11-01): the search
proposed five pages; every read failed (`robots_unreachable`, the session's network allowlist),
and the verdict came back `not_yet_found` with reason `not_on_any_page`. CLAUDE.md: "A blocked,
failed or unread source is never 'none found'." `corroboration.py:249` picks
`NOT_ON_ANY_PAGE` whenever no page verified the title, including when no page was read at all.

## Your tree
Worktree `/home/user/careerwright-wt/6e-unread`, branch `wt-6e-unread`, from 1d227ff. Work and
commit only there. The controller is running `make acceptance` in the main tree: don't touch
it. Read `/home/user/careerwright/planning/env-cloud.md` (Node 24 on PATH; checks with the
Adzuna variables unset) and `/home/user/careerwright/planning/implementer-contract.md`.

## Fix (RED first)
1. Trace how the product (not only the live tool) reaches `corroborate`: which pages it is
   given (read only? failed too?), and what the API and the web show for a run whose pages all
   failed, some failed, or none were proposed.
2. Make it true: where no page was read, or some failed and none verified, the reason says
   that pages couldn't be read (a distinct reason code, worded in the web from
   `vocabulary.ts`), never `not_on_any_page`; `not_on_any_page` only when every proposed page
   was read and none shows the title. A partly read set says how many couldn't be read. The
   verdict stays `not_yet_found` (never "doesn't exist"); a failed run is never an empty
   success. Same in the live tool's printed result.
3. Tests at the domain level, the API and the web (Vitest). A migration only if a stored CHECK
   lists the reasons (next free: 0045). Regenerate the client if the API changes. ADR 0015
   one line. Register last.

## Rules
`env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` after each change. Don't run
integration or acceptance (the controller does). Edit/Write only (generators fine), explicit
pathspecs, no web, no live calls, no subagents, never start Docker, never read `.env` or
print an environment value, never push. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
Append "Follow-up: unread pages" to `/home/user/careerwright/planning/task-6e-report.md`;
reply with the short contract and your head SHA.
