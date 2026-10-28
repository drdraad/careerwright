# Sprint 1 review: a polished local walking skeleton

- Date: 2026-10-28. Branch `l0-local-release`.
- Reviewed revision: `94c0015`, the last Task 4 commit that changes code or tests (after
  review fix round 1). `make check` and `make acceptance` ran on it. The screenshots were
  captured from the same app code; `94c0015` changes one browser-test expectation. The
  commit that updates this review changes only docs.
- Sprint 1 commits: `a31fd42`..`eb70b6a` (Task 3: S1.1–S1.3, the platform),
  `a5d6a7c`..`a939024` (Task 4: S1.4–S1.5, the web shell, and this review) and
  `aea2e32`..`94c0015` plus the docs update (Task 4 review fix round 1).
- Reviewer: the Task 4 implementing agent. It is not independent of the work reviewed. A
  separate reviewer is dispatched after this task, and the human gates below remain open.

## Outcome

The card's demonstrable outcome is shown end to end, from the UI, by an automated browser
journey on a fresh stack (`apps/web/e2e/journey.spec.ts`):

1. Start Nessa from the documented commands.
2. Sign in as a seeded local identity (Ada) through the Auth emulator.
3. Edit the profile (a second work area, weekly study hours) and save it as the next
   version.
4. Inspect where an answer came from, then a fixture route (TRACE-01 route B) in the
   evidence drawer.
5. Stop and restart every service while the page stays open. The page keeps its work on
   screen and reconnects by itself.
6. Reload the same address: it reopens the same workspace and version.

Throughout, the browser contacts nothing but the web origin and the loopback Auth emulator.

The six-chapter shell follows the Sprint 0 references: ink rail, raised strip, light reading
surfaces, cards, the evidence drawer and phone bottom sheet, the status vocabulary and the
two licensed fonts. Only You (the profile) and Routes (the labelled fixture preview) have
content. Roles, Skills, Options and Plan show what they will hold, which answers they
depend on and what to do next, because their features belong to later sprints.

**Human design approval: not run, requires a human (H-01).** The screenshots and the agent
pre-review below are evidence for that review, not the review itself (ruling R2).

## Card deliverables and acceptance

| Card item | Result | Evidence |
|---|---|---|
| S1.1 command contract, Compose, health checks, migrations, seeding, identities, fail-closed configuration | **Done** (Task 3). Task 4 adds the web service to every stack and extends `make setup/check/acceptance` | `docs/reviews` of Task 3 in its report; `docs/runbook.md`; `BND1-14` |
| S1.2 versions, expected-version writes, sources, envelopes, runs, outbox, row-level ownership | **Done** (Task 3). The UI now uses them: expected-version saves, the stale path, source references in the drawer, envelope codes in words | ADR 0004; `ProfileEditor.test.tsx`, `access.spec.ts` |
| S1.3 encrypted key storage, revoke, rotate, budget reservation, redacted logging | **Done** (Task 3, backend). **No key UI yet**: MODEL-07's consent UI is not in this task's brief; the controller assigned it to T6 | ADR 0004; register MODEL-07 |
| S1.4 rail, strip, drawer, cards, buttons, form controls, status vocabulary, mobile layouts, tokens, Storybook states | **Done** | `apps/web/src/components/`, 26 Storybook stories incl. the seven named states, each axe-clean (`e2e/storybook.spec.ts`); UI-04 |
| S1.5 real API and database, fixture adapter with labelled content, no hard-coded financial examples, resumable events with reconnect | **Done** | the journey; `src/lib/fixtures/trace.test.ts`; `src/lib/events.test.ts`; ADR 0005 |
| Fresh database migrates; populated fixture database upgrades without losing the selected snapshot | **Passed** (Task 3 tests, re-run here) | `tests/integration/test_migrations.py` |
| Profile updates survive reload and restart | **Passed** | the journey (UI); `test_a_profile_edit_survives_a_full_stop_and_start` (API) |
| A stale version is rejected | **Passed** | `access.spec.ts` (two tabs, real API); `ProfileEditor.test.tsx`; DUR-04 |
| Other workspace's and uninvited requests fail (API, stream, cache, worker) | **Passed** (Task 3), and from the UI: Ben gets "not found" for Ada's workspace, the uninvited account is refused | `access.spec.ts`; SEC-01 |
| Key redaction across errors, history and exports | **Passed** (Task 3) | MODEL-06 |
| An unauthorised local origin cannot trigger authenticated changes | **Passed**, now also through the web origin: a foreign or missing Origin is refused and nothing changes | `access.spec.ts`; `test_the_web_origin_serves_the_app_and_forwards_only_the_api_with_its_checks`; BND1-13 |
| The shell passes the first visual review on desktop and mobile | **Not run — requires human** (H-01). Automated checks pass on 48 captures (16 states × 3 viewports); agent pre-review below | `docs/reviews/sprint-1/screenshots/` |
| Keyboard reaches every chapter and the evidence drawer, with correct focus return | **Passed** | `e2e/keyboard.spec.ts` (desktop rail, skip link, drawer, phone menu and sheet); `EvidenceDrawer.test.tsx` |
| Fixture mode makes no external request after setup | **Passed** | web container in the egress probe (BND1-11); the journey's request log; CSP |
| The route preview is clearly fixture-driven and does not claim the production solver exists | **Passed** | "Fixture preview: not your routes" on the page and "Not a route Nessa computed for you" in every route's drawer; shown only in the fixture workspace |

