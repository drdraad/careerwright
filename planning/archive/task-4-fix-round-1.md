# Task 4 — fix round 1 (FIX_BASE a939024)

Findings: A- = task-4-review-A.md (apps/web/src), B- = task-4-review-B.md (integration,
docs, visual package). Read each finding's full text there. Fix ALL items listed.

## Must-fix
- A-I1  Auth tokens must not sit in localStorage. Use the persistence ADR 0005/MODEL-06
        claim (IndexedDB) or change the claim to match a justified choice; test which store
        holds the tokens.
- A-I2  After a stale 409, rebase the draft: fields the user did not edit take the new
        version's values; edited fields are surfaced as a conflict. Failing test first
        (the scratch repro: second PUT sent the old £1,500 cap over version 2's £900).
- A-I3  A failed refetch in the stale path is visible to the user, never swallowed.
- A-I4  The evidence drawer reads live source state, not a frozen copy; no endless
        "Loading", no false "no source record".
- A-I5  Event stream resumes from the last event id (Last-Event-ID) on reconnect and page
        reopen; replace the assertion-free test with one that fails on the old behaviour.
- A-I6  Unknown / Skipped / Prefer-not-to-say are answers: never shown as "Not answered
        yet", never block a chapter; a budget that only reduces precision does not block
        Options.
- B-I1  Evidence drawer label/value overlap at 1440 and 768 (`.kv` grid); fix, recapture,
        and correct the pre-review claim in sprint-1.md.
- B-I2  End-to-end evidence that a status event crosses the web origin unbuffered: a
        Playwright (or stack) test that triggers a real backend event and observes it in
        the browser through the proxy; "Live" shown only after the stream delivers.
        STATE-07 stays planned until that test exists.
- B-I3  Visual package captures the empty, stale, unavailable and failed states the shell
        already has, at the three viewports; correct sprint-1.md:158 and register row 593.
- A-M3  Route preview claims (conditions, "every route here is…", "every payment funded…")
        derived from the fixture data, not hard-coded; numeric sort for layers.
- A-M4  Clamp the server `retry` value (minimum 1 s).
- A-M5  Workspace-create idempotency key reused across a retry of the same submission.
- A-M6  Workspace list follows next_cursor (or shows truncation honestly); failed list
        load is visible; the strip never says "showing what was last loaded" when nothing
        was loaded.
- A-M7  Accessibility: drop aria-pressed on drawer-opening cards (use aria-haspopup/
        aria-expanded as appropriate); no aria-busy on the status live region; a phone
        surface for the live-update status with a restart action; rail shows visited and
        not-started marks per the design README.
- A-M8  Use the generated request type (no `as unknown as`); economic cost uses SignedMoney
        per CLAUDE.md.

## Cheap fixes
- A-M1 typed ErrorCode set and one typed constant for SSE event names; A-M2 tone/state on
  each ErrorStatement so non-failure codes are not red failures.
- B-M1–B-M10: capture count, stale comment, runbook grouping, journey comment, unused
  helpers, NEXT_TELEMETRY_DISABLED on every host script, ADR 0005 marks the `next` age
  exception provisional with the removal step (16.4.1 turns 14 days old at
  2026-10-28T17:43Z; ruling: exception accepted by the controller), live-mode web probe
  asserts outside/dns, register tag on the pnpm-lock reader test, phone-sheet peek
  deviation listed in the visual findings for H-01.

## Rules
- No live Meta calls. Leave CLAUDE.md's retry-owner sentence untouched (awaiting user).
- Recapture affected screenshots with the existing visual spec; agent pre-review stays
  labelled as agent evidence (R2).
- Re-run `make check` and `make acceptance` once at the end; leave the dev stack stopped.
- Append "Fix round 1" to task-4-report.md: per ID, the change, the covering test, command, output.
