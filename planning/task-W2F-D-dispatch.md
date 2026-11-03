# Task W2F, slice D: "Research this role" searches wider and never reads a home page (main tree)

Careerwright L0. The product owner's re-test (3 November 2026): research of "Biodiversity net
gain officer" read five pages and found the title on none. All five were the sites' home pages
(`https://studentjob.co.uk/`, `https://jobs24.co.uk/`, `https://environmentjob.co.uk/`,
`https://sercanto.co.uk/`, `https://recruitmenthub.solutions/`, from
`careerwright.acquisition_targets`): the search's own candidates were bare home pages
(`check_url` keeps paths), so no page could show the title. The product owner's yes, the same
day: "Widen it. Deeper search, up to 8 pages, no home pages. Still needs the exact title on 2
independent sites before saying found."

## Your tree
The main tree, `/Users/darianraad/Code/careerwright`, branch
`claude/confident-ramanujan-ux3saw`. Commit with a pathspec only; the controller also commits
ledger lines here, and the product owner's live session runs from images already built (don't
rebuild them; never run `make stop` or `make session`).

## Read first
`planning/implementer-contract.md`, `planning/task-W2F-brief.md` (its preamble's Global
Constraints and rulings), `CLAUDE.md` (Evidence, ADR 0009), ADR 0003 (search is Meta's own web
search tool), ADR 0009 (decision 12 and its amendments: the five pages), ADR 0015 decision 2,
`careerwright/evidence/search.py`, `search_agent.py`, `role_research.py`, the run's spend
reservation for a role search (the model registry and wherever a search's worst case is
priced), and the web's cost line for "Research this role" (`RunEstimate`).

## Deliver (role research only; discovery's source search is unchanged)
1. **Never a home page.** A role research candidate whose address is a site's root (path empty
   or "/", with or without a query) is never read: it can't describe one role. If every
   candidate is one, the result is the existing "the search found no page Careerwright could
   read" state, never "not yet found". The role search's instructions say so too: the page
   itself, never a site's home page. Tests.
2. **A deeper search**: role research's search context `medium` (from `low`) and up to 4 tool
   calls (from 2), in the one request; discovery's source search keeps its own settings. Its
   worst-case cost reservation and the cost shown before the click cover the deeper search
   (priced from the registry, never a guess; if Meta's price for `medium` isn't in the
   registry, stop and report, don't invent it).
3. **Up to 8 pages read** (from 5), so `MAX_CANDIDATES` must allow at least 8 real job
   pages after home pages are dropped (raise it if needed, with its bound in the prompt). The
   found rule is unchanged: the exact title, word for word, on two independent sources (or one
   official page).
4. A new role search prompt version; ADR 0009's amendment line (5 → 8 pages, the product
   owner's yes, 3 November 2026) and ADR 0003's line if the search settings are recorded there;
   the register rows your work touches (last commit).

## Rules
`make check` after each change. Focused integration runs (role research) under the lock, one
guarded command each (wait and retry if held; never remove a lock you didn't take):
`L=/Users/darianraad/Code/careerwright/.superpowers/acceptance.lock; mkdir $L && { cd /Users/darianraad/Code/careerwright/backend && uv run --locked pytest -m integration <files> > /private/tmp/claude-501/-Users-darianraad-Code-careerwright/51b74d1a-6cb8-4bb3-b832-9054484ac3c7/scratchpad/w2fd-int.log 2>&1; rc=$?; rmdir $L; exit $rc; }`
No whole acceptance. RED before GREEN. Edit/Write only (generators fine), explicit pathspecs,
no web requests, no live calls (the controller and the product owner run the live check), no
subagents, never read `.env` or print an environment value, never push. Commit messages end
with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
`/Users/darianraad/Code/careerwright/planning/task-W2F-D-report.md`; reply with the short
contract and head SHA.
