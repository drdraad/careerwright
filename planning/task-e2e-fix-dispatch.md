# Two browser-journey failures (main tree)

Acceptance run 8 at 81010d3 (this Linux host, the machine's Chromium via
`CAREERWRIGHT_CHROMIUM_PATH=/opt/pw-browsers/chromium`): pytest 466 passed; Storybook build
passed; Playwright 60 passed, 2 failed. The journeys hadn't run since Tasks 6d C, 6f, 6e and
10A landed, so these may be real. Log: `/tmp/acc8.log` (failures from line 239); traces under
`apps/web/test-results/`.

1. `e2e/conversation.spec.ts:318` [STATE-09] "the demo's way on names only what is in sight":
   after "What next?" in an answered workspace, `locator('.question')` still has 1 element
   (expected 0), line 345. Likely Task 6f's two new optional answers (what you're doing now,
   qualifications) left unasked in the test's `answeredWorkspace` fixture, or the demo now asks
   one again when it shouldn't (6f: "neither is asked twice"). Find which; fix the code if the
   product asks something it shouldn't, else the fixture (say why).
2. `e2e/storybook.spec.ts:44` [UI-04][UI-06]: the story `components--status-vocabulary-on-space`
   logs "Failed to load resource: 404". Find the missing resource and fix its cause.

## Your tree
Main tree `/home/user/careerwright`, branch `claude/confident-ramanujan-ux3saw`. Nothing else
runs there. Explicit pathspecs.

## Read first
`planning/env-cloud.md`, `planning/implementer-contract.md`, `task-6f-report.md`,
`apps/web/e2e/` (the two specs, `stack.ts`, the fixtures they use).

## Checks
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24 on PATH).
- Focused Playwright runs, under the lock with the build shim and the machine's Chromium, one
  guarded command each, for example:
  `export PATH=/tmp/ccr-shim:/opt/node24/bin:$PATH; L=/home/user/careerwright/.superpowers/acceptance.lock; mkdir $L && { cd /home/user/careerwright/apps/web && CAREERWRIGHT_CHROMIUM_PATH=/opt/pw-browsers/chromium pnpm run build-storybook > /tmp/e2e-fix.log 2>&1 && CAREERWRIGHT_CHROMIUM_PATH=/opt/pw-browsers/chromium pnpm exec playwright test e2e/conversation.spec.ts e2e/storybook.spec.ts >> /tmp/e2e-fix.log 2>&1; rc=$?; rmdir $L; exit $rc; }`
  Don't run the whole acceptance (the controller does). Never start or restart Docker, never
  prune, remove only `careerwright-l0-*` test containers your runs created.

## Hard rules
Edit/Write for every source change. No web requests, no live calls, no subagents, never read
`.env` or print an environment value, never push, pnpm only. Never weaken an assertion;
disclose any changed expectation with why. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
Append to `/home/user/careerwright/planning/task-acceptance-fix-report.md` a section
"Browser journeys"; reply with the short contract.
