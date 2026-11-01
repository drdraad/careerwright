# Acceptance fix on the Linux host, and the Linux-stack review's three fixes: report

Main tree, branch `claude/confident-ramanujan-ux3saw`. Commits:
- `fd4f939` Acceptance on the Linux host: a light worker health check, role pages keep their
  port for the worker's check, test fixes; the Linux-stack review's three fixes
- `61597ee` Register: DIV1-15, ARC1-08 and ACQ-05 record the acceptance fixes and the
  Linux-stack review fixes

## Result
The final whole `make acceptance` ran at `61597ee`, under the lock with the build shim
(`/tmp/acc9.log`):
- **pytest (integration, stack, owner commands): 458 passed, 0 failed, 0 errors** (21 min 31 s).
  Run 6 had 423 passed, 14 failed and 21 errors.
- **Storybook build: passed.**
- **Playwright: 2 passed, 60 failed. Blocked by the environment, not the code.** All 60
  failures say the same thing: `browserType.launch: Executable doesn't exist at
  /opt/pw-browsers/chromium_headless_shell-1248/...`. The pinned `@playwright/test` 1.64.0
  needs Chromium build 1248. This machine has only build 1243
  (`/opt/pw-browsers/chromium-1243`, `chromium_headless_shell-1243`). Installing the right
  build means a download (`pnpm exec playwright install chromium`), and my rules forbid web
  requests. **The controller needs to install it and re-run Playwright.**
- `make check` (Adzuna variables unset, Node 24) on the final tree: ruff and mypy clean;
  backend 2,061 passed and 8 skipped; fixture validator passed; client in sync; Biome and
  `tsc` clean; Vitest 471 passed.

## The failures: cause and fix (code or test, and why)

1. **Stack tests, 21 errors. Cause: the worker's health check timed out. Fixed in the code.**
   The dispatch suspected `migrate`. It wasn't: I started `careerwright-l0-stacktest` under
   the lock and found `migrate` exited 0 (`/tmp/diag-stack.log`). The worker was running
   fine: it logged "worker ready", and its heartbeat file was fresh. But Docker's health log
   showed every check ending with "Health check exceeded timeout (3s)". The check
   (`python -m careerwright.worker --check`) imported the whole worker first (DBOS, Pydantic
   AI, every run kind, with the project sources uncompiled). On this 4-core host that takes
   more than 3 s; locally the import alone took 3.3 s.
   Fix: a new standard-library-only `careerwright/identity/heartbeat.py` (`beat`, `check`,
   `python -m` entry point), which the worker loop uses. Compose's worker health check now
   calls it. `python -m careerwright.worker --check` still works and delegates to it. The
   stack test uses that form.
   New tests: `tests/domain/test_worker_heartbeat.py`, and an architecture test that the
   check's import closure is the module alone, with no vendor package.

   Then **two more stack failures appeared, both in the egress tests (demo and live). Cause:
   the test, which assumed Docker Desktop. Fixed in the test.** The positive control (the
   edge container dialling the host listener) got `gaierror`. On a Linux host,
   `host.docker.internal` does not exist, and a container cannot reach the host's
   127.0.0.1. On Linux, the listener now binds to the `edge` network's gateway address and
   the probes dial that. On the Mac it still uses `host.docker.internal` on 127.0.0.1. Every
   assertion is unchanged, and the positive controls now connect (edge in demo; the worker
   and acquisition worker in live), so the "blocked" results are real.

2. **`test_role_research.py`, 11 failures. Cause: the port check, not the proxy. Fixed in
   the code (10 tests); one test expectation was wrong (1 test).**
   - The 409 `no_pages` came from `role_research.pages_to_read`. It re-ran `check_url` with
     only ports 80 and 443 allowed, so it dropped the test source server's random port before
     any fetch. The proxy variables play no part: the refusal happens in the API before
     anything is fetched.
     Fix: `pages_to_read` now uses `acquisition.RECORDABLE_PORTS`, just as job acquisition
     records its targets. The restricted worker's own fetch check still refuses any port
     other than 80 or 443, and records it as a blocked attempt. In production nothing
     changes, because the search already excludes other ports (`search.py`, default
     `check_url`). No guard is weakened: the worker's check is the guard.
     TDD: the new unit test
     `test_the_pages_to_read_leave_the_port_to_the_restricted_workers_own_check` failed
     before the fix (RED) and passed after (GREEN).
   - **Changed test expectation:**
     `test_a_page_that_could_not_be_read_is_never_a_page_without_the_title[no page read]`.
     When every page answers 404, the acquisition run fails (`retrieval_failed`) by its
     documented contract: `publish_acquisition` says "Never an empty success", which is a
     CLAUDE.md invariant too. So the research reads `reading_stopped`, never
     `not_yet_found`/`pages_unread`. The test had assumed the run completes, and Task 6e's
     report listed that assumption as unverified. The test now expects, for that case,
     `reading_stopped`, no reason, and the reading `failed` with `retrieval_failed`. The
     other two cases additionally assert the reading `complete` with no failure class. The
     test's purpose holds: an unread page is never "not on any page".

