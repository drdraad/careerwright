# Task report: two flaky world journeys (2026-11-02)

## What I found

### 1. "Holding the world still…" (world.spec.ts, WLD-05): a product bug, a lost click
The click was not lost by the test: the moving world dropped it.

When the person lets go, the frame loop wakes and the world's liveliness (`live`) grows from 0
by `dt × 1.5` each frame. Right after growing, it snapped any value below 0.002 back to 0
(meant for settling to rest). If the first frame after the wake came less than about 1.3 ms
after it (the wake runs in a React effect; the next animation frame can be due almost at
once, more often under load), the step was tiny, `live` snapped to 0, the frame saw nothing
moving and stopped the loop. Nothing woke it again, so `data-motion` stayed "still" and the
ambient motion never resumed: the person's "let go" was ignored. A frame with a zero step
had the same effect.

Fix (`apps/web/src/components/World.tsx`, frame loop):
- the snap to 0 applies only while settling to rest (`target === 0`), never while waking;
- the loop keeps requesting frames while nothing holds the world (`target > 0`), so even a
  zero step cannot stop it. While unheld, `live > 0` already kept it running, so the loop's
  behaviour at rest, paused or settled is unchanged.

Reproducer (TDD): `src/components/World.test.tsx`, "[WLD-05] moves again when the person lets
go, however soon the next frame comes". Fake clock: hold the world, let the frames stop, let
go about 1 ms before the next frame is due. RED on the old code (`data-motion` stayed
"still"; 1 failed, 13 passed), GREEN after the fix (14 passed).

### 2. "The still world shows the same names…" (world.spec.ts, WLD-03, 768×1024): a test race
The test's `open()` waited only for the chapter heading, then a fixed 900 ms. But the You
chapter shows its heading while it is still "Loading the conversation" (`YouChapter.tsx`):
the panel over the world is a small loading panel then and changes size when the chapter
loads. Where long names fit depends on that panel, so a page read while one view had loaded
and the other had not could show a different set of names. Under full-suite load the
chapter's requests can take longer than 900 ms, which is the failure seen (one long name
missing from the reduced-motion view). The world's target list itself is not partial: the
targets come in one response (`list_targets`), so either none or all three are named.

Fix (test only, `apps/web/e2e/world.spec.ts`, `open()`): after the heading, wait until no
loading state is visible in the chapter (`main .skeleton`, the `LoadingState` placeholder,
visible count 0), and, in this test, until the world names each of the three targets
(attached in the "Your world" list, shown in sight or not). The existing 900 ms travel and
settle wait then starts from a loaded chapter. What is compared is unchanged.

## Changed expectations (disclosed)
- None loosened. Added in the WLD-05 journey: after the second click, the control reads
  `aria-pressed="false"` before `data-motion` is checked (a stronger check).
- `open()` gained an optional `targets` argument; the other caller (the You chapter's "says
  the same" journey) now also waits for the chapter's loading state to clear, which only
  removes the same race there.
- No sleeps or retries added; the existing 900 ms wait is unchanged.

## Files changed
- `apps/web/src/components/World.tsx` (product fix)
- `apps/web/src/components/World.test.tsx` (reproducer)
- `apps/web/e2e/world.spec.ts` (`open()` waits; one added assertion)

## Process note
While finding the reproducer's timing I added temporary `console.log` lines to `World.tsx`
and the test with shell edits, then restored the file from a copy; the final changes were
made with Edit. The final diff holds no debugging code.

## Checks run
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24): passed (ruff,
  mypy 409 files, pytest 2205 passed / 9 skipped, generated client matches, Biome, tsc,
  Vitest 45 files / 473 tests).
- The two journeys five times under the acceptance lock, build shim and machine Chromium
  (log `/tmp/world-harden.log`): 5 of 5 runs "4 passed" (the WLD-05 journey and the WLD-03
  journey at 1440×900, 768×1024 and 390×844), 6.7 to 8.2 minutes each; no failure, no flaky.
- Focused Vitest for the reproducer: RED on the old `World.tsx` (1 failed, 13 passed), GREEN
  on the fix (14 passed).
- `make acceptance`: not run: the controller runs acceptance.

## Concerns
- The race in journey 2 could not be reproduced on demand (it needs load); the fix is from
  the code path. The five runs show no regression, not proof of the absence of the race.
- Other `waitForTimeout(900)` settle waits in world.spec.ts (the "names sit clear" journey)
  have the same heading-only wait; they have not been seen to flake and were left alone.
