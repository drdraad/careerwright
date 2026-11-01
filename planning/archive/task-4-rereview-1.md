# Task 4 re-review, fix round 1 (a939024..ccf3d05)

Scope: I checked that each item in `task-4-fix-round-1.md` is fixed and looked for regressions in the fix diff. This is not a fresh full review.

Method:
- I read the contract, the fix list, both reviews, the report's "Fix round 1" section, and the 5.5k-line diff in four passes: e2e and build; components; lib, stories and backend; docs and checks JSON.
- I looked at these screenshots:
  - `you--source-drawer` at 1440×900 and 768×1024;
  - `you--stale` at 390×844 and 1440×900;
  - `you--unavailable`, `you--failed` and `routes--empty` at 390×844.
- I summed all three `checks-*.json` files: 16 entries each, none failing.
- I made these focused checks outside the diff, one per named risk:
  - `Alert.tsx`, for whether the stale notice is announced;
  - every web-storage call in `src/`;
  - the `last_event_seq` column, its grants and its RLS (migration r0001, `test_isolation.py`);
  - `routes_events.py`, for whether `retry:` is sent first and how resume works;
  - the query-client refetch triggers (`app/providers.tsx`);
  - the design README's rail marks;
  - the shadow token;
  - CLAUDE.md, compared between a939024 and ccf3d05.
- Constraints kept: no suites run, no Docker, no live calls, the tree untouched.

## Per finding