## Checks run on the final candidate (`94c0015`)

Machine: macOS arm64, Docker 29.1.2 (aarch64), Node 24.11.1 (host) and 24.22.1 (images),
pnpm 10.33.2, uv 0.9.18, Playwright 1.64.0 with Chromium 1248.

| Command | Result |
|---|---|
| `make check` | Backend: ruff format and lint clean, mypy clean (118 files), pytest 210 passed (115 deselected), fixture validator `passed`. Web: generated client matches the backend's OpenAPI document, Biome clean (91 files), `tsc` clean, Vitest 142 passed in 19 files. About 7 s |
| `make acceptance` | pytest `-m "integration or stack"`: 115 passed in 190.8 s (real PostgreSQL 16.15, DBOS, the emulator, the Compose stack incl. the web container). Storybook build succeeded (26 stories). Playwright: 17 passed in 1.2 min on a fresh `nessa-l0-webtest` stack (access 5, journey 1, keyboard 4, session 3, Storybook 1, visual 3). No test project left behind. One line of noise: Node's notice that `NO_COLOR` (set in the host shell) is ignored because Playwright sets `FORCE_COLOR`. The run before it, on `be3e256`, failed only the journey, whose expected drawer wording was out of date; `94c0015` corrects it |
| `cd apps/web && pnpm run review-screenshots e2e/session.spec.ts` | 6 passed: 48 captures (16 states × 3 viewports) with no axe violation, no horizontal overflow, no label overprinting its value, no unexpected console error and both fonts loaded (`checks-*.json`), plus the three session tests. Captured from the same app code as `94c0015` |
| `playwright test e2e/journey.spec.ts --repeat-each=4` | Earlier round (`1f76506`): 4 passed. This was run because an earlier `make acceptance` (on `a08643a`) failed the journey once: the test's live-state check matched "Reconnecting", the page reloaded before re-authenticating after the restart, and the restarted emulator, which re-imports its seed and ends earlier sessions, signed it out. The check is now exact and the journey starts from a reset fixture |
| `cd docs/design && pnpm run contrast` | Earlier round: 68 of 68 pairs pass (three added for the shell). Fix round 1 adds no colour pairing |
| `cd docs/design && pnpm run screenshots` | Earlier round: 18 of 18 captures pass after the conversation fix. `docs/design` is unchanged since |
| `cd apps/web && pnpm audit` | Earlier round: 8 advisories remain, all in `undici` through `jsdom` (dev only, unit-test DOM); accepted in `docs/dependencies.md`. No dependency changed since |

Not run: live Meta calls (none needed; none made, so no cost to ledger), `make live-smoke`,
WebKit and Safari, VoiceOver, amd64 images, 200 % zoom.

## The six questions

**1. Does the journey make sense from entry to the latest outcome?** Yes, for what exists.
- Sign-in, the workspace list, You (edit and save), the evidence drawer, the fixture route
  and recovery after a restart all work from the UI.
- A missing-data path is visible: a chapter whose starting answers were never asked says
  which ones ("Needs answers in You first", then "Not asked yet: …"). Unknown, Skipped
  and Prefer not to say are answers: they never block a chapter and never read "not
  answered". A missing budget only makes Options less precise, and says so. An Unknown
  answer reads "Unknown" or "Not confirmed", never £0.
