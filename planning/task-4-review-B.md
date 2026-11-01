# Task 4 review, half B (integration, e2e, build, docs, Sprint 1 review)

Reviewer: independent task reviewer (half B: everything outside `apps/web/src`). Range
`eb70b6a..a939024`. The diff (3,504 lines) was read in four passes: build/e2e, backend/stack,
ADR/dependencies/design/register, then the Sprint 1 review/runbook. I sampled 9 screenshots:
all three viewports, the refused state, the drawer at each viewport, and Sprint 0 references
for comparison. I ran no suite, started no Docker stack and made no live Meta call.
Read-only, with one exception: a crop of one screenshot in the scratchpad to confirm the
overlap in Important 1.

Named-risk checks (one focused check each):

- **Same-origin proxy.** I read `apps/web/src/lib/apiProxy.ts`, `src/app/api/[...path]/route.ts`,
  `src/proxy.ts`, `src/lib/requestPolicy.ts`, `src/lib/config.ts`, the API settings
  (`backend/src/nessa/config.py:99-140`) and `compose.yaml:75-80`.
  - The upstream is a fixed origin from validated configuration.
  - The path must start with `v1`. Empty, `.` and `..` segments are refused, and every
    segment is `encodeURIComponent`-ed, so the proxy is not an open relay or SSRF.
  - Request and response headers are allowlisted. No X-Forwarded-*, cookies or set-cookie
    pass, and the API runs `--no-proxy-headers` and reads the socket peer
    (`guard.py:47`), so the client check cannot be spoofed.
  - `NESSA_ALLOWED_HOSTS` and `NESSA_ALLOWED_ORIGINS` are unchanged in this range. Origin is
    forwarded verbatim. Host is checked by the web server for every route except `/healthz`.
  - `compress: false` and `body` pass-through are in place. Unbuffered delivery is not
    proven end to end (Important 2).
- **Loopback and BND1-11.**
  - `web` has no `ports:` and sits on `internal` only (`compose.yaml:139-158`). The edge
    publishes 127.0.0.1 only.
  - The demo probe now covers `web`: TCP to TEST-NET, the host listener, and DNS
    (`test_local_stack.py:183-202`). The live probe covers `web` too, host only (Minor 8).
  - Next.js telemetry is off in the Dockerfile build and runtime stages and in the
    Makefile. Storybook telemetry is off in `.storybook/main.ts`. The host `next`
    scripts are the one gap (Minor 6).
- **Playwright journey.** It follows the brief step for step: sign in, edit and save,
  source drawer, fixture route B with focus return, full `stop`/`demo` with the page open,
  reload of the same address, and no external request. It uses no fixed sleeps,
  `retries: 0` and one worker. The keyboard suite covers the rail (every chapter), skip
  link, drawer (Enter, Close, Escape, focus return) and phone menu and sheet. Heights are
  measured under `reducedMotion: "reduce"`, so the 212 px exact check is stable.
- **Generated client.**
  - `scripts/generate-client.mjs --check` regenerates into a temporary directory and
    compares bytes, including missing or extra files. It runs in `make check`
    (`package.json:22`, `Makefile:240`).
  - `tests/api/test_openapi.py` asserts the served schema equals the offline one, and
    the committed `openapi.json` equals `render()`.
  - The stack test compares the running API's schema with the committed copy.
- **Dependencies.**
  - Every `package.json` pin is exact, `packageManager` is pnpm@10.33.2 and the lockfile
    is committed.
  - Every direct dependency is in `docs/dependencies.md` with a licence.
  - `next` was published 2026-10-14T17:43Z and first committed at 2026-10-28T05:16Z, so
    "13.5 days" is accurate.
  - I fetched GHSA-2464-fhr4-w9xw: it is critical, affects `next` 16.0.0–16.4.0 and is
    patched in 16.4.1, as claimed. Its vector is the image optimiser, which this app
    disables (`images.unoptimized`), but pinning the patched release is still right.
  - The undici/jsdom acceptance is reasoned: dev only, no network in unit tests, and the
    fix was under 14 days old.