| ID | Status | Evidence (HEAD) | Covering test; would it fail on the old behaviour? |
|---|---|---|---|
| A-I1 | **Fixed** | `auth.tsx:57` uses `indexedDBLocalPersistence`. The only other web-storage writes are the calm flag in localStorage and the visited marks in sessionStorage (`WorkspaceShell.tsx:42,53,71,80`). With a single persistence, Firebase falls back to memory, never to localStorage | `e2e/session.spec.ts:12` checks: no `firebase:` key in localStorage or sessionStorage, and a `firebase:authUser:` key in IndexedDB. It looks before opening the database, so it creates nothing. A RED on `browserLocalPersistence` is reported. Yes, it would fail |
| A-I2 | **Partially fixed** | The lost update is fixed: `rebaseDraft` (`profile.ts:159-174`) gives untouched fields the newer values, keeps edits and lists clashes, and the editor wires it in (`ProfileEditor.tsx:111-118`). The conflict line is visual only (`:239-246`). **Neither stale notice is announced** (`:159,170`: `tone="stale"`; `Alert.tsx:29-32` sets `role="alert"` only for the error tone). Focus stays on Save, and the editor's own `role="status"` line (`:180`) stays empty. See Important 1 | `ProfileEditor.test.tsx:167` asserts that the second PUT carries the £900 cap and that the field shows "900"; on the old editor it fails (got 150000, as reviewer A's repro showed). `:202` checks the conflict line, and `profile.test.ts` checks `rebaseDraft`. No test checks an announcement |
| A-I3 | **Fixed** | Errors are caught; `fetchQuery` runs with `retry: false`. It sets `{kind: "unloaded"}`, which shows the notice and a `RequestFailure`, and the edits are kept (`ProfileEditor.tsx:100-109,169-179`) | `ProfileEditor.test.tsx:222`. Yes: the old code had an unhandled rejection and showed no notice |
| A-I4 | **Fixed** | `FieldSource.tsx` reads `useProfile` and `useSources` live, refetches once for a missing id, and says "Loading" only until the list settles (`:20-47`). A failed refetch shows "failed", not "none" | `ProfileEditor.test.tsx:272` (loading, then the record) and `:291` (two list calls, never "no source record"). Yes: the old drawer froze both states |
| A-I5 | **Fixed** | Backend: `last_event_seq` is an existing r0001 column that the event append increments under the row lock (`store.py:178`). It is read in the same RLS-scoped SELECT (`api_owner` policy), and `test_isolation.py:27` and `:97` already prove another actor gets no row. Reset keeps the sequence increasing (`cli.py:175`), so a stale `lastSeen` cannot skip events. Web: the stream starts at `lastSeen ?? workspace.last_event_seq` (`queries.ts:185-230`), and a later refetch does not restart it. The boundary has no gap: the workspace is read before the profile, the server resumes with `seq > N`, and "live" refetches everything on each connect. A duplicate only costs a coalesced refetch | `test_events.py::test_a_workspace_reports_its_last_event…` asserts `last_event_seq == last_seq == 2` and resumes with `[3]` (RED: KeyError). The unit test `events.test.ts:113` now awaits the stream and asserts 8 then 9, but on its own it would pass on old `events.ts`, because the option existed. The wiring defect is caught by `e2e/session.spec.ts:46`: on a939024 the field is undefined and no `Last-Event-ID` is sent on first open, so both expects fail. Its assertions do catch the original defect, despite there being no browser RED. Gap (admitted): resuming after a remount within one page is untested |
| A-I6 | **Fixed** | `readiness.ts:40-50` blocks only on start answers that are `unasked`. An Unknown, Skipped or Prefer-not-to-say start answer goes to `withoutStart`, which shows a non-blocking notStarted state (`ChapterView.tsx:119-124`). Refining answers, the budget included, only add "Less precise without …" lines (`:74-79`). Nothing in `src/` renders those states as unanswered or blocking: a grep finds `describeField` → "Unknown", the strip → "Not confirmed", and only one story string (Minor 5) | `readiness.test.ts:22,38,51`. These are pure-function tests and would fail on the old rule (the module did not exist, and the old rule counted every non-provided state). There is no ChapterView render test (Minor 5) |
| A-M1 | Fixed | `events.ts:44` is `ReadonlySet<ErrorCode>`; `STREAM_EVENT` is at `:51-55` | Existing stream tests and `tsc` |
| A-M2 | Fixed | `vocabulary.ts` `ERROR_TONE: Record<ErrorCode, Tone>`; `PageState.tsx` passes `statement.tone` | `PageState.test.tsx` (4 codes) |
| A-M3 | Fixed | `trace.ts` maps readiness to words and treats an unknown state as malformed. `RoutePreview.tsx` derives `sharedCondition`, sorts numerically, and drops "every payment funded…" | `RoutePreview.test.tsx:55,61,69`; `trace.test.ts` |
| A-M4 | Fixed | `events.ts:131` `Math.max(MIN_RETRY_MS, …)` | `events.test.ts:152` (old code slept 0) |
| A-M5 | Fixed | `ChangeKeys` (`api.ts`) is used by create and save; `settled()` runs on success | `queries.test.tsx:35`, `api.test.ts` |
| A-M6 | Fixed | `allPages` follows `next_cursor`. The switcher shows "couldn't be loaded", and the strip shows "What we know couldn't be loaded" (`WorkspaceStrip.tsx:152-157`). `refreshFailed` now requires data (`WorkspaceShell.tsx:135-138`) | `queries.test.tsx:61` and `WorkspaceStrip.test.tsx:50,72`. Shell computation: see Minor 4 |
| A-M7 | Fixed | Route cards use `aria-haspopup="dialog"` and an `aria-expanded` that tracks whether the drawer is open (`RoutePreview.tsx:186`; Radix Dialog gives `role=dialog`). `LoadingState` no longer sets `aria-busy`. Live updates show on every size with Reconnect, as the 390 unavailable capture shows. The rail marks visited and not started, matching `docs/design/README.md:97` | `RoutePreview.test.tsx:79`, `WorkspaceStrip.test.tsx:58`, `ChapterNav.test.tsx` |
| A-M8 | Fixed | `inputFrom` uses typed readers with no cast (`profile.ts`). Economic cost uses a local `SignedMoney` with `formatSignedMoney`, documented as replaced by the generated type at T11. `disabledReason` replaces the story-only `disabled`. The story uses `FieldError`. The shadow is a token that exists (`tokens.css:147`). Only the listed `SESSION_ENDED` codes sign out (`auth.tsx:71,142`) | `money.test.ts`, `trace.test.ts`, `tsc` |
| B-I1 | **Fixed** | `globals.css:489` `max-content minmax(0, 1fr)`. The recaptured drawer at 1440 and 768 has no overprint, and the hash wraps. `sprint-1.md` question 5 is corrected, and the finding is under Visual findings | `visual.spec.ts:190` `overprintedLabels`, made a hard check at `:294`. The reported RED showed `["Source","SHA-256"]`. All 48 entries are clean |
| B-I2 | **Fixed** | "Live" is set on the first body chunk (`events.ts:119-128`), and the API sends `retry:` at once (`routes_events.py:105`). The only refetch triggers are the stream and `visibilitychange` focus (`providers.tsx:13`), and the test changes neither visibility nor focus. So version 2 can appear only through the stream, via the proxy | Unit test `events.test.ts:123` (real RED: the old code said live on headers). E2E `session.spec.ts:62` waits for Live, has another client save, and expects version 2 and the new answer within 5 s. It would pass on a939024, which is expected because the proxy was not buffering. A buffering hop would fail it twice: no Live, and no event within 5 s. Adequate. Nit: Minor 2 |
| B-I3 | **Fixed** | 16 states × 3 viewports, covering empty, stale, unavailable and failed (`visual.spec.ts` shots). The captures I viewed render correctly. `sprint-1.md` known gaps and register UI-11 (row 593) are corrected. The H-01 checklist says what the screenshots cover and which Storybook states to review | The captures with their checks |
| B-M1 | Fixed | 30 → 48, and the error is stated | — |
| B-M2 | Fixed | The `visual.spec.ts` header is corrected | — |
| B-M3 | Fixed | The runbook gives the command its own paragraph and says it needs Docker | — |
| B-M4 | Fixed | The comment is corrected (the vacuous `toBeHidden` is now honestly described) | — |
| B-M5 | Fixed | Both helpers removed | — |
| B-M6 | Fixed | `package.json` scripts set `NEXT_TELEMETRY_DISABLED` and `STORYBOOK_DISABLE_TELEMETRY` | — |
| B-M7 | Fixed | ADR 0005 status line and decision 1 (provisional, with the removal step), `dependencies.md` and the CLAUDE.md compatibility line | — |
| B-M8 | Fixed | `test_local_stack.py:221-222` | runs in `make acceptance` |
| B-M9 | Fixed | `@pytest.mark.req("ARC1-01")` | — |
| B-M10 | Fixed | Listed under Visual findings | — |

