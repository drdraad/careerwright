# Carried into Task 6 (from Task 4)
- MODEL-07: the consent UI shown before a user stores a Meta key (spec §16) is not built. Task 6 owns it (ruling in ledger): explicit consent copy, what is stored and where, revoke/rotate affordances using the Task 3 credential API (`CREDENTIAL_REVOKED` 409 handling), keyboard and screen-reader correct.

# Carried into Task 6 (from Task 4 review)
- Remove the `next` 16.4.1 `minimumReleaseAgeExclude` exception from `apps/web/pnpm-workspace.yaml` (it turned 14 days old at 2026-10-28T17:43Z) and update ADR 0005 decision 1, `docs/dependencies.md` and the CLAUDE.md compatibility line; reinstall with `--frozen-lockfile` to prove the lock is unchanged.
- Stale-save alert uses role=alert plus focus; some screen readers may read it twice (H-03 to confirm). If you touch it, keep one mechanism.
- `apps/web/src/lib/queries.ts` keeps a module-global `lastSeen` map for event resume; scope it per workspace/session if the You chapter adds streams.
- H-01 pre-review findings for the UI you extend: phone sheet peek lacks the route name and key figures; no Try again action on a failed load; the stale-save conflict sits below the fold.

# Carried into Task 6 (from Task 5)
- Streaming (spec §4): Task 5 streams the interview reply text to a sealed partial store with IDs-only events and an owner-checked read path. Task 6 renders the streamed reply in the conversation (partial clearly provisional, replaced by the validated turn; failure mid-stream visible), then closes MODEL-03.
- Provisional product decisions from Task 5 (ONS region per city, hard-constraint field set) are listed for the product owner; the UI must not present them as settled facts.
- Reply streaming API (Task 5): `GET .../interview/turns/{id}/reply` returns the partial for the run's owner with a completeness state (`streaming`/`stopped`/`incomplete`/`superseded`, per the generated enum); `run.partial_updated` events carry run ID + seq only and should refresh only that turn's reply query. Map every completeness state in the UI vocabulary; `stopped` is not final; `incomplete` only once the run failed.
- Live eval (R5): the capped live run of representative eval cases uses the test model on synthetic inputs only, through an explicit budget-capped command on the existing usage ledger (per-scope cap 9 calls / 3 production / $0.30). Keep it to at most 6 live cases; no production-model calls (release task owns that).
- The acute-distress / diagnostic-inference response policy is a reviewed policy: record it per R6 as provisional and add it to the human-gate list (not self-certified).