- Failure paths are visible:
  - A refused account says it is not invited.
  - Another person's workspace is "not found".
  - A save based on an older version keeps the edits and names what changed. Answers the
    person did not edit take the newer version's values; where both changed, the edit is
    kept and the newer value is shown beside it.
  - An unreachable API keeps the last loaded work on screen and says it could not refresh.

The journey ends where the product currently ends: there is no conversation, research or
route search yet, and the chapters say so.

Result: **passed (UI, automated)**.

**2. Do shared concepts mean the same thing everywhere?**
- **One state vocabulary:** the UI takes `WorkState`, `FieldState`, `DataMode` and
  `ErrorCode` from the generated client and maps every value in one table each, so they
  cannot drift.
- **Unknown, skipped and prefer-not-to-say** stay distinct from zero in the form, the strip
  and the chapters.
- **Conditional** readiness is a gate glyph with its condition in words. **Stale** (the
  stale-save notice) uses sand and a clock; **failed** uses a red edge and a cause.
- **Economic cost** is labelled as such on the fixture preview. Direct spending is a
  separate figure.
- **Synthetic** is a persistent pill in the strip and the phone top bar.

Hazard noted: the fixture preview's layers are the fixture's stated `expected.fronts`, not
a computation. The page and the drawer say so, and nothing in TypeScript ranks routes.

Result: **passed**.

**3. Can a consequential displayed claim be traced to source, version, confirmation and
calculation?** Traced: the strip's "Up to £1,500" in the fixture workspace.
- It is `direct_spend_cap = {minor_units: 150000, currency: GBP}` in profile version 1,
  read through `GET /v1/workspaces/{id}/profile` (generated client, row-level secured).
- That field cites the source reference "Synthetic fixture persona P01 (supplied M0 pack)",
  `fixtures/m0/personas/P01.json`, SHA-256 `03e72eef…518e`. The drawer shows it, and the
  hash matches `fixtures/README.md`.
- The seed copied it from `direct_spend_cap_minor: 150000` without arithmetic.
- `formatMoney` renders minor units with integer arithmetic (`money.test.ts`).
- Confirmation: the fixture's synthetic confirmation only. A real person's edit becomes a
  new version citing a "direct entry" source, which the journey shows in the drawer.

Route B's "minimum prefunded cash balance of £4,850" traces to `worked_trace.json`
`expected.print_snapshot.minimum_prefunded_cash_minor`, read under its pinned hash.

Result: **passed for the profile; fixture-level for routes** (the product calculation is
Sprint 5–6).

**4. Are module and process boundaries intact?**
- **Backend:** unchanged apart from named operation IDs and an offline OpenAPI export. The
  architecture checks pass and now cover the JavaScript lockfiles.
- **Web app:** it holds no business rule. It shows the API's values, maps codes to words
  and computes no rank, layer or affordability.
- **Fixture adapter:** the only port, at a real I/O boundary (the file system). It fails
  typed and never fills a live workspace.
- **Process boundary:** the web container joined the internal network with no route out.
  It forwards only `/api/v1` with the browser's Origin unchanged, and the API's Host,
  Origin and client checks are unchanged and still refuse.
- **State:** one store for server state (TanStack Query); the editor draft and drawer are
  local interaction state.
- No hidden fallbacks: an unreachable API is a stated state. After a stale save the editor
  rebases on the newer version and names every answer that version changed, so nothing is
  merged or reverted silently.

Result: **passed**.

**5. Is the interface coherent and polished?** Compared with the Sprint 0 references, the
rail, strip, cards, status words and typography follow them (screenshots against
`docs/design/screenshots/`). The drawer did not, and the agent pre-review missed it: the
Task 4 review found its labels overprinting long values at 1440 and 768 px. That is fixed
and now checked on every capture. Differences and defects are listed under "Visual
findings". Keyboard focus is tested. Human scores: **not run — requires human (H-01)**.

**6. What exact evidence establishes completion?** The commands and results above, on
`94c0015`. Known gaps:
- the consent UI for keys (MODEL-07);
- calm mode has no automated test (UI-05);
- 200 % zoom;
- chapter content states with no producer yet: partial results, zero results, the 100-job
  limit, and selected states in chapters without content (UI-11). The shell's empty,
  stale, unavailable and failed states are captured;
- human gates H-01, H-03 and H-04;
- amd64 images.

