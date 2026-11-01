# Task 4 re-review 2 (scoped: fix round 2, ccf3d05..885596b)

Read the diff and the changed files. Ran `vitest run queries.test.tsx ProfileEditor.test.tsx`: 15 passed. Viewed `you--stale--390x844.png` (notice visible with the wording; the 1440 and 768 variants were not opened).

## Per ID
| ID | Verdict | Evidence |
|---|---|---|
| A-I2 (a11y) | Fixed | Both stale notices are `role="alert"` via `announce` (`ProfileEditor.tsx:166-172`, `:192-197`). The notice names each changed answer with its new value (`:176-181`). Focus moves once per refusal: the effect depends on `[stale]` (`:63-66`), and `stale` is set only in the 409 path (`:120`) and cleared on save or discard, so a re-render does not refocus. Each conflict line has an id (`:274`), and the select (`:247`) and the value control or list fieldset (`:255,263`; `fields.tsx:73-110`) reference it through `aria-describedby`. The unloaded case has one alert (`RequestFailure announce={false}`, `PageState.tsx`). Tests assert role, text, focus and `toHaveAccessibleDescription` on the amount box and the select (`ProfileEditor.test.tsx` diff 175-250); the e2e asserts focus and text. |
| M1 | Fixed | The register row no longer cites `queries.test.tsx` for resume, live and back-off, and now cites it for the remount resume and the Connecting-at-once tests, which exist. |
| M2 | Fixed | `session.spec.ts` sets a `window` marker and asserts it survives; the URL check is gone. |
| M3 | Fixed | `WorkspaceStrip.tsx:~76` offers Reconnect only for `reauthentication_failed`, with a test for `access_ended`, `closed` and `signed_out`. The implementer found `run()` already emits `connecting`, so the "connecting at once" test is a regression guard. Plausible; I did not re-derive it. |
| M4 | Fixed | `firstLoadFailed` and `refreshFailed` (`queries.ts`) are used by `WorkspaceShell.tsx` and tested directly. |
| M5 | Fixed | `ChapterView.test.tsx` renders `PlannedChapter` with Unknown, Skipped and Prefer-not-to-say budgets; the story wording is changed. |
| M6 | Fixed | The `queries.test.tsx` remount test expects `["2","5"]`. It is real: it stubs `fetch`, receives event 5, unmounts, remounts, and checks `Last-Event-ID`. |
| M7 | Fixed | `profile.ts` treats an edit equal to the newer value as untouched. Covered by a unit test and an editor test (no conflict line, no description). |
| M8 | Fixed | The strip's failed-load span is no longer `role="alert"` (`WorkspaceStrip.tsx`), with a test. |

## Specific checks
- **Focus and double reading.** Focus is not stolen on re-render and there is no trap: `tabIndex=-1` on a non-interactive div, and the global `:focus-visible` ring applies (`globals.css:86`). `role="alert"` plus focus on the same node can be read twice by some screen readers. This is acceptable, not a defect, and the implementer flagged it as unchecked (H-03 stays human-only). The usual pattern is either focus without `role="alert"` (the focused container is read once), or `role="alert"` without moving focus. Optional follow-up: drop `announce` and keep the focus move, or keep the alert and drop the focus move. A decision for H-03.
- **Out-of-list changes.** The `profile.version > base.version` guard (`ProfileEditor.tsx:70`) is sound. After a rebase, `base` is the newer version, so an older query value cannot revert the form; the successful-save path still sets `base`. The `useWorkspaceEvents` options object is wired at the only call site (`WorkspaceShell.tsx:140`, `token: auth.token`). `auth.token` is `useCallback`-memoised (`auth.tsx:133`), so the effect dependency does not restart the stream every render. The `useAuth` import was removed from `queries.ts`. `errorId` is gone from the props; the only remaining use is the local id for `FieldError` (`ProfileEditor.tsx:216,282`). Fully wired.
- **queries.test.tsx.** The heredoc-appended tests are well-formed (the file parses, 15/15 pass with the editor tests) and the tests are real. They mock only `fetch` (a system edge). Biome reformatted the file. The heredoc was a process-rule slip the implementer disclosed.

## New issues
### Critical
None.
### Important
None.
### Minor
1. **Alert plus focus**: see above; decide with H-03 (VoiceOver) and drop one of the two if the double reading is confirmed.
2. **Stale `lastSeen` map is module-global** (`queries.ts`). It is keyed by workspace id and never cleared on sign-out, so the same page resumes from an old seq after another user signs in. Pre-existing and low impact; mention only.
3. **Conflict `aria-describedby` on a non-provided state**: when the person switches a conflicting field to Unknown, the value control is not rendered, but the state select still carries the description. This is correct, with no defect.

## Assessment
**Task quality:** Approved
**Reasoning:** The stale-save refusal and rebased values are announced, focused once, linked to their controls, and covered by role, focus and description assertions. M1-M8 are fixed with real tests, and the out-of-list changes are sound and fully wired.