Counts: Fixed 26, Partially fixed 1 (A-I2), Not fixed 0.

## Specific checks

- **A-I1:** confirmed above. The visited marks hold `nessa.visited.<workspace UUID>` → a list of chapter ids. They contain no personal data, and they are recorded in ADR 0005 decision 9 and in MODEL-06.
- **A-I2:** the rebase is correct and tested. The conflict is not announced: it is a WCAG 4.1.3 status message with no role, and focus does not move. The implementer's note that it sits below the fold is accurate. The bigger point is that nothing tells an assistive-technology user that the save was refused and that untouched fields now hold other values.
- **A-I5:** confirmed above. The backend change adds one column to an RLS-scoped row. Isolation is already proven by `test_isolation.py`, and the new value is tested by `test_events.py`.
- **A-I6:** confirmed above.
- **B-I2:** confirmed above.
- **Out-of-list additions:** all three are in scope and sound.
  - The chapter heading on a failed or loading chapter (`ChapterView.tsx`) was found by B-I3's capture. It gives the page its h1, and the you-chapter path has no duplicate h1.
  - The sessionStorage visited marks are needed for A-M7. They are documented in the ADR, the register and the review.
  - `e2e/api.ts` and `saveElsewhere` are a refactor that extracts code from `access.spec.ts`, plus a helper used by two specs. The PUT body drops `source_ref_id`, which the input does not take.