Next dependent milestone: Task 5 (Sprint 2: ESCO import, the InterviewTurn contract and the
model port), then Task 6 (the You chapter's conversation on this shell).

## Coherence question (Sprint 1 card)

**Trace one workspace through browser, API, database, outbox and worker.** The fixture
workspace, as the journey drives it:

1. **Browser:** `PUT /api/v1/workspaces/{id}/profile` with `expected_version`, an
   `Idempotency-Key` and the page's Origin.
2. **Web server:** forwards it to `api:8000` with the Origin unchanged.
3. **API:**
   - verifies the emulator token and the invitation;
   - runs `write_profile` inside `actor_transaction`, where row-level security scopes it
     to Ada's workspace;
   - inserts profile version N+1 with a direct-entry source reference, takes the next
     event sequence from the workspace row under the same lock, and stores the receipt.
4. **Event stream:** delivers `profile.version_created` with that sequence, and the page
   refetches.

The outbox and worker are not exercised by a profile write, because a profile write
creates no run. The run path (submit, outbox, DBOS worker, sealed output) is traced by
Task 3's durable tests. In demo mode the API refuses model runs (`MODEL_UNAVAILABLE`), and
the UI has no run trigger yet.

**Every record has an owner and a version.**
- The workspace has an owner and a version.
- Every profile is an immutable version with `created_by`.
- Every answer cites a server-assigned source reference.
- Events carry a per-workspace sequence.
- Receipts belong to their workspace.
- The UI shows the version in the strip and in "What we know".

**All six chapters share the same state vocabulary:** yes (question 2).

**Empty states explain what the user can do next:** yes. Each planned chapter names its
purpose, the answers it uses with their current state, and a "Review what we know" action;
the home page offers "New workspace".

**Duplicate state stores and placeholder abstractions eliminated:**
- **State stores:** server state lives only in the query cache, and the strip and chapters
  read the same queries. Calm mode is the only browser-stored preference; the rail's
  visited marks are per tab (`sessionStorage`).
- **Placeholder abstractions:** none were built. Chapters without features have no empty
  components, ports or stores. The fixture adapter is a real adapter with a failure
  contract.
- **One duplicate removed:** the stale-save path now fetches through the same query
  definition the shell uses (`profileQuery`), instead of a second, query-function-less
  copy.

Result: **passed**, with the outbox and worker traced by Task 3's tests rather than from the
UI (no run trigger exists yet).

## Visual findings

Agent pre-review (from the 48 captures; not a score). The first package held 30 captures (10
states × 3), not the 33 this review first stated.

Strong:
- The shell reads as the reference: one structural motif, the ink rail, sea-glass used only
  for the current chapter, the primary action and selection.
- The fixture route cards and drawer closely follow the route-comparison reference, layers
  are told apart by shape and words, and every route is labelled synthetic.
- Empty chapters are explained rather than blank, and so are the empty home and a new
  workspace's Routes.
- The stale save keeps the edits and names what changed; the unavailable state keeps the
  work on screen and says "Reconnecting" in the strip on every size, phones included.
- The phone sheet peeks at 212 px and expands; the tablet drawer is a full-height side
  sheet.

Weak:
- **You:** a long single-column form. The reference's two-column composition (conversation
  beside "What we know") waits for the conversation (T6). The field-state select beside
  each value adds visual weight; a human may prefer a quieter control.
- **Phone Routes:** the fixture notice and "What's being compared" fill the first screen,
  and the route cards start below the fold (as in the Sprint 0 failure state).
- **Strip:** it wraps to two rows on tablets and phones; on phones the workspace switcher is
  indented relative to the target.
- **Refused page:** "This account isn't invited" repeats as heading and alert title.
- **Failed load:** "Nessa's service isn't reachable" says to try again in a moment but
  offers no Try again action; the person has to reload.
- **Stale save:** in the captures, the field-level conflict ("Version 1 has … here") sits
  below the fold; only the notice that names the changed answers is on the first screen.
- **Width:** at 1440 px without the drawer, reading chapters leave a wide empty right
  margin (content is held to 760–1080 px).
- **Layers:** layers 2 and 3 share one grey and differ by shape and label (carried from
  Task 2 for H-01).
- **Motion:** none is visible in static captures. Calm mode is untested.
- **Phone route sheet peek:** the peek shows the generic "Where this came from" title, and
  the route's key figures start below it. The reference peek
  (`docs/design/screenshots/route-comparison--default--390x844.png`) shows the route name
  with its readiness, direct-spend and economic-cost figures.