3. **`test_migrations.py::test_0040...`: a test bug. Fixed in the test.** It inserted a
   workspace on a fresh database with no actor. It now invites the owner first
   (`identity_store.upsert_actor`, as `seed_fixture` does). No assertion changed.

4. **`test_targets.py::test_a_chosen_occupation...`. Changed test expectation:** I added
   `"on_a_list": True` to the expected nurse target. The field is intended: Task 6e fix
   round 1 (review M2) added it to `TargetRecordOut`, and an occupation chosen from ESCO is
   on a list by definition (`TargetRecord.on_a_list`).

5. **`test_live_smoke_ledger.py`, 2 failures. Cause: the worker started slowly on this
   machine. Not the code, and not the shared actor-insert bug. Fixed in the test.**
   There was no foreign-key violation in these tests in run 6 or in my runs (the only one was
   item 3). In the first test the worker log was **empty**: the worker was still importing
   when the test killed it, about 6.5 s after starting it. So `calls.log` never existed, and
   that run stayed in the outbox. The next test's worker then picked it up as well, which
   gave 6 calls (9 in my rerun) against a limit of 3.
   Fix: `Worker.wait_ready()` in `tests/support/workers.py` waits for the worker's first good
   pass, using its heartbeat file, and fails if the worker exits first. Both tests call it
   before the smoke, so their sleeps time a running worker's calls. Assertions are unchanged.

6. **Not in the dispatch: `test_durable_runs.py::test_a_crash_after_a_recorded_failure...`**
   failed in run 6 with "worker ignored SIGTERM for 20s". It passed in my focused run and in
   both whole runs, so I treat it as a one-off and changed nothing. Watch for it.

## The Linux-stack review's fixes
- **M1 (safety):** `entrypoint.py` now requires a tmpfs. It reads the type of the mount in
  use at the private path from `/proc/mounts` (the last mount listed there wins), as the
  postgres script does. Any other mount, a disk volume for example, is refused with the
  existing message. Unit tests: the refusal cases add "mounted as ext4". A new test covers
  stacked mounts and paths. Test helper change: `started()` now gives `main` a fake
  `/proc/mounts` instead of patching `os.path.ismount`, and `mounted` became a file-system
  type. TDD: the code came first, so there was no RED.
- **M4 (safety):** `security_opt: no-new-privileges:true` is set on every service: the backend
  anchor (migrate, api, worker, acquisition, edge), postgres, auth and web. The stack test
  now also reads `NoNewPrivs` for each service process and expects `1`. This is a
  **strengthened assertion**, and it passed in both whole runs. The drop from root
  (`setuid`, `gosu`) still works under it.
- **M5 (truth):** ADR 0004's amendment now says:
  - The rootful Linux host was tested here.
  - Rootless Docker and Docker Desktop should work by reasoning but were not tested.
  - `userns-remap` hosts fail loudly at start.
  - Compose ignoring `uid/gid/mode` is what its documentation describes, and was not tested.
  - The new tmpfs and `no-new-privileges` behaviour, and what tests them.

## Rulings
- I kept `python -m careerwright.worker --check` (the stack test and the docstring use it)
  as a thin delegate, rather than removing it.
- The egress listener on Linux binds to the edge gateway address, not 0.0.0.0, so the test
  never listens on every interface.

## Disclosure
- One source change was not made with Edit/Write. I appended
  `test_only_the_mount_in_use_at_the_private_directory_counts` to
  `backend/tests/domain/test_container_entrypoint.py` with a shell heredoc. The content is as
  reviewed above, and it is lint-clean and passing.
- Docker use: one diagnostic script (`/tmp/diag/stack_diag.py`, outside the repository)
  started and tore down `careerwright-l0-stacktest` twice under the lock, plus focused runs
  and three whole runs, all under the lock with the shim. Nothing was pruned, and no
  `careerwright-l0-*` containers are left. The daemon was not touched.
- Whole run 8 (`/tmp/acc8.log`: 458 passed, then the same Playwright blocker) overlapped
  Task 7f's commits landing, so it is not the evidence. Run 9 at `61597ee` is.