- **CLAUDE.md:** only the compatibility boundary changed (3+/2−, the `next` provisional exception). The retry-owner sentence (`CLAUDE.md:38`) is byte-identical between a939024 and ccf3d05.

## New issues in the fix diff

### Critical
None.

### Important
1. **A refused (stale) save is not announced, so the rebase changes fields silently for assistive-technology users.**
   - *Where:* `ProfileEditor.tsx:159,170` (stale-tone `Alert`, no role under `Alert.tsx:29-32`); `:239-246` (the conflict line is neither live nor linked to its control); `:180` (the existing `role="status"` line stays empty).
   - *What:* after Save, the 409 rebase rewrites untouched fields with the newer version's values and shows the notice at the top of the form. A screen-reader user hears nothing. A second Save then commits values that user never heard about.
   - *Why it matters:* this fails WCAG 2.2 SC 4.1.3 (AA), which axe cannot detect. UI-06's T4 part ("announced errors") is marked verified, and A-I2 asked for the conflict to be surfaced.
   - *Fix:*
     - pass `announce` (or `role="status"`) on both stale notices, or put their title in the existing status line;
     - give each conflicting control `aria-describedby` pointing at its conflict line;
     - assert the role in `ProfileEditor.test.tsx:167/202`.

### Minor
1. **Register citation:** the STATE-07 row (`requirements-register.md:410`) cites `src/lib/queries.test.tsx` for resume, live and back-off behaviour. That file tests only create keys and paging. Drop the citation.
2. **Weak no-reload check:** "without a reload" is checked by URL equality (`session.spec.ts:87`), and a reload keeps the URL. Set a `window` marker before the save and assert it survives.
3. **Reconnect where it cannot help, and no feedback after it:**
   - Reconnect is offered for the `access_ended` and `closed` stops (`WorkspaceStrip.tsx:74`). For `access_ended` it cannot help, and for `closed` it flashes during a normal stream restart.
   - After Reconnect, the strip keeps "Updates stopped …" until the first byte arrives, because a newly opened stream emits no `connecting` (`queries.ts:230`, `events.ts` `run`).
   - Fix: limit Reconnect to `reauthentication_failed`, and emit `connecting` when a stream opens.
4. **Untested shell condition:** A-M6's condition in the shell (`WorkspaceShell.tsx:135-138`) has no unit test. `WorkspaceStrip.test.tsx:50` passes `refreshFailed=false`, so its "not 'showing what was last loaded'" assertion does not exercise it; only the `you--failed` capture shows it.
5. **A-I6 coverage and wording:**
   - A-I6 is tested at the pure function only; no render test covers ChapterView with an Unknown, Skipped or Prefer-not-to-say budget.
   - The Storybook alert "Not answered yet" in the unknown tone (`Components.stories.tsx:73`, pre-existing) uses words that conflict with the "Not asked yet" vocabulary. H-01 now points humans at Storybook.
6. **Untested remount resume:** resuming after a remount within one page (module `lastSeen`, `queries.ts:185,226`) is untested. The implementer admits this.
7. **Cosmetic conflict line:** `rebaseDraft` lists a conflict even when the person's edit equals the newer value (`profile.ts:172`), so the line reads "Version N has X here. Saving keeps your answer instead." with the same X.
8. **Two alerts at once:** a failed first profile load raises two alerts together: the strip's "What we know couldn't be loaded" (`WorkspaceStrip.tsx:154`) and the chapter's `RequestFailure`.

Process note (reported by the implementer, outside my review): `sed -i` was used twice for import edits in `6f22212`, against the workspace rule. The resulting edits are correct.

## Assessment
**Task quality:** Needs fixes

**Reasoning:** Every finding is fixed with a test that would fail on the old behaviour, except A-I2's accessibility. The lost update is fixed, but a stale save's refusal and its silent field changes are never announced (WCAG 4.1.3, Important 1). That is a small, local fix. The remaining items are Minor.