Found by the Task 4 review or by its new captures, not by this pre-review, and fixed:
- **Drawer facts overprinted their values** at 1440×900 and 768×1024: "Source" over the
  persona's source name and "SHA-256" over the hash. The facts list sized its value column
  to the longest value and squeezed the label column to nothing. Labels now take their own
  width and values wrap (`max-content minmax(0, 1fr)`; the hash keeps
  `overflow-wrap: anywhere`). Every capture now also checks that no label's text meets its
  value's text (`overprinted` in `checks-*.json`).
- **A failed or loading chapter had no heading:** when "What we know" could not be loaded,
  the chapter showed only the failure notice. The new failed-state capture found it (its
  heading font never loaded). The chapter's heading now stays above the notice.

## Accepted limitations and open items

| Item | Owner | Disposition |
|---|---|---|
| H-01 design-review scores for Sprint 1 | Product owner and design reviewer | Not run — requires human. Checklist below |
| H-03 VoiceOver, H-04 Safari | Humans, Sprints 8–9 | Not run — requires human |
| MODEL-07 consent UI for storing a Meta key | T6 (assigned by the controller) | Not in the Task 4 brief; backend done; the error words exist |
| UI-05 calm-mode test; graph reveal | T14 | Implemented, untested |
| UI-06 200 % zoom | T8 onward | Not run |
| UI-09 focused graph views; UI-11 data-dependent states | T8, T14 | No graphs or such data yet |
| DUR-03 partial results with completeness and freshness | first partial run kind | No producer yet |
| `next` 16.4.1 pinned at 13.5 days for a critical security fix | Next dependency change after 2026-10-28T17:43Z | Accepted by the controller, provisional. Removal step: drop `minimumReleaseAgeExclude` once 16.4.1 is 14 days old (ADR 0005 decision 1) |
| `undici` advisories via `jsdom` (dev only) | next `jsdom` bump | Accepted; recheck with `pnpm audit` |
| Gantt aria-label wording (carried from Task 2) | T14 | Unchanged: the Gantt is not built yet |
| After a full restart the Auth emulator re-imports its seed and ends earlier sessions: an open page refreshes its token and carries on, a page loaded before that asks to sign in again (then returns to the same address) | Emulator behaviour (L0 only) | Accepted; documented in the runbook |
| amd64 images | T16 | Not built |

## Human design-review checklist (H-01, Sprint 1, not run)

Use `docs/reviews/sprint-1/screenshots/` (or run `make demo` and open
`http://127.0.0.1:53000`, signing in as Ada), alongside the Sprint 0 references in
`docs/design/screenshots/`. Score 1–5 with concrete defects (plan section 5).

What the screenshots cover, at each of the three sizes:
- **Default:** sign-in and all six chapters on the fixture workspace.
- **Selected:** a field's source in the drawer; route B in the drawer.
- **Empty:** Ben's home with no workspaces; Routes in a new workspace.
- **Stale:** a save refused because another tab saved first.
- **Unavailable:** live updates down (Reconnecting).
- **Failed:** "What we know" unreachable; another person's workspace (not found); an
  uninvited account.

Not in the screenshots, so review them in Storybook (`cd apps/web && pnpm storybook`):
- **States:** Loading, Empty, Unknown, Conditional, Stale, ErrorState and Disabled.
- **Shell:** the strip when refreshing failed or the stream stopped, an unknown budget, and
  long names with three targets; the drawer with an unknown source and a failed load; a
  failed route preview.

Not reviewable yet (no producer): partial results, zero results and the 100-job limit.

Also check:

1. Does the shell feel like the calm observatory at all three sizes? Rail, strip, light
   reading chapters, ink exploration chapters.
2. Is "Fixture preview: not your routes" unmistakable, and is any wording too
   apologetic or too technical?
3. Do the empty chapters explain enough, without nagging?
4. On the phone, is the bottom sheet's peek, More and Less, and drag right? Is the expanded
   height right?
5. Does the You form's field-state control ("Answered", "Unknown", …) read clearly?
6. Layers 2 and 3: is one grey enough (carried from Task 2)?
7. Keyboard: tab through a chapter and open and close the drawer; is focus always visible?

| Category | Score (1–5) | Defects |
|---|---|---|
| Hierarchy | | |
| Typography | | |
| Spacing | | |
| Visual identity | | |
| Chart legibility | | |
| Uncertainty communication | | |
| Responsive composition | | |
| Interaction continuity | | |

Approval: not given. Approver and date: blank until a human reviews.
