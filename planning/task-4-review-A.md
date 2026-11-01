# Task 4 review, half A (apps/web/src and apps/web/.storybook), eb70b6a..a939024

Method: I read the brief, the carry-forward, the report and then the diff in three passes (lib, then components, then app routes, stories and CSS) against the files at HEAD `a939024` (clean tree). I did not review generated code under `src/generated/**`. I did check how the app uses it. I ran two focused scratch tests from my scratchpad, which wrote nothing in the repository: `/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/215e3a32-af56-4146-900e-11d9bbf0dae9/scratchpad/vt/stale.test.tsx` and `.../vt/resume.test.tsx`. I made no live calls and did not re-run any suite.

### Spec Compliance
- ❌ Issues found:
  - GC7, expected-version writes: the client's stale-save "rebase" defeats the version check for fields the user did not touch (ProfileEditor.tsx:92-100). See I2.
  - GC6, failure is never an empty success:
    - the stale path swallows a failed refetch (ProfileEditor.tsx:93, 124-126);
    - the drawer can freeze a "loading" state or a false "no source record" (ProfileEditor.tsx:104-121). See I3 and I4.
  - Invariant "unknown is never ineligible": the placeholder chapters treat an explicit Unknown, Skipped or Prefer-not-to-say answer as "Needs information first" and "Not answered yet" (ChapterView.tsx:89, 99-108). See I6.
  - Auth persistence: the code writes the session to localStorage (auth.tsx:9, 55). ADR 0005 decision 9 and the MODEL-06 register evidence say IndexedDB. See I1.
  - Carried item, "the UI maps codes to the status vocabulary": partly met. Codes map to words, not to state and tone (PageState.tsx:26-34). See M2.
  - Everything else in the slice exists in this half:
    - chapter rail and menu, workspace strip, evidence drawer with the phone sheet, cards, buttons, form controls and status vocabulary;
    - tokens mirror, mobile CSS, the 7 named-state stories plus shell stories (26 in all);
    - generated-client use, emulator sign-in with seeded identities, the hash-pinned fixture adapter shown only in fixture workspaces, the same-origin proxy, and resumable events with re-authentication.
- ⚠️ Cannot verify from diff (half B or outside this half):
  - e2e journey (sign in, edit, source, fixture route, full restart, reopen);
  - keyboard e2e (every chapter, drawer focus return, phone menu, sheet More/Less heights);
  - visual and axe captures at 1440×900, 390×844 and 768×1024, and the Storybook axe run;
  - "fixture mode makes no external request" (the web egress probe, BND1-11);
  - compose, edge and API Host/Origin allowlist changes; the Dockerfile;
  - backend `operationId` changes;
  - `scripts/generate-client.mjs` drift check; the Makefile `check`/`acceptance` wiring;
  - CLAUDE.md commands;
  - `docs/reviews/sprint-1.md`: agent pre-review labelled as such, human checklist per R2, screenshots;
  - contrast-pairs measurement (68/68), the conversation failure-state fix in docs/design, ADR 0005, register rows, `dependencies.md` (Next 16.4.1 age exception).
  - Note for half B: ADR 0005:118-121 and register MODEL-06 (requirements-register.md:535) contradict the code (I1).
