# Sprint 1 review: a polished local walking skeleton

- Date: 2026-10-28. Branch `l0-local-release`.
- Reviewed revision: `283f45e`, the last Task 4 commit that changes code or tests (after
  review fix round 2). `make check` and `make acceptance` ran on it. The `you--stale`
  captures were taken on it; the other captures are from fix round 1 and render the same
  (compared byte for byte, apart from the per-run reference on the refused pages). The
  commit that updates this review changes only docs.
- Sprint 1 commits: `a31fd42`..`eb70b6a` (Task 3: S1.1–S1.3, the platform),
  `a5d6a7c`..`a939024` (Task 4: S1.4–S1.5, the web shell, and this review),
  `aea2e32`..`ccf3d05` (fix round 1) and `e96ae5f`..`283f45e` plus the docs update (fix
  round 2).
- Implementation reviewer: the Task 4 implementing agent, not independent of the work.
  Screenshot reviewer: Codex, reviewing all 48 committed PNGs and the three recorded check
  reports. This is an **agent pre-review — not the required human review** (R2). The
  implementation checks below are retained historical results, not rerun for this review;
  the screenshots do not establish the behaviour of later revisions.

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
content. Roles, Skills and Options explain their intended content and starting answers;
their features belong to later sprints. Plan describes its intended next step, but its
action and missing-feature explanation need correction (V-06).

**Human design approval: not run, requires a human (H-01).** The screenshots and the agent
pre-review below are evidence for that review, not the review itself (ruling R2).
The screenshot critique is complete: the visual language is coherent, but route readiness,
phone comparison hierarchy and failure recovery need attention before visual acceptance.

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

## Checks run on the final candidate (`283f45e`)

Machine: macOS arm64, Docker 29.1.2 (aarch64), Node 24.11.1 (host) and 24.22.1 (images),
pnpm 10.33.2, uv 0.9.18, Playwright 1.64.0 with Chromium 1248.