- Live calls: none ($0). No web requests. No secret or environment value read or printed.

## Not run, blocked or open
- Playwright on this host: blocked until Chromium build 1248 is installed (see Result).
- The Mac (Docker Desktop) path: not run; it needs the product owner's machine.
- Review minors 2 and 3 (silent skips in the copy; the tmpfs-destination and `CapEff`
  assertions) are out of this dispatch and were not done.

## Paths a reviewer can skip
None generated. `apps/web/storybook-static/` and `test-results/` are build output from the
acceptance runs and are not committed.

## Browser journeys (acceptance run 8's two Playwright failures)

### 1. `e2e/conversation.spec.ts` [STATE-09] "the demo's way on names only what is in sight"
- Cause: the test's `answeredWorkspace` fixture ("every question the demo asks already
  answered") predates Task 6f. It sets the entry to "Help me explore" (`unsure`), and since 6f
  the demo asks an unsure person "What do you enjoy doing, at school, at work or in your own
  time?" (field `enjoyed_tasks`) before the practical questions. The fixture left that field
  unasked, so after "What next?" the demo rightly asked it and `.question` had 1 element.
- Ruling: the product is right, the fixture is stale. The demo asks the enjoy question only
  while `enjoyed_tasks` is unasked (`_first_unanswered` in `profile/fixture_interviewer.py`),
  so it is never asked twice. The two other 6f answers (what you're doing now,
  qualifications) are never asked by the demo, so they were not the cause.
- Fix: the fixture now answers `enjoyed_tasks` ("helping people"). No assertion changed.

### 2. `e2e/storybook.spec.ts` [UI-04][UI-06], story `components--status-vocabulary-on-space`
- Cause: the trace's console entry names `http://127.0.0.1:<port>/favicon.ico`. Storybook's
  `iframe.html` declares no icon, so the full Chromium this machine uses
  (`CAREERWRIGHT_CHROMIUM_PATH`) asks for `/favicon.ico` on its first page, and the static
  build has none (it has `favicon.svg`). Only the first story hit it: the browser asks once.
- Fix: new `apps/web/.storybook/preview-head.html` declares the build's own
  `./favicon.svg` as the frame's icon (checked in the rebuilt `storybook-static/iframe.html`).
  The test and its static server are unchanged.

### Checks (final code)
- Focused Playwright, under the lock, with the build shim and the machine's Chromium:
  `pnpm run build-storybook` then `pnpm exec playwright test e2e/conversation.spec.ts
  e2e/storybook.spec.ts`: **12 passed** (both previously failing tests included). Lock
  released; no `careerwright-l0-*` containers left.
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24): **rc 0**; pytest
  2,159 passed, 8 skipped; Vitest 45 files, 471 passed; lint, types, client drift clean.
- `make acceptance`: not run, the controller runs acceptance.

### Follow-up: [STATE-09] failing later, at the second "Skip" reply (acceptance run 9)
- What the trace shows: the "Skip" message was never posted. Only one turn was POSTed (the one
  for "What next?"). When the test filled "Skip", the field still held "What next?", and Send was
  `aria-disabled`. Its reason was "Careerwright is still replying.": the reply's words were
  already shown, but the turn list had not yet marked the turn finished. The click sent nothing.
  When that first send settled, the field was emptied, and "Skip" with it.
- Product cause (a lost input): `Conversation.tsx` `send` cleared the field with
  `text === message.trim()`, where `message` was the field's value when sending began, which
  always equals the sent text. So it emptied the field even when the person had typed a new
  message while the first was on its way. Fix: it now compares against the field's value at
  that moment (`setMessage(current => current.trim() === text ? "" : current)`). Only the words
  that were sent are cleared.
  RED then GREEN: the new `YouChapter.test.tsx` test "[STATE-09] a reply typed while the last
  one is on its way is kept…" failed first (the field was empty, not "Skip"), then passed.
- Test cause: the helper clicked Send while the product was blocking it on purpose, with a
  stated reason. Blocking a send while a turn finishes is intended. `send()` in
  `e2e/conversation.spec.ts` now waits until Send is no longer `aria-disabled` (up to 60 s)
  before clicking, as a person would. This waits longer; it does not loosen any assertion. No
  expectation changed.
- Why my first run passed: timing. The turn usually finishes before the next fill.
- Checks: `e2e/conversation.spec.ts` run 3 times in a row under the lock (build shim,
  machine Chromium): **11 passed** each time. Lock released, no `careerwright-l0-*`
  containers left. `make check` rc 0 (pytest 2,159 passed; Vitest 45 files, 472 passed).
  `make acceptance`: not run, the controller runs acceptance.