- Named-risk checks (one each):
  1. **Enums from the generated client.**
     - The vocabulary tables are `Record<generated union, …>` (vocabulary.ts:13, 39, 56, 128), and error-code comparisons are typed through `ErrorBody["code"]`.
     - Exceptions: `ACCESS_ENDED` is a `ReadonlySet<string>` (events.ts:43), and the SSE event names are hand-copied (events.ts:117-118). See M1.
  2. **Financial examples.**
     - I grepped components, lib and app for `£` and minor-unit literals. Only the symbol table and the input prefix appear.
     - Figures come from the fixture adapter, and stories import the pack (stories/data.ts:6-7).
     - Money is integer-only (money.ts:15-51, BigInt parse). Unknown money reads as its state (profile.ts:10-13; WorkspaceStrip.tsx:27-40).
  3. **Distinct states.** Loading, empty, unknown, conditional, stale, error and disabled each have a story (States.stories.tsx). Gaps: I3, I4, I6, M6.
  4. **Events.**
     - Last-Event-ID is sent on reconnect within a page (events.ts:82).
     - Re-authentication uses a forced refresh with a 10 s settle rule, then stops (events.ts:186-197).
     - Backoff is capped at 30 s (events.ts:146-151), and the stream stops on unmount (queries.ts:191).
     - Gaps: M4 (no floor on the retry value) and I5 (the stated "reopen does not replay" is not wired, and its test asserts nothing).
  5. **Error envelope.**
     - Every code has words. The raw message is never shown (no `.message` use; ApiError's message is code plus status, api.ts:16).
     - The correlation id is shown in RequestFailure (PageState.tsx:32).
     - The 409 codes are told apart by code, not status (ProfileEditor.tsx:92).
     - Partial: M2.
  6. **Auth.**
     - Sign-in is emulator-only: config refuses a non-loopback emulator or a non-`demo-` project (config.ts:65-82), and `connectAuthEmulator` loads no resolver (auth.tsx:51-56).
     - The query cache is cleared on sign-out (providers.tsx:18-21).
     - No token is logged (one `console.error` in proxy.ts:12, config errors only).
     - Tokens are written to localStorage (I1).
  7. **Optimistic concurrency.** Expected version and idempotency key are sent, and a retry reuses the key (ProfileEditor.tsx:76-85). The conflict display loses updates (I2).
  8. **Accessibility.**
     - Rail and menu links carry `aria-current` (ChapterNav.tsx:37, 70). The drawer moves focus to its title and returns it on close (EvidenceDrawer.tsx:100-107; unit-tested).
     - The phone sheet is a real toggle with `aria-expanded`/`aria-controls` and data-expanded heights (EvidenceDrawer.tsx:125-134; globals.css:712-728).
     - There is one primary action per view in the editor, sign-in and home.
     - Nits: M7.
  9. **Tokens.**
     - The Tailwind theme is reset to semantic tokens only (globals.css:11-67).
     - Sea-glass appears only on the primary button, quiet/icon actions, the current-chapter landmark and selected cards (globals.css:203-209, 333-355, 429-432). No industry colour is used.
     - New text pairings resolve to measured primitives: status-neutral equals text-on-*. The three new pairs are in contrast-pairs.json.
     - One new raw shadow literal (M8).
  10. **Tests.**
      - No `vi.mock` or `spyOn` of the app's own modules. Mocks sit at `fetch` and at injected stream dependencies. Assertions are behavioural.
      - Exceptions: events.test.ts:105-125 asserts nothing (I5), and ProfileEditor.test.tsx:130-163 does not check what the second PUT sends (I2).

### Strengths
- The vocabulary is compile-checked against the generated unions: a new API state or error code fails `tsc` until it has words (vocabulary.ts:1-3, 13-29, 128-233).
- Money is exact. Formatting splits into quotient and remainder, and parsing uses BigInt with stated rejection reasons. Tests include round-trips and large values (money.ts; money.test.ts).
- The fixture adapter matches the live-adapter contract:
  - the hash is pinned;
  - every failure is a typed `failed` result, never an empty preview;
  - route keys are namespaced (`TRACE-01/A`);
  - provenance is carried into the drawer;
  - the preview is shown only in `workspace.fixture` (trace.ts:91-166; load.ts; ChapterView.tsx:160).
- The event stream is carefully bounded. Re-authentication refreshes once and stops when a fresh token fails within 10 s. A transient sign-in outage keeps the refresh pending under backoff. Access-ended codes stop for good. The tests drive all of this through injected fetch, token and sleep (events.ts; events.test.ts).
- The same-origin proxy is narrow:
  - it forwards an allowlist of request headers and Origin verbatim, and no cookies or `x-forwarded-*`;
  - it refuses paths outside `/v1` and dot segments;
  - an unreachable API is a 502 with no envelope;
  - SSE is unbuffered and `Location` is rewritten (apiProxy.ts; apiProxy.test.ts).
- Configuration fails closed, the CSP restricts every resource to self plus the emulator, and the Host allowlist answers DNS rebinding (config.ts; requestPolicy.ts; proxy.ts).
- A disabled Button stays focusable and says why next to it (Button.tsx:18-44). After a first load, a failed refresh keeps the last data visible instead of blanking the shell (WorkspaceShell.tsx:103-137).

### Issues
#### Critical
None.

#### Important
**I1. The auth session (ID token and refresh token) is persisted to localStorage, which contradicts ADR 0005 decision 9, the MODEL-06 evidence and the report.**
- *Where:* `apps/web/src/lib/auth.tsx:9,55`.
- *What:* `initializeAuth(app, { persistence: browserLocalPersistence })` stores the Firebase user under `firebase:authUser:*` in `window.localStorage`, including `stsTokenManager.accessToken`/`refreshToken`. I confirmed this in `node_modules/@firebase/auth/dist/esm/index-LY22yodV.js`: `class BrowserLocalPersistence … super(() => window.localStorage, "LOCAL")` at line 7505, and the user JSON includes `stsTokenManager` with both tokens (lines 1705-1706 and 1865).
- *Why it matters:* the named risk is that tokens never go into localStorage. ADR 0005:118-121 and requirements-register.md:535 record "IndexedDB (its default local persistence)" as by-construction evidence, so the register states something untrue. `browserLocalPersistence` is neither IndexedDB nor the SDK default.
- *Fix:* use `indexedDBLocalPersistence` to match the record, or `inMemoryPersistence`/`browserSessionPersistence` if tokens must not persist at all. If the localStorage choice is deliberate, correct the ADR and the register instead. Add a browser check (e2e) that no `firebase:authUser` key is in localStorage.

**I2. Saving again after a stale refusal silently reverts the other version's changes to fields the user never edited.**
- *Where:* `apps/web/src/components/ProfileEditor.tsx:92-100,152-160`.
- *What:* on 409 the editor calls `setBase(latest)` but keeps the whole old draft. Fields the user did not touch still hold the values from before the conflict. The alert says "Version N changed: X. Check those answers", but field X shows the old value, and the latest value is visible nowhere. "Save" then sends the old X under `expected_version: N`, so the server accepts it.
- *Evidence:* a scratch test (`…/scratchpad/vt/stale.test.tsx`) mirrors ProfileEditor.test.tsx:130-163, with the other version changing the spending cap to £900. After the stale notice, the field still shows "1,500". The second PUT sent `expected_version: 2`, `direct_spend_cap: 150000`, reverting £900 (assertion failed: expected 90000, got 150000).
- *Why it matters:* this is the classic lost update that GC7's expected version exists to prevent, and the UI does not show the conflict honestly.
- *Fix:*
  - On stale, rebuild the draft as `draftFrom(latest)` overlaid only with the fields the user changed against the old base.
  - Where both sides changed a field, keep the local edit and show the latest value beside it.
  - Add an assertion on the second PUT body for an untouched field.

**I3. A failed refetch during the stale path is swallowed: the user sees nothing.**
- *Where:* `apps/web/src/components/ProfileEditor.tsx:93,124-126`.
- *What:* if `queries.fetchQuery(...)` rejects (the API drops between the PUT and the GET), the error escapes `submit()` as an unhandled rejection (`void submit()`, :135). `failure` excludes `STALE_INPUT_VERSION`, and `stale` is never set, so no notice appears. The Save click looks like it did nothing.
- *Why it matters:* this is a swallowed error (GC6).
- *Fix:* wrap the refetch in try/catch and show `RequestFailure` for its error. Alternatively, set a stale state that says the latest version couldn't be loaded.

**I4. Drawer content is a frozen snapshot of query state, so provenance can be shown wrongly.**
- *Where:* `apps/web/src/components/ProfileEditor.tsx:104-121` with `EvidenceDrawer.tsx:39-42,139-141`.
- *What:* `showSource` captures `source`, `loading={sources.isPending}` and `failed={sources.isError}` into a ReactNode stored in drawer state, and nothing updates it afterwards.
  - Opened while sources are pending, it shows "Loading the source record" forever (SourceEvidence.tsx:29).
  - Opened just after a save, while the sources list is being refetched, a new `source_ref_id` is not in the old list. The drawer then states "Unknown: no source record was found for this answer" (SourceEvidence.tsx:35-37) for an answer that has a record, and it stays that way.
- *Why it matters:* a stuck loading state and a false "unknown" about provenance are the distinct-state failures the product forbids.
- *Fix:* store only the field name in the drawer and render a small component inside the drawer that calls `useSources`/`useWorkspaceData` itself, so it updates live. If the id is not found after a successful refetch, refetch once before saying none was found.

**I5. The "reopened page does not replay old events" test asserts nothing, and the behaviour it names is not wired.**
- *Where:* `apps/web/src/lib/events.test.ts:105-125`; `apps/web/src/lib/events.ts:36,61,64,207`; `apps/web/src/lib/queries.ts:180-190`.
- *What:* the test calls `resumed.stop()` synchronously. `run()` checks `stopped` after `await deps.token()`, so `fetch` (which holds the only `expect`) is never called, and the test is synchronous anyway. My scratch test (`…/scratchpad/vt/resume.test.tsx`) passed asserting `fetch` calls === 0.
- *What else:* the app never passes `lastEventId` and never reads `handle.lastEventId()`. Every page open and every new stream therefore starts with no `Last-Event-ID`, and the API replays the workspace's whole event history from 0 (backend routes_events.py:49-51).
- *Why it matters:* the test passes vacuously (contract: tests asserting nothing). The API also carries a speculative extension point with no caller.
- *Fix:* make the test `async`, await the fetch call and assert the header. Then either wire a resume point (for example, start from the current `last_seq` via `GET …/events` or a stored sequence) or delete the option and the handle method.

**I6. Placeholder chapters call an explicit Unknown, Skipped or Prefer-not-to-say answer "Not answered yet" and block on it.**
- *Where:* `apps/web/src/components/ChapterView.tsx:89,99-108`.
- *What:* `missing` is every need whose state is not `"provided"`. Options needs both spending caps and the weekly hours (:47). A person who chose Unknown for their budget therefore sees "Needs information first", then "Not answered yet: total spending limit, monthly payment limit", then "Each can also be marked Unknown". They already did that.
- *Why it matters:* the same app says those answers only reduce precision ("they are shown without a spending check", vocabulary.ts:105, 111). The CLAUDE.md invariant "unknown is never zero or ineligible" is contradicted on a visible state, and it carries through to the coherence question about a shared state vocabulary.
- *Fix:*
  - Count only `unasked` as missing.
  - Reserve `blocked_missing_information` for the needs that genuinely gate (targets, work areas).
  - Word the other states by their actual state, such as "Unknown: results less precise".

#### Minor
**M1. Two pieces of backend vocabulary are hand-copied and not compile-checked.**
- *Where:* `apps/web/src/lib/events.ts:43,117-118`.
- *What:* `ACCESS_ENDED` is a `ReadonlySet<string>` with literal codes, and the SSE event names `reauthenticate` and `stream_ended` are duplicated by hand.
- *Fix:* type the set as `ReadonlySet<ErrorCode>`. Name the event names in one typed constant that points at routes_events.py, or describe them in the OpenAPI document.

**M2. Error codes map to words but not to the status vocabulary.**
- *Where:* `apps/web/src/components/PageState.tsx:26-34`; `apps/web/src/lib/vocabulary.ts:128`.
- *What:* RequestFailure renders every code as a red failure. When runs arrive, SOLVE_LIMIT_REACHED ("routes found so far are kept"), INSUFFICIENT_EVIDENCE and STALE_INPUT_VERSION (outside the editor) will look like failures, not partial, unknown or stale. This is the carried item.
- *Fix:* add a `state`/`tone` to each `ErrorStatement`.

**M3. RoutePreview asserts fixture-specific facts instead of deriving them, and sorts layers as strings.**
- *Where:* `apps/web/src/components/RoutePreview.tsx:32,133-134,210,258`.
- *What:* the condition wording, "every route here is …" and "every payment funded before it falls due" are hard-coded rather than derived from `route.conditional` or the fixture. `layers.sort()` sorts lexicographically.
- *Fix:* derive the claims from the data, as with the carried Gantt aria-label item. Use `.sort((a, b) => a - b)`.

**M4. A server `retry:` value of 0 would reconnect with zero delay.**
- *Where:* `apps/web/src/lib/events.ts:113-115`.
- *What:* the value is used unchecked, so `retry: 0` gives a zero-delay reconnect loop. The backend sends 2000 today.
- *Fix:* clamp it, for example `Math.max(DEFAULT_RETRY_MS, ms)` or at least 1 s.

**M5. A retried "Create workspace" can create a duplicate.**
- *Where:* `apps/web/src/lib/queries.ts:140`.
- *What:* a new idempotency key is made on every submit, so a retry after a lost response creates a second workspace. This contradicts api.ts:52, "a retry of the same change reuses it".
- *Fix:* key on the form contents, as ProfileEditor does.

**M6. Lists are truncated or masked, and the strip misreports a failed first load.**
- *Where:* `apps/web/src/lib/queries.ts:49-57`; `apps/web/src/components/WorkspaceShell.tsx:166`; `apps/web/src/components/WorkspaceStrip.tsx:133-143`.
- *What:*
  - `useWorkspaces` reads one page of 200 and ignores `next_cursor`, so a truncated list shows as complete.
  - A failed workspace list shows only the current workspace in the switcher.
  - When the profile's first load fails, the strip says "Loading" and "Couldn't refresh: showing what was last loaded", though nothing was loaded.

**M7. Accessibility and design nits.**
- *Where:* `RoutePreview.tsx:160`; `LoadingState.tsx:11`; `WorkspaceStrip.tsx:145` with `globals.css:694-696`; `ChapterNav.tsx:36`.
- *What:*
  - `aria-pressed` on route cards that open a drawer rather than toggle.
  - `aria-busy="true"` on a `role="status"` region suppresses its announcement.
  - The live-update status is hidden on phones, so "Updates stopped: sign in again" has no phone surface, and there is no action to restart the stream anywhere.
  - The rail marks only current and decided, not the visited and not-started marks that the design README specifies.

**M8. Type escapes, the economic-cost type and small leftovers.**
- *Where:* `apps/web/src/lib/profile.ts:16,36,97`; `apps/web/src/lib/fixtures/trace.ts:28,129`; `apps/web/src/components/fields.tsx:15`; `apps/web/src/stories/States.stories.tsx:99-101,117-122`; `apps/web/src/app/globals.css:281`; `apps/web/src/lib/auth.tsx:122-127`.
- *What:*
  - `as unknown as ProfileInput` bypasses the generated request type.
  - Economic cost is typed `Money` (≥ 0) and negative values fail as "malformed". CLAUDE.md says to use SignedMoney for economic cost. That is fine for TRACE-01, but it will fail closed on the first negative economic cost; note it until SignedMoney exists.
  - The `disabled` prop on the field controls is used only by a story.
  - The Disabled story shows a natively disabled select with no reason. The Error story copies the FieldError markup.
  - There is a new raw shadow colour.
  - Any non-network token refresh error, such as too-many-requests or an emulator 5xx, signs the user out.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The shell is well structured, the vocabulary is compile-checked, money is exact, and the fixture adapter and event stream are carefully bounded. However, the conflict path loses concurrent updates (I2, verified by execution), the auth tokens sit in localStorage against the recorded decision and the register evidence (I1), and several state paths show failure or unknown wrongly (I3, I4, I6). One event-stream test asserts nothing (I5).
