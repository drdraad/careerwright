# Make acceptance pass on this Linux host (main tree)

The first full `make acceptance` on this Linux Docker host after the Linux-stack change (run 6,
at 7a17a65): 423 passed, 14 failed, 21 errors (21 min). Log: `/tmp/acc6.log` (read it with
grep and line ranges; it is long). Playwright and Storybook did not run (pytest failed first).

This round also carries the Linux-stack review's three fixes (`planning/task-linux-stack-review.md`):
M1 (safety: `entrypoint.py:77` must check the private folder is tmpfs, not just a mount),
M4 (safety: `no-new-privileges` in compose where it costs nothing), M5 (truth: ADR 0004's
amendment states an untested Compose behaviour as fact and omits that userns-remap hosts
refuse to start; make it true).

## Your tree
Main tree `/home/user/careerwright`, branch `claude/confident-ramanujan-ux3saw` (head 39e2176).
Explicit pathspecs. No other implementer runs now.

## Read first
`planning/env-cloud.md`, `planning/implementer-contract.md`, the reports of the pieces whose
tests fail (`task-6e-report.md`, `task-6f-report.md`, `task-linux-stack-report.md`), and the
reviews named above.

## The failures (each: find the cause; fix the code if the code is wrong, the test if the test
is demonstrably wrong; say which and why)
1. **Stack tests, 21 errors:** `docker compose up … postgres auth edge api acquisition worker
   web` — the `migrate` service exits non-zero (log line ~53 on). Get migrate's own logs
   (start the `careerwright-l0-stacktest` project yourself under the lock if needed) and fix.
   Likely in the new entrypoint/tmpfs path or the datasets mount; prove it.
2. **`test_role_research.py`, 11 failures:** `PROPOSAL_NOT_AVAILABLE`, "no page Careerwright
   could read", `no_pages`, 409. Is the acquisition worker in the integration setup reaching the
   test's fake pages? Check whether this container's `HTTPS_PROXY`/`HTTP_PROXY`/`NO_PROXY`
   environment leaks into a client that should ignore it (environment-specific), or the code is
   wrong. If it is the environment, fix the test isolation (clear the proxy variables in the
   fixture), never the product's guard.
3. **`test_migrations.py::test_0040_gives_every_stored_profile_both_new_answers_not_yet_asked`:**
   ForeignKeyViolation, the workspace's owner actor isn't inserted first. A test bug from 6f.
4. **`test_targets.py::test_a_chosen_occupation_is_stored_with_the_choice_and_the_pack_target_it_covers`:**
   the response now carries `on_a_list: True` (6e's fix round): update the expectation if the
   field is intended (check 6e's report), and say so.
5. **`test_live_smoke_ledger.py`, 2 failures:** `calls.log` missing, `3 >= 6`, and an FK
   violation in the same tests. Find whether it is timing on this machine, the shared
   actor-insert bug of item 3, or the code.

## Checks
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24 on PATH) after each change.
- Focused integration and stack runs, and finally one whole `make acceptance`, only under the
  lock with the build shim, in one guarded command each:
  `export PATH=/tmp/ccr-shim:/opt/node24/bin:$PATH; L=/home/user/careerwright/.superpowers/acceptance.lock; mkdir $L && { env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY <command> > /tmp/<name>.log 2>&1; rc=$?; rmdir $L; exit $rc; }`
  Never `docker system prune`; remove only `careerwright-l0-*` test projects' containers and
  volumes, and only ones your runs created. Don't start or restart the Docker daemon: if it is
  down, report it.
- Report the final acceptance counts, including Storybook and Playwright.

## Hard rules
Edit/Write for every source change. No web requests, no live calls, no subagents, never read
`.env` or print an environment value or secret, never push, pnpm only. Disclose every changed
test input or assertion. The register last. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
`/home/user/careerwright/planning/task-acceptance-fix-report.md`; reply with the short contract.