| Command | Result |
|---|---|
| `make check` | Backend: ruff format and lint clean, mypy clean (118 files), pytest 210 passed (115 deselected), fixture validator `passed`. Web: generated client matches the backend's OpenAPI document, Biome clean (92 files), `tsc` clean, Vitest 154 passed in 20 files. About 7 s |
| `make acceptance` | pytest `-m "integration or stack"`: 115 passed in 195.0 s (real PostgreSQL 16.15, DBOS, the emulator, the Compose stack incl. the web container). Storybook build succeeded (26 stories). Playwright: 17 passed in 1.3 min on a fresh `nessa-l0-webtest` stack (access 5, journey 1, keyboard 4, session 3, Storybook 1, visual 3). No test project left behind. One line of noise: Node's notice that `NO_COLOR` (set in the host shell) is ignored because Playwright sets `FORCE_COLOR`. In fix round 1, a run on `be3e256` failed only the journey, whose expected drawer wording was out of date; `94c0015` corrected it |
| `playwright test e2e/visual.spec.ts e2e/session.spec.ts e2e/access.spec.ts` with `NESSA_REVIEW_DIR` set to a scratch folder (fix round 2) | 11 passed. All 48 captures pass every check (axe, overflow, label overprint, console, fonts); the `checks-*.json` files are byte-identical to the committed ones. Of the PNGs, only `you--stale` changed (copied in); `not-found` and `not-invited` differ only in their per-run reference (kept) |
| `cd apps/web && pnpm run review-screenshots e2e/session.spec.ts` | Fix round 1 (`94c0015`'s app code): 6 passed, 48 captures (16 states × 3 viewports), every check clean |
| `playwright test e2e/journey.spec.ts --repeat-each=4` | Earlier round (`1f76506`): 4 passed. This was run because an earlier `make acceptance` (on `a08643a`) failed the journey once: the test's live-state check matched "Reconnecting", the page reloaded before re-authenticating after the restart, and the restarted emulator, which re-imports its seed and ends earlier sessions, signed it out. The check is now exact and the journey starts from a reset fixture |
| `cd docs/design && pnpm run contrast` | Earlier round: 68 of 68 pairs pass (three added for the shell). Fix rounds 1 and 2 add no colour pairing |
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
    kept and the newer value is shown beside it. The refusal is announced and takes focus,
    and it names each changed answer with its new value.
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
- **Conditional** readiness is a gate glyph with its condition in the comparison summary
  and drawer, but the route cards say only "Ready in …" (visual finding V-01). **Stale**
  (the stale-save notice) uses sand and a clock; **failed** uses a red edge and a cause.
- **Economic cost** is labelled as such on the fixture preview. Direct spending is a
  separate figure.
- **Synthetic** is a persistent pill in the strip and the phone top bar.

Hazard noted: the fixture preview's layers are the fixture's stated `expected.fronts`, not
a computation. The page and the drawer say so, and nothing in TypeScript ranks routes.

Result: **passed for the shared vocabulary; route-card wording needs correction (V-01)**.

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

**5. Is the interface coherent and polished?** Coherent, but visual acceptance remains
open. All 48 screenshots were inspected against the rubric and the Sprint 0 default You
and Routes references. The rail, surfaces and typography carry through; the phone route
sheet loses the reference's visible key figures, and phone Routes puts every route below
the first viewport. The cards' unqualified readiness and the failed page's recovery/status
wording also need correction. The earlier drawer-label overprint is absent from the
visible facts in these captures. Findings, coverage gaps and follow-up checks are below.
The original keyboard-test results remain historical evidence; static images cannot
verify focus behaviour. Human scores: **not run — requires human (H-01)**.

**6. What exact evidence establishes completion?** The commands and results above, on
`283f45e`. Known gaps:
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

**Empty states explain what the user can do next:** mostly. The home page offers "New
workspace"; Roles, Skills and Options name the answers they use and offer "Review what we
know". Plan says to choose a route but offers the same profile action, without explaining
that plan selection is not available yet (V-06).

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

**Agent pre-review — not the required human review.** All 48 viewport PNGs were opened
and inspected: 16 states at 1440×900, 768×1024 and 390×844. The first package held 30
captures (10 states × 3), not the 33 this review first stated. No numeric design scores
or human approval are assigned.

**Evidence inspected.** Each link is a reviewed image. The three `checks-*.json` reports
contain exactly these files, once each, with matching PNG dimensions: fonts loaded,
zero horizontal page overflow, and empty overprint, axe and unexpected-error lists for
all 48. This checks the committed reports' contents, not a new browser run. The overprint
check covers description-list labels against their values; it does not detect every
clipped control or judge composition.

| State | 1440×900 | 768×1024 | 390×844 |
|---|---|---|---|
| Sign-in | [Desktop](sprint-1/screenshots/sign-in--1440x900.png) | [Tablet](sprint-1/screenshots/sign-in--768x1024.png) | [Phone](sprint-1/screenshots/sign-in--390x844.png) |
| You | [Desktop](sprint-1/screenshots/you--1440x900.png) | [Tablet](sprint-1/screenshots/you--768x1024.png) | [Phone](sprint-1/screenshots/you--390x844.png) |
| You: source selected | [Desktop](sprint-1/screenshots/you--source-drawer--1440x900.png) | [Tablet](sprint-1/screenshots/you--source-drawer--768x1024.png) | [Phone](sprint-1/screenshots/you--source-drawer--390x844.png) |
| Roles | [Desktop](sprint-1/screenshots/roles--1440x900.png) | [Tablet](sprint-1/screenshots/roles--768x1024.png) | [Phone](sprint-1/screenshots/roles--390x844.png) |
| Skills | [Desktop](sprint-1/screenshots/skills--1440x900.png) | [Tablet](sprint-1/screenshots/skills--768x1024.png) | [Phone](sprint-1/screenshots/skills--390x844.png) |
| Options | [Desktop](sprint-1/screenshots/options--1440x900.png) | [Tablet](sprint-1/screenshots/options--768x1024.png) | [Phone](sprint-1/screenshots/options--390x844.png) |
| Routes | [Desktop](sprint-1/screenshots/routes--1440x900.png) | [Tablet](sprint-1/screenshots/routes--768x1024.png) | [Phone](sprint-1/screenshots/routes--390x844.png) |
| Routes: B selected | [Desktop](sprint-1/screenshots/routes--route-b--1440x900.png) | [Tablet](sprint-1/screenshots/routes--route-b--768x1024.png) | [Phone](sprint-1/screenshots/routes--route-b--390x844.png) |
| Plan | [Desktop](sprint-1/screenshots/plan--1440x900.png) | [Tablet](sprint-1/screenshots/plan--768x1024.png) | [Phone](sprint-1/screenshots/plan--390x844.png) |
| Routes: empty workspace | [Desktop](sprint-1/screenshots/routes--empty--1440x900.png) | [Tablet](sprint-1/screenshots/routes--empty--768x1024.png) | [Phone](sprint-1/screenshots/routes--empty--390x844.png) |
| You: stale save | [Desktop](sprint-1/screenshots/you--stale--1440x900.png) | [Tablet](sprint-1/screenshots/you--stale--768x1024.png) | [Phone](sprint-1/screenshots/you--stale--390x844.png) |
| You: updates unavailable | [Desktop](sprint-1/screenshots/you--unavailable--1440x900.png) | [Tablet](sprint-1/screenshots/you--unavailable--768x1024.png) | [Phone](sprint-1/screenshots/you--unavailable--390x844.png) |
| You: first load failed | [Desktop](sprint-1/screenshots/you--failed--1440x900.png) | [Tablet](sprint-1/screenshots/you--failed--768x1024.png) | [Phone](sprint-1/screenshots/you--failed--390x844.png) |
| Home: no workspaces | [Desktop](sprint-1/screenshots/home--empty--1440x900.png) | [Tablet](sprint-1/screenshots/home--empty--768x1024.png) | [Phone](sprint-1/screenshots/home--empty--390x844.png) |
| Workspace not found | [Desktop](sprint-1/screenshots/not-found--1440x900.png) | [Tablet](sprint-1/screenshots/not-found--768x1024.png) | [Phone](sprint-1/screenshots/not-found--390x844.png) |
| Account not invited | [Desktop](sprint-1/screenshots/not-invited--1440x900.png) | [Tablet](sprint-1/screenshots/not-invited--768x1024.png) | [Phone](sprint-1/screenshots/not-invited--390x844.png) |

**What holds up.**

- The rail, raised strip, light reading chapters and ink exploration chapters form one
  recognisable shell. Newsreader headings and Source Sans 3 body copy retain the Sprint 0
  identity; headings, labels and amounts are readable in the inspected views.
- Default and empty chapters explain their state. Skills says nothing has been assessed,
  rather than treating unassessed skills as missing. Options distinguishes unasked study
  hours from the explicit £1,500 limits. Empty Routes says no route has been computed;
  the desktop/tablet unknown budget reads "Not confirmed", not £0.
- Fixture status is prominent in the top bar, the Routes notice and both evidence views.
  Route costs distinguish economic cost from direct spending. Route B's selected edge is
  clear at every width, and its desktop/tablet drawer separates dates, costs and monthly
  amounts without the earlier label collisions.
- The stale notice names the changed answer and newer value, says the local edits are
  kept, and distinguishes unsaved changes from the saved version in the editor heading.
  The unavailable captures retain the visible profile and say "Reconnecting" at all sizes.
- Sign-in and refusal pages reflow without visible text collisions. The phone's longer
  identity buttons wrap; not-found offers both workspaces and sign-out as recovery paths.

**Open findings, ordered by consequence.** V-01–V-06 are usability or clarity corrections;
V-07–V-10 are polish or comprehension risks. Recommendations describe follow-up work;
this review does not change the application.

1. **V-01 — Route cards omit their readiness condition (all sizes).** In
   [selected phone Routes](sprint-1/screenshots/routes--route-b--390x844.png), A/B/C each
   say "Ready in … months"; the qualification is above the list and can scroll away.
   The selected drawer restores it, but an unopened card can read as unconditional. Keep
   "Conditional" beside each card's readiness, with the assessed-report requirement
   available there. Recheck cards with the summary off-screen; do not carry this wording
   into computed routes.
2. **V-02 — Failed-load recovery has no action and ambiguous status (all sizes).**
   [Failed You](sprint-1/screenshots/you--failed--390x844.png) says "try again in a
   moment" but supplies no retry control. The strip simultaneously says "Live" and
   "What we know couldn't be loaded". A live event connection can coexist with a failed
   profile request, but the unqualified label and service-wide error do not explain that.
   Offer an explicit retry and distinguish profile loading from live-update status.
   Check that a retry can recover without requiring the person to navigate away.
3. **V-03 — Phone Routes does not lead with routes.** At 390×844, the
   [default viewport](sprint-1/screenshots/routes--390x844.png) contains the 174 px shell,
   title, fixture notice and comparison context; no route card is visible. The
   [Sprint 0 default](../design/screenshots/route-comparison--default--390x844.png)
   already showed route A before the sheet. Keep the synthetic warning unmistakable,
   shorten the introductory stack and move secondary context behind disclosure so that
   the first route appears in the initial viewport. The same stacking pushes tablet
   route C mostly below its viewport, although A and B remain visible.
4. **V-04 — The phone route-sheet peek omits the decision figures.** In
   [route B's peek](sprint-1/screenshots/routes--route-b--390x844.png), the 212 px sheet
   spends its height on a generic title, "Route B", the synthetic badge and condition;
   its readiness and costs are not visible inside the sheet. The Sprint 0 peek showed
   the route name, condition, 4 months, £600 direct spending and £600 economic cost.
   Put the selected route and compact key figures in the peek, retaining fixture and
   condition labels. Capture both peek and expanded states; More alone does not establish
   that the expanded content fits or scrolls correctly.
5. **V-05 — The phone data-mode explanation is clipped.** On
   [empty home](sprint-1/screenshots/home--empty--390x844.png), the native select cuts off
   "Demo data: synthetic, nothing leaves this computer" at "…leaves thi". Page overflow
   remains zero, so that check misses the lost information. Keep the selected option
   short and place the complete explanation in wrapping helper text. Verify it at 390 px
   and 200 % zoom.
6. **V-06 — Plan's stated next step and action disagree (all sizes).**
   [Empty Plan](sprint-1/screenshots/plan--390x844.png) says a plan starts from a route
   selected in Routes, but its only action is "Review what we know". Unlike the other
   planned chapters, it does not say plan selection is absent from this build. Explain
   that limitation and make the offered action's purpose explicit; do not imply that
   selecting a fixture preview creates a plan. Recheck the empty copy and destination.
7. **V-07 — The profile introduction outweighs the first task.** In
   [phone You](sprint-1/screenshots/you--390x844.png), the first field card starts around
   y=566; even "Add another target role" is cut by the bottom of the viewport. Repeated
   field titles, helper copy and "How you answer …" labels make a sparse form tall.
   At 1440 px, the 760 px form also leaves a broad unused right margin. Shorten the
   introductory explanation and review spacing while retaining explicit field-state
   labels. The deferred conversation explains the missing two-column composition; it
   is not a Sprint 1 feature defect.
8. **V-08 — Reconnecting moves desktop content.** Comparing
   [default You](sprint-1/screenshots/you--1440x900.png) with
   [unavailable You](sprint-1/screenshots/you--unavailable--1440x900.png), the longer status
   wraps the strip from 65 to 117 px and shifts the form down 52 px. Reserve room for the
   longer status or use a stable row arrangement at this width. Verify the transition
   while editing; these stills establish the layout difference, not its animation.
9. **V-09 — Visited chapter dots can resemble completed work.** In
   [desktop Plan](sprint-1/screenshots/plan--1440x900.png), You through Routes have filled
   dots although those chapters include "Not started" content. Current selection is
   clear, but there is no visible explanation that filled means visited. This is a
   comprehension risk, not evidence of a wrong stored state. Distinguish or explain
   visitation before adding completion indicators, and ask the human reviewer what the
   marks communicate.
10. **V-10 — The refused-account page repeats its headline.**
    [Not invited](sprint-1/screenshots/not-invited--390x844.png) uses "This account isn't
    invited" as both page heading and alert title. The repetition adds weight without a
    second piece of information. Retain one clear cause and the sign-out action; use
    supporting copy for the recovery instruction.

**Limits of the image evidence.** These are viewport captures (`fullPage: false`), not
whole-page reviews. In particular:

- Neither drawer has an expanded phone capture. Source-file, hash and observation details
  are visible on desktop/tablet but below the phone peek. The images show More, a handle
  and Close; they do not prove dragging, expansion, scrolling or focus return.
- No stale capture shows the actual conflicting input and its inline newer value. The
  notice is visible, but retained input, field-level association and the save control's
  layout need scrolled captures or a live check. The default phone form also omits most
  fields and Save. Existing automated tests remain separate evidence for behaviour.
- Route D and E cards and the layer 3 glyph are outside these viewports; even the default
  desktop shows only the layer 2 heading at the bottom. The package therefore cannot
  establish layer 2/3 differentiation. There are no application charts, Gantt or scenario
  whiskers yet; chart legibility is not assessable from the fixture cards.
- The no-producer states remain deferred: partial results, zero results and the 100-job
  limit. Long names, three targets, negative economic cost, unknown/skipped/prefer-not-to-say
  selections and the open phone chapter menu are not shown here. Storybook or test claims
  are not substitutes for inspecting those views.
- Static captures do not establish focus visibility across the journey, error
  announcements, calm/reduced-motion behaviour, 200 % zoom, VoiceOver or real Safari.
  No application, browser suite, Storybook or contrast measurement was rerun for this
  screenshot critique.

**Previously corrected defects (Task 4's evidence, not new fixes in this review):**

- **Drawer facts overprinted their values** at 1440×900 and 768×1024: "Source" over the
  persona's source name and "SHA-256" over the hash. The facts list sized its value column
  to the longest value and squeezed the label column to nothing. Labels now take their own
  width and values wrap (`max-content minmax(0, 1fr)`; the hash keeps
  `overflow-wrap: anywhere`). Every capture now also checks that no label's text meets its
  value's text (`overprinted` in `checks-*.json`).
- **A failed or loading chapter had no heading:** when "What we know" could not be loaded,
  the chapter showed only the failure notice. The new failed-state capture found it (its
  heading font never loaded). The chapter's heading now stays above the notice.
- **A refused stale save was silent for screen readers** (found by the fix round 1
  re-review): the notice was not announced, focus stayed on Save, and the conflict lines
  were not tied to their fields. The notice is now an alert that takes focus and names each
  changed answer with its new value. Each conflict line describes its field's controls. A
  failed first load is announced once, by the chapter, not again by the strip.

## Accepted limitations and open items

| Item | Owner | Disposition |
|---|---|---|
| H-01 design-review scores for Sprint 1 | Product owner and design reviewer | Agent screenshot critique complete; scoring and approval not run — requires human. Checklist below |
| V-01–V-10 screenshot findings | Web owner; product/design reviewer for the visitation convention | Open. Prioritise V-01–V-06 and recapture affected views before visual acceptance; V-07–V-10 need polish/comprehension review |
| Screenshot coverage gaps | Web owner | Add expanded phone sheets, scrolled conflict/save views and lower route layers; inspect long names and other supported states before claiming full visual coverage |
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
`docs/design/screenshots/`. The agent's evidence and defects are filled in below;
**scoring and approval are not run — requires human**, under R2 in
[`docs/plan/l0-sprint-tasks.md`](../plan/l0-sprint-tasks.md). Score 1–5 with concrete
defects (plan section 5); every category must reach at least 4 before the final local
release. A pending score is not a pass or an agent-assigned failure.

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

Use the following observations to guide the live human check:

1. **Identity:** the rail, typography and light/ink chapter distinction are consistent.
   Judge whether the tall tablet strip and the desktop status-induced shift (V-08) still
   feel calm while editing.
2. **Fixture clarity:** "Fixture preview: not your routes" is prominent. Check that a
   person still understands the conditional readiness when the notice is off-screen
   (V-01), without needing to open the drawer.
3. **Empty chapters:** Roles, Skills and Options explain missing features and inputs.
   Check Plan's next-step/action mismatch (V-06), and whether filled rail dots imply
   completed chapters (V-09).
4. **Phone sheet:** the captured route peek omits its key figures (V-04). Inspect both
   sheets expanded, More/Less, drag, dismissal and internal scrolling; those states have
   no image evidence here.
5. **Profile controls:** Answered and Not asked yet are readable, but repeated labels
   make the form long (V-07). Inspect Unknown, Skip and Prefer not to say, the scrolled
   stale conflict and Save; confirm the complete data-mode explanation is readable
   (V-05).
6. **Comparison:** check that a route is discoverable promptly on the phone (V-03).
   Scroll to D/E to judge the layer 2/3 shapes and grey, which these captures do not show.
7. **Recovery and keyboard:** test retry after the failed load and distinguish it from
   update-stream status (V-02). Tab through chapters and sheets, checking visible focus,
   announcements and focus return; repeat at 200 % zoom and with reduced motion.

| Category | Human score (1–5) | Evidence and defects to assess |
|---|---|---|
| Hierarchy | Not run — requires human | Chapter titles and state cards are distinct. Phone Routes shows no route card initially (V-03); the sheet's generic title displaces decision figures (V-04) |
| Typography | Not run — requires human | Serif headings, body copy and numeric rows remain readable. Repeated profile labels add weight (V-07); inspect the small wrapped source hash and long-name cases at zoom |
| Spacing | Not run — requires human | Cards use consistent gutters. The phone profile's first card starts around y=566 (V-07); desktop reconnect adds 52 px to the strip (V-08). Wide empty margins alone do not establish a defect |
| Visual identity | Not run — requires human | Rail, raised strip, sea-glass selection and light/ink surfaces match the reference language. Filled visited dots may imply completion (V-09); the refusal headline repeats (V-10) |
| Chart legibility | Not run — requires human | No application charts exist in this package. Route A/B/C figures and B's monthly rows are readable; D/E, layer 3 and charts cannot be judged. Assess charts when implemented |
| Uncertainty communication | Not run — requires human | Synthetic notices, unknown budget and stale/failed states are explicit. Card readiness loses the condition (V-01); failed profile loading still says Live (V-02); the phone mode explanation is clipped (V-05) |
| Responsive composition | Not run — requires human | Chapters reflow without visible page overflow. Phone Routes hierarchy (V-03), sheet figures (V-04), mode clipping (V-05) and form density (V-07) remain open. Expanded sheets and lower content are unreviewed |
| Interaction continuity | Not run — requires human | B's selection and the stale notice are visible. Retry is absent (V-02), Plan's action does not match its next step (V-06), and reconnect moves content (V-08). Keyboard, drag, retained edits and motion need live checks |

Approval: **not given — requires human (H-01)**. Approver and approval date: not recorded.