- **Docs honesty.**
  - H-01 is "Not run — requires human" with a checklist and a blank score table.
  - H-03 and H-04 are recorded as not run. Their owners are Sprints 9 and 8–9
    (`requirements-register.md:620-621`), so they need no Sprint 1 checklist.
  - The agent pre-review is labelled "not a score", and the reviewer is named as the
    implementing agent.
  - Every CLAUDE.md command exists. I did not flag the retry-owner sentence, as instructed.
- **Screenshots.** The shell matches the references' rail, strip, cards, drawer and
  typography. The conversation failure reference now has one primary action ("Try
  again", with Send secondary) at 1440 px. I found overlapping text in the evidence drawer
  at 1440 and 768 (Important 1).

### Spec Compliance
- ❌ Issues found:
  - The first visual review package omits the states the Sprint 1 shell already supports
    (empty, stale, unavailable, failed). This is against plan section 5 ("Review default,
    selected, empty, partial, stale, unavailable and failed states for the components that
    support them … Never approve only the attractive fixture"). The gap is attributed to
    later sprints (`docs/reviews/sprint-1.md:158`, `docs/requirements-register.md:593`).
    See Important 3.
  - "API/events routed through the web origin": events through the proxy have no
    end-to-end delivery evidence (Important 2).
  - Everything else in my half matches the brief: the Playwright journey, keyboard
    reachability with focus return, no external request in fixture mode, the generated
    client with its drift check, the CLAUDE.md commands, and the Sprint 1 review with
    screenshots at three viewports, an agent pre-review and the R2 checklist.
- ⚠️ Cannot verify from diff (half A, `apps/web/src`):
  - Storybook story content: the seven named states and 26 stories.
  - `StatusBadge` and vocabulary completeness, and enums taken only from the generated
    client.
  - The ProfileEditor stale/409 rebase path and the money parsing.
  - The `events.ts` reconnect, re-auth and back-off logic.
  - The fixture adapter's SHA-256 pin and typed failure, and that no component hard-codes
    financial examples.
  - The phone sheet's More/Less, drag and ARIA wiring.
  - Calm mode.
  - The CSP's `'unsafe-inline'` script source.
  - The CSS root cause of Important 1.

### Strengths
- The proxy is narrow and well reasoned:
  - fixed upstream, `v1`-only, dot-segment rejection, allowlisted headers both ways, 502
    without an envelope when the API is unreachable, `Location` rewritten;
  - the API allowlists are genuinely unchanged, and the API keeps `--no-proxy-headers`;
  - the Host check lives where the browser's Host is still visible.
- BND1-11 is closed with a real probe. The `web` container runs the same TCP, host-listener
  and DNS probe as the backend, against an edge positive control. DNS assertions were also
  extended to `auth`.
- `test_the_web_origin_serves_the_app_and_forwards_only_the_api_with_its_checks`
  (`test_local_stack.py:364`) exercises CSP, a foreign Host, an unauthenticated
  pass-through with its envelope and correlation ID, the non-`v1` refusal and a foreign
  Origin on the real stack.
- Contract drift fails three independent ways, and the operation IDs are named and tested
  for uniqueness.
- The e2e harness is isolated: its own project, ports and temporary `NESSA_HOME`. `down`
  refuses the default project (`tools/stack.py`), and teardown removes volumes and the home.
- The JS excluded-technology check covers all three pnpm locks and has a reader test with
  a non-empty guard.
- The human gates are honest throughout. The `next` age exception is narrow, dated and
  verifiably justified.

### Issues

#### Critical
None.

#### Important

1. **Overlapping text in the evidence drawer at 1440×900 and 768×1024. The review package
   does not report it and claims a match.**
   - **Where:** `docs/reviews/sprint-1/screenshots/you--source-drawer--1440x900.png` and
     `you--source-drawer--768x1024.png`. In the drawer's facts, "Source" overprints
     "Synthetic fixture persona P01…", and "SHA-256" overprints the hash; I confirmed this
     on an enlarged crop. The cause is in half A: `.kv` uses
     `grid-template-columns: minmax(0, 1fr) auto` (`apps/web/src/app/globals.css:485-500`).
     The `auto` value column takes the long value's width and squeezes the `dt` column to
     zero, so labels spill into values. The same `.kv` is used by
     `RoutePreview.tsx:53,83,102` and `ChapterView.tsx:67`, so any long value overlaps
     its label.
   - **Why it matters:**
     - The provenance line (source and hash) is the drawer's purpose and is unreadable.
     - "Nothing clipped or overlapping" is a stated acceptance concern, and the automated
       checks only measure page-level horizontal overflow.
     - `docs/reviews/sprint-1.md:149` says the drawer "match[es]" the references, and the
       agent pre-review (`sprint-1.md:215-235`) misses the defect. A human reviewer would
       be handed a package whose checks all say pass.
   - **Fix:**
     - Use `grid-template-columns: max-content minmax(0, 1fr)`, or stack `dt` above `dd`
       below a width.
     - Keep `overflow-wrap: anywhere` on the hash.
     - Recapture the package and add the defect, then its fix, to the visual findings.
     - Consider an automated check that no text box in `.kv` intersects its sibling.

2. **No evidence that a status event is delivered through the web origin. A buffering or
   non-delivering proxy would pass every test and show "Live".**
   - **Where:**
     - The only proxy streaming test (`apps/web/src/lib/apiProxy.test.ts:86-112`) mocks
       `send` and reads a complete body.
     - The UI reports "Live" on an accepted response, before any event
       (`src/lib/events.ts:75-105`).
     - The journey only asserts "Live" and "Reconnecting" (`e2e/journey.spec.ts:66-80`).
     - The stack test does not open the stream through the web origin.
     - The two-tab test (`e2e/access.spec.ts:104-145`) never checks that tab 2 learns of
       tab 1's save.
   - **Why it matters:**
     - The brief requires "API/events routed through the web origin" with resumable status
       events.
     - STATE-07 is marked verified on the journey (`requirements-register.md:410`).
     - If Next's route handler, compression or the edge ever buffered `text/event-stream`,
       pages would show stale data labelled "Live". That is a failure presented as a
       success (GC6), and no check would notice.
   - **Fix:** add one end-to-end assertion that an event crosses the proxy promptly. For
     example, open two pages on the fixture workspace, save in one, and expect the other's
     strip to show the next version without a reload within a few seconds. Alternatively,
     a stack test reads the first `id:` frame from `{web}/api/v1/workspaces/{id}/events/stream`
     after a `reset-demo`, with a short timeout.

3. **The first visual review package captures only happy paths and the refused account.
   It omits the empty, stale, unavailable and failed states the shell already has, and
   attributes the gap to later sprints.**
   - **Where:** `apps/web/e2e/visual.spec.ts:1002-1046` holds 10 shots: sign-in, six
     chapters, two drawers, not-invited.
   - **Not captured:**
     - Ben's empty home ("No workspaces yet") and Routes in a non-fixture workspace (the
       explained empty state). Both are reachable today.
     - The stale-save notice: the two-tab 409 is already driven in `access.spec.ts`.
     - The unavailable strip ("Reconnecting" / "Couldn't refresh") during a `stop`.
     - The failed states: another person's workspace "can't be shown", and a failed
       fixture or drawer load.
   - **The docs:** `docs/reviews/sprint-1.md:158` and `requirements-register.md:593` say
     stale and unavailable states "need data from later sprints". That is true for chapter
     content but not for these shell states. The H-01 checklist (`sprint-1.md:262`) points
     the human only at the screenshots, not at the Storybook failure stories.
   - **Why it matters:**
     - Plan section 5 requires the screenshot approval to cover these states "for the
       components that support them" and says "Never approve only the attractive fixture".
     - This is the package H-01 will score.
   - **Fix:**
     - Add those shots to `visual.spec.ts`, at least: empty home, empty Routes, stale save,
       reconnecting or could-not-refresh, and not found.
     - Recapture, and correct the two "later sprints" sentences.
     - Or, at minimum, list the Storybook states in the H-01 checklist and say exactly
       which states are not in the screenshots and why.

#### Minor

1. **Wrong capture count.** `docs/reviews/sprint-1.md:54,71,217` (and the report) say "33
   captures (11 states × 3 viewports)". The package holds 30 PNGs: 10 states × 3, plus 3
   JSON files, and each `checks-*.json` lists 10 entries. Correct it to 30.
2. **Stale comment in the visual spec.** `apps/web/e2e/visual.spec.ts:6` says it writes
   "checks.md", but it writes `checks-<viewport>.json`.
3. **Misleading runbook grouping.** `docs/runbook.md:48-50` places `pnpm run
   review-screenshots` under "For UI work without Docker". That command runs the
   Playwright global setup, which builds and starts the `nessa-l0-webtest` Compose stack.
   Say that it needs Docker.
4. **A journey comment claims more than the test checks.** `apps/web/e2e/journey.spec.ts:71`
   says the work stays on screen "marked as not refreshed", but nothing asserts a
   not-refreshed marker during the outage. Line 79's `toBeHidden()` passes even if the
   notice never appeared. Either assert the outage marker or correct the comment.
5. **Unused helpers.** `apps/web/e2e/helpers.ts:68` (`expectNoHorizontalOverflow`) and `:85`
   (`expectChapter`) are never used. `expectChapter`'s docstring also says it checks
   "live updates are connected", which it does not. Remove both.
6. **Host `next` scripts bypass the telemetry opt-out.** `apps/web/package.json:12-14`
   (`dev`, `build`, `start`) are undocumented and refuse to serve without the `NESSA_*`
   variables. They run the Next.js CLI without `NEXT_TELEMETRY_DISABLED`, which is set
   only by the Makefile and the Dockerfile. SEC-04's "Next.js telemetry off" therefore
   holds only on those paths. Prefix them with `NEXT_TELEMETRY_DISABLED=1`, or remove the
   unused ones.
7. **The `next` exception reads as settled and has no cleanup.**
   `docs/adr/0005-web-app-and-same-origin-api.md:3` says "Accepted", but ruling 2 (the
   age exception) still awaits controller confirmation per the report. There is no
   follow-up to drop `minimumReleaseAgeExclude` (`apps/web/pnpm-workspace.yaml:7-16`)
   once `next` 16.4.1 turns 14 days old at 2026-10-28T17:43Z. `CLAUDE.md:86` states "at
   least 14 days old" without the exception. Mark the exception provisional and record
   the removal step.
8. **The live-mode web probe asserts less than the demo probe.**
   `backend/tests/stack/test_local_stack.py:219-221` only checks `host`, not
   `outside`/`dns`. Add both assertions so live mode cannot open a route for `web`
   unnoticed.
9. **One test has no register tag.**
   `backend/tests/architecture/test_boundaries.py:263`
   (`test_the_pnpm_lock_reader_finds_scoped_and_plain_names`) has no `req` marker.
   CLAUDE.md asks for every test to be tagged; tag it ARC1-01.
10. **A design deviation the pre-review did not list.** The phone sheet's peek
    (`routes--route-b--390x844.png`) shows a generic "Where this came from" heading, with
    the route's key figures below the peek. The reference peek
    (`docs/design/screenshots/route-comparison--default--390x844.png`) shows the route name
    and its readiness, direct-spend and economic-cost figures. Add it to the visual
    findings for H-01.

### Assessment
**Task quality:** Needs fixes

**Reasoning:** The integration is sound and well evidenced. The proxy keeps the API's
checks meaningful, BND1-11 is closed with a real probe, the drift check is in `make check`,
and the human gates are honest. However:

- the review package ships an overlapping-text defect in the evidence drawer, unreported;
- event delivery through the web origin is untested end to end;
- the first visual review package omits failure and empty states the shell already
  supports, which plan section 5 requires.
